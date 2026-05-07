"""
session_hashmap.py — Dakika Bazlı İstatistik Hash Haritası
=============================================================
Oturum boyunca her dakikanın istatistiklerini O(1) erişimle saklar.

Neden hash map?
---------------
Dakika tam sayı (epoch // 60) olarak anahtarlanır; dict'in hash lookup'ı O(1).
Son dakikanın istatistiğini anlık güncellemek her olayda bu kadar hızlı olmalı.

İç yapı:
--------
{
    minute_bucket: {
        "focus_seconds": int,
        "distraction_seconds": int,
        "event_counts": { "phone_detected": 4, ... },
        "avg_focus_score": float,
    },
    ...
}

Karmaşıklıklar:
---------------
record_event()       : O(1)
get_minute(m)        : O(1)
get_all_minutes()    : O(m), m = dakika sayısı (rapor için)
to_dataframe()       : O(m)
"""

from time import time
from typing import Optional
import pandas as pd

from config import EventType


def _minute_bucket(timestamp: float) -> int:
    """Epoch saniyesini dakikaya yuvarlar (hash key)."""
    return int(timestamp // 60)


class SessionHashMap:
    """Oturum süresince dakika bazlı istatistik hash map'i."""

    def __init__(self):
        self._buckets: dict[int, dict] = {}
        self._session_start: Optional[float] = None

    # ---- Yaşam döngüsü ----
    def start_session(self) -> None:
        self._session_start = time()
        self._buckets.clear()

    # ---- Yazma operasyonları ----
    def record_event(self, event_type: str, focus_score: float) -> None:
        """
        Bir olayı o dakikanın bucket'ına ekler. Bucket yoksa tembel oluşturur.
        Amortized O(1).
        """
        bucket_key = _minute_bucket(time())
        bucket = self._buckets.get(bucket_key)
        if bucket is None:
            bucket = {
                "event_counts": {},
                "focus_score_sum": 0.0,
                "focus_score_n": 0,
                "timestamp_start": time(),
            }
            self._buckets[bucket_key] = bucket

        # Olay sayısını artır
        bucket["event_counts"][event_type] = \
            bucket["event_counts"].get(event_type, 0) + 1

        # Ortalama odak skoru için toplam ve sayaç (tek geçişte hesaplanır)
        bucket["focus_score_sum"] += focus_score
        bucket["focus_score_n"] += 1

    # ---- Okuma operasyonları ----
    def get_minute(self, bucket_key: int) -> Optional[dict]:
        """Belirli bir dakikanın istatistiği. O(1)."""
        return self._buckets.get(bucket_key)

    def get_current_minute(self) -> Optional[dict]:
        """Şu anki dakikanın istatistiği."""
        return self.get_minute(_minute_bucket(time()))

    def total_events(self, event_type: str) -> int:
        """Oturum boyunca toplam X tipi olay sayısı. O(m)."""
        return sum(
            b["event_counts"].get(event_type, 0)
            for b in self._buckets.values()
        )

    def average_focus_score(self) -> float:
        """Tüm oturumun ortalama odak skoru."""
        total_sum = sum(b["focus_score_sum"] for b in self._buckets.values())
        total_n = sum(b["focus_score_n"] for b in self._buckets.values())
        return round(total_sum / total_n, 2) if total_n else 0.0

    def session_duration_seconds(self) -> float:
        if self._session_start is None:
            return 0.0
        return time() - self._session_start

    def to_dataframe(self) -> pd.DataFrame:
        """
        Bütün dakika bucketlarını pandas DataFrame'e çevirir.
        Zaman serisi analizi için hazır format.
        """
        rows = []
        for minute_key in sorted(self._buckets.keys()):
            b = self._buckets[minute_key]
            avg_score = (b["focus_score_sum"] / b["focus_score_n"]
                         if b["focus_score_n"] else 0)
            row = {
                "minute": minute_key,
                "timestamp": b["timestamp_start"],
                "avg_focus_score": avg_score,
                "total_events": sum(b["event_counts"].values()),
            }
            # Her olay türü için ayrı kolon
            for etype in [EventType.FOCUSED, EventType.LOOKING_AWAY,
                          EventType.EYES_CLOSED, EventType.FACE_ABSENT,
                          EventType.PHONE_DETECTED, EventType.SOCIAL_MEDIA,
                          EventType.PRODUCTIVE_APP, EventType.UNKNOWN_APP]:
                row[etype] = b["event_counts"].get(etype, 0)
            rows.append(row)
        return pd.DataFrame(rows)


# ============ Hızlı self-test ============
if __name__ == "__main__":
    sm = SessionHashMap()
    sm.start_session()
    sm.record_event(EventType.FOCUSED, 95.0)
    sm.record_event(EventType.PHONE_DETECTED, 72.0)
    sm.record_event(EventType.SOCIAL_MEDIA, 58.0)
    print("Toplam telefon olayı:", sm.total_events(EventType.PHONE_DETECTED))
    print("Ortalama odak:", sm.average_focus_score())
    print(sm.to_dataframe())
