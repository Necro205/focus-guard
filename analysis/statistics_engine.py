"""
statistics_engine.py — Oturum Sonu İstatistiksel Analiz
=========================================================
Oturum bittiğinde SessionHashMap verilerinden detaylı istatistik çıkarır.

İçerdiği analizler:
1. Tanımlayıcı istatistikler (ortalama, medyan, std, IQR)
2. Odak skoru zaman serisi + hareketli ortalama
3. Dikkat dağınıklığı türleri arasında korelasyon (Pearson)
4. Pomodoro verimlilik skoru
5. Shapiro-Wilk normallik testi (odak skoru dağılımı normal mi?)
6. İki farklı oturum bölgesinin karşılaştırması (opsiyonel Welch t-testi)
"""

from dataclasses import dataclass, asdict
from typing import Optional

import numpy as np
import pandas as pd
from scipy import stats

from config import EventType


@dataclass
class SessionStatistics:
    # Genel
    duration_minutes: float
    total_events: int
    avg_focus_score: float
    median_focus_score: float
    std_focus_score: float
    min_focus_score: float
    max_focus_score: float
    iqr_focus_score: float

    # Olay türüne göre dağılım
    event_breakdown: dict[str, int]
    event_percentages: dict[str, float]

    # Zaman serisi (dakika başına)
    focus_trend_slope: float        # lineer regresyon eğimi
    rolling_avg_5min: list[float]   # 5 dakikalık hareketli ortalama

    # Korelasyon
    correlation_matrix: dict       # dikkat türleri arası Pearson r

    # Test sonuçları
    normality_p_value: float       # Shapiro-Wilk p-değeri
    is_focus_normal: bool

    # Verimlilik skoru (0-100)
    productivity_score: float

    # Tavsiyeler
    recommendations: list[str]

    def to_dict(self) -> dict:
        return asdict(self)


class StatisticsEngine:
    """SessionHashMap → SessionStatistics dönüşümü."""

    DISTRACTION_COLS = [
        EventType.LOOKING_AWAY,
        EventType.EYES_CLOSED,
        EventType.FACE_ABSENT,
        EventType.PHONE_DETECTED,
        EventType.SOCIAL_MEDIA,
    ]

    def analyze(self, df: pd.DataFrame, duration_sec: float) -> SessionStatistics:
        if df.empty:
            return self._empty_stats(duration_sec)

        scores = df["avg_focus_score"].values

        # --- Tanımlayıcı istatistikler ---
        q1, q3 = np.percentile(scores, [25, 75])
        desc = {
            "avg":    float(np.mean(scores)),
            "median": float(np.median(scores)),
            "std":    float(np.std(scores, ddof=1)) if len(scores) > 1 else 0.0,
            "min":    float(np.min(scores)),
            "max":    float(np.max(scores)),
            "iqr":    float(q3 - q1),
        }

        # --- Olay dağılımı ---
        all_event_cols = [c for c in df.columns
                          if c in [EventType.FOCUSED] + self.DISTRACTION_COLS
                          + [EventType.PRODUCTIVE_APP, EventType.UNKNOWN_APP]]
        breakdown = {col: int(df[col].sum()) for col in all_event_cols}
        total_events = sum(breakdown.values())
        percentages = {
            k: round(100.0 * v / total_events, 2) if total_events else 0.0
            for k, v in breakdown.items()
        }

        # --- Zaman serisi: trend eğimi (en küçük kareler) ---
        if len(scores) >= 2:
            x = np.arange(len(scores))
            slope, _intercept, _r, _p, _se = stats.linregress(x, scores)
        else:
            slope = 0.0

        # --- Hareketli ortalama ---
        rolling = pd.Series(scores).rolling(window=5, min_periods=1).mean().tolist()

        # --- Korelasyon matrisi ---
        corr = {}
        distraction_df = df[self.DISTRACTION_COLS].copy()
        # Sadece en az 2 sıfırdan farklı değeri olan kolonları tut (korelasyon için)
        valid_cols = [c for c in self.DISTRACTION_COLS
                      if distraction_df[c].nunique() > 1]
        if len(valid_cols) >= 2:
            corr_df = distraction_df[valid_cols].corr(method="pearson")
            corr = corr_df.round(3).to_dict()

        # --- Normallik testi (Shapiro-Wilk, n<5000 için uygun) ---
        if 3 <= len(scores) <= 5000:
            _w, p_val = stats.shapiro(scores)
        else:
            p_val = float("nan")
        is_normal = p_val > 0.05 if not np.isnan(p_val) else False

        # --- Verimlilik skoru ---
        productivity = self._compute_productivity(df, breakdown, total_events)

        # --- Tavsiyeler ---
        recs = self._generate_recommendations(desc, percentages, slope)

        return SessionStatistics(
            duration_minutes=round(duration_sec / 60.0, 2),
            total_events=total_events,
            avg_focus_score=round(desc["avg"], 2),
            median_focus_score=round(desc["median"], 2),
            std_focus_score=round(desc["std"], 2),
            min_focus_score=round(desc["min"], 2),
            max_focus_score=round(desc["max"], 2),
            iqr_focus_score=round(desc["iqr"], 2),
            event_breakdown=breakdown,
            event_percentages=percentages,
            focus_trend_slope=round(float(slope), 4),
            rolling_avg_5min=[round(v, 2) for v in rolling],
            correlation_matrix=corr,
            normality_p_value=round(float(p_val), 4) if not np.isnan(p_val) else None,
            is_focus_normal=is_normal,
            productivity_score=round(productivity, 1),
            recommendations=recs,
        )

    # ---------------- yardımcılar ----------------
    def _compute_productivity(
        self, df: pd.DataFrame, breakdown: dict, total: int
    ) -> float:
        """
        Verimlilik = ağırlıklı toplam / maksimum.
        Odaklanma ve verimli uygulama puan kazandırır,
        her distraksiyon belli ceza verir.
        """
        if total == 0:
            return 0.0
        weights = {
            EventType.FOCUSED:        +1.0,
            EventType.PRODUCTIVE_APP: +0.8,
            EventType.LOOKING_AWAY:   -0.4,
            EventType.EYES_CLOSED:    -0.5,
            EventType.FACE_ABSENT:    -0.7,
            EventType.PHONE_DETECTED: -1.0,
            EventType.SOCIAL_MEDIA:   -1.2,
            EventType.UNKNOWN_APP:    -0.2,
        }
        score = sum(weights.get(k, 0) * v for k, v in breakdown.items())
        max_possible = total * 1.0  # hepsi FOCUSED olsaydı
        min_possible = total * -1.2
        # 0-100 aralığına normalize
        normalized = (score - min_possible) / (max_possible - min_possible)
        return max(0.0, min(100.0, normalized * 100))

    def _generate_recommendations(
        self, desc: dict, pct: dict, slope: float
    ) -> list[str]:
        recs = []
        if desc["avg"] < 60:
            recs.append(
                "Ortalama odak skorun düşük. 25 dakika Pomodoro + 5 dakika mola dene."
            )
        if pct.get(EventType.PHONE_DETECTED, 0) > 15:
            recs.append(
                "Oturumun %15'inden fazlasında telefon görüldü. "
                "Telefonu başka odaya koymayı düşün."
            )
        if pct.get(EventType.SOCIAL_MEDIA, 0) > 10:
            recs.append(
                "Sosyal medya kullanımın yüksek. Cold Turkey veya Freedom gibi "
                "site engelleyici kullanmayı düşün."
            )
        if pct.get(EventType.EYES_CLOSED, 0) > 8:
            recs.append(
                "Uyuklama belirtileri gözlemlendi. Uyku düzenini gözden geçir."
            )
        if slope < -0.5:
            recs.append(
                "Odaklanma seviyen zamanla düştü. "
                "Oturum başına daha kısa süreler planla."
            )
        elif slope > 0.5:
            recs.append(
                "Odaklanma seviyen zamanla arttı — ısınma etkisi. "
                "Isınma rutini oluşturabilirsin."
            )
        if desc["std"] > 20:
            recs.append(
                "Odak skorunun varyansı yüksek — tutarsız çalışıyorsun. "
                "Düzenli aralıklarla kısa molalar verebilirsin."
            )
        if not recs:
            recs.append("Harika bir oturum! Dengeli ve sürdürülebilir görünüyor.")
        return recs

    def _empty_stats(self, duration_sec: float) -> SessionStatistics:
        return SessionStatistics(
            duration_minutes=round(duration_sec / 60.0, 2),
            total_events=0,
            avg_focus_score=0, median_focus_score=0, std_focus_score=0,
            min_focus_score=0, max_focus_score=0, iqr_focus_score=0,
            event_breakdown={}, event_percentages={},
            focus_trend_slope=0.0, rolling_avg_5min=[],
            correlation_matrix={}, normality_p_value=None, is_focus_normal=False,
            productivity_score=0.0,
            recommendations=["Oturum çok kısa; analiz için yeterli veri yok."],
        )
