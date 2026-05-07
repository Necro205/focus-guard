"""
demo_without_webcam.py — Webcam olmadan tam pipeline gösterimi
================================================================
Sentetik olay akışı üreterek tüm veri yapılarının gerçek zamanlı
çalıştığını, uyarıların tetiklendiğini ve raporun üretildiğini gösterir.

Sunumda webcam çekmediğinde güvenli fallback — hoca da öyle test edebilir.

Çalıştırma:
    python demo_without_webcam.py
"""

import random
import time
import webbrowser

from config import EventType, REPORT_OPEN_AUTOMATICALLY
from data_structures import (
    EventDeque, Event, SessionHashMap, AlertHeap,
    IntervalTree, Interval,
)
from modules.feedback import FeedbackManager
from analysis.statistics_engine import StatisticsEngine
from analysis.report_generator import ReportGenerator


# Olay üretim olasılıkları (simülasyon için)
SCENARIO = [
    # (event_type, probability) — liste gibi davranan kategoric dağılım
    (EventType.FOCUSED,         0.55),
    (EventType.PRODUCTIVE_APP,  0.20),
    (EventType.LOOKING_AWAY,    0.08),
    (EventType.PHONE_DETECTED,  0.05),
    (EventType.SOCIAL_MEDIA,    0.05),
    (EventType.EYES_CLOSED,     0.03),
    (EventType.FACE_ABSENT,     0.02),
    (EventType.UNKNOWN_APP,     0.02),
]


def sample_event() -> str:
    r = random.random()
    cum = 0
    for etype, p in SCENARIO:
        cum += p
        if r < cum:
            return etype
    return EventType.FOCUSED


def run_demo(duration_seconds: int = 120, events_per_second: float = 3.0):
    print(f"🎬 {duration_seconds} saniyelik sentetik oturum başlıyor...\n")

    # Veri yapıları
    window = EventDeque()
    session_map = SessionHashMap()
    heap = AlertHeap()
    tree = IntervalTree()

    feedback = FeedbackManager()
    distracting = {
        EventType.LOOKING_AWAY, EventType.EYES_CLOSED,
        EventType.FACE_ABSENT, EventType.PHONE_DETECTED,
        EventType.SOCIAL_MEDIA,
    }

    session_map.start_session()
    start = time.time()
    tick = 0

    while time.time() - start < duration_seconds:
        etype = sample_event()
        now = time.time()

        # Veri yapılarına yaz
        window.push(Event(etype))
        score = window.get_focus_score()
        session_map.record_event(etype, score)
        tree.insert(Interval(now, now + 1, etype))
        if etype in distracting:
            heap.push_alert(etype)

        tick += 1
        if tick % 15 == 0:
            # Her 15 olayda bir durumu yazdır
            print(f"  [t={int(now - start):3d}s] Skor: {score:5.1f} | "
                  f"Son 60sn: {len(window)} olay | "
                  f"Heap: {len(heap)} bekleyen")
            # Bekleyen uyarılardan birini göster (gerçek GUI'de feedback yapar)
            alert = heap.pop_next_alert()
            if alert:
                feedback.show(alert[0], alert[1])

        time.sleep(1.0 / events_per_second)

    duration = session_map.session_duration_seconds()
    df = session_map.to_dataframe()
    print(f"\n✅ Oturum bitti: {len(df)} dakika, {df['total_events'].sum()} olay")

    # Analiz + rapor
    engine = StatisticsEngine()
    stats = engine.analyze(df, duration_sec=duration)
    print(f"\n📊 İSTATİSTİK ÖZETİ")
    print(f"   Ortalama odak:     {stats.avg_focus_score}")
    print(f"   Medyan odak:       {stats.median_focus_score}")
    print(f"   Std. sapma:        {stats.std_focus_score}")
    print(f"   IQR:               {stats.iqr_focus_score}")
    print(f"   Trend eğimi:       {stats.focus_trend_slope}")
    print(f"   Verimlilik:        {stats.productivity_score}")
    print(f"   Shapiro-Wilk p:    {stats.normality_p_value} "
          f"({'normal' if stats.is_focus_normal else 'normal değil'})")
    print(f"\n💡 ÖNERİLER:")
    for r in stats.recommendations:
        print(f"   • {r}")

    generator = ReportGenerator()
    path = generator.generate(stats, df)
    print(f"\n📄 HTML rapor: {path.resolve()}")

    if REPORT_OPEN_AUTOMATICALLY:
        try:
            webbrowser.open(f"file://{path.resolve()}")
        except Exception:
            pass


if __name__ == "__main__":
    # Hoca kısa süreli gösterim isterse: duration_seconds=30 yap
    run_demo(duration_seconds=60, events_per_second=5.0)
