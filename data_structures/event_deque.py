"""
event_deque.py — Kayar Pencere Olay Kuyruğu
=============================================
Son N saniyedeki olayları tutan çift-uçlu kuyruk (deque).

Neden deque?
------------
- Baştan silme ve sondan ekleme O(1). Liste kullansaydık baştan silme O(n) olurdu.
- Python'un collections.deque'i C tabanlı; milyonlarca ekleme/çıkarmada bile hızlı.
- Zaman damgalı olaylarda "eski olanları at" mantığı için ideal.

Matematiksel özet:
------------------
n = penceredeki olay sayısı
append(x)            : O(1) amortized
popleft()            : O(1)
prune_expired()      : O(k), k = silinen eleman sayısı
get_rate(type)       : O(n)
get_focus_score()    : O(n)
"""

from collections import deque
from dataclasses import dataclass, field
from time import time
from typing import Optional

from config import EVENT_WINDOW_SECONDS, EVENT_FOCUS_CONTRIBUTION, EventType


@dataclass
class Event:
    """Tek bir olay kaydı. Immutable gibi davranır, timestamp otomatik atanır."""
    type: str
    timestamp: float = field(default_factory=time)
    meta: Optional[dict] = None

    def age(self) -> float:
        """Olayın bu andan kaç saniye önce gerçekleştiği."""
        return time() - self.timestamp


class EventDeque:
    """
    Son `window_seconds` saniyedeki olayların FIFO kuyruğu.
    İçeride collections.deque kullanılır.
    """

    def __init__(self, window_seconds: int = EVENT_WINDOW_SECONDS):
        self._dq: deque[Event] = deque()
        self._window = window_seconds
        # Tür sayaçları - her eklemede/silmede güncellenir, O(1) erişim sağlar
        self._type_counts: dict[str, int] = {}

    # --------------- Temel operasyonlar ---------------
    def push(self, event: Event) -> None:
        """Yeni olayı pencereye ekler, eskileri siler."""
        self._dq.append(event)
        self._type_counts[event.type] = self._type_counts.get(event.type, 0) + 1
        self._prune_expired()

    def _prune_expired(self) -> None:
        """Pencere dışında kalan olayları baştan siler. O(k)."""
        cutoff = time() - self._window
        while self._dq and self._dq[0].timestamp < cutoff:
            old = self._dq.popleft()
            self._type_counts[old.type] -= 1
            if self._type_counts[old.type] == 0:
                del self._type_counts[old.type]

    # --------------- Sorgular ---------------
    def __len__(self) -> int:
        self._prune_expired()
        return len(self._dq)

    def count_of(self, event_type: str) -> int:
        """Belirli türden kaç olay olduğunu O(1) döndürür."""
        self._prune_expired()
        return self._type_counts.get(event_type, 0)

    def rate_per_minute(self, event_type: str) -> float:
        """Pencere içindeki olay oranını dakika başına normalize eder."""
        count = self.count_of(event_type)
        return (count / self._window) * 60.0

    def get_focus_score(self) -> float:
        """
        Returns a focus score between 0 and 100.

        Algorithm (weighted-average approach):
        ---------------------------------------
        Her olay türünün [0, 100] arasında bir "odak katkısı" var:
          - FOCUSED, PRODUCTIVE_APP  → 100 puan (ideal durum)
          - LOOKING_AWAY             →  60 puan (hafif distraksiyon)
          - EYES_CLOSED, FACE_ABSENT →  40 puan (orta distraksiyon)
          - PHONE_DETECTED           →  15 puan (ağır distraksiyon)
          - SOCIAL_MEDIA             →   0 puan (en kötü)
          - UNKNOWN_APP              →  70 puan (nötr, şüpheyle)

        Skor = olayların bu katkılarının basit aritmetik ortalaması.

        Avantajları:
        - Tamamen olay sayısından bağımsız (frame-rate ne olursa olsun stabil)
        - 0-100 aralığını doğal olarak üretir
        - FOCUSED olayları skoru otomatik yukarı çeker
        - Pencere boşsa 100 döner (iyimser varsayım)
        """
        self._prune_expired()
        if not self._dq:
            return 100.0

        total = 0.0
        for event in self._dq:
            total += EVENT_FOCUS_CONTRIBUTION.get(event.type, 50.0)

        avg = total / len(self._dq)
        return round(max(0.0, min(100.0, avg)), 1)

    def snapshot(self) -> list[Event]:
        """Geçerli pencerenin kopyası (dış kullanım için)."""
        self._prune_expired()
        return list(self._dq)


# ============ Hızlı self-test ============
if __name__ == "__main__":
    import time as t
    q = EventDeque(window_seconds=3)
    q.push(Event(EventType.FOCUSED))
    q.push(Event(EventType.PHONE_DETECTED))
    q.push(Event(EventType.SOCIAL_MEDIA))
    print(f"Skor: {q.get_focus_score()}")       # düşük olmalı
    print(f"Telefon: {q.count_of(EventType.PHONE_DETECTED)}")
    t.sleep(3.5)
    q.push(Event(EventType.FOCUSED))             # eskileri budayacak
    print(f"Sonra: {len(q)} olay kaldı")
