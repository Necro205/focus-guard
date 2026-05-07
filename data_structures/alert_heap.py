"""
alert_heap.py — Öncelikli Uyarı Kuyruğu (Min-Heap)
=====================================================
Oluşan dikkat dağınıklığı olaylarını, önem derecesine göre min-heap'te tutar.
En acil uyarı her zaman kökte → feedback modülü pop() ile alır.

Neden heap?
-----------
Çok sayıda olay aynı anda tetiklenebilir (örn: hem telefon görüldü hem
sosyal medya açıldı). Kullanıcıya önce en kritik olanı göstermeliyiz.
- Heap kökü: O(1) erişim
- Ekleme/çıkarma: O(log n)
- Liste sıralasaydık her pop öncesi sort → O(n log n)

Cooldown mantığı:
-----------------
Aynı tür uyarı art arda rahatsız etmesin diye son gösterim zamanı
`_last_shown` hash map'inde tutulur. Pop edildiğinde kontrol edilir.
"""

import heapq
import itertools
from time import time
from typing import Optional

from config import EVENT_PRIORITY, ALERT_COOLDOWN_SECONDS


class AlertHeap:
    """Min-heap öncelikli uyarı kuyruğu."""

    def __init__(self, cooldown_seconds: float = ALERT_COOLDOWN_SECONDS):
        # Heap giriş formatı: (öncelik, sıra_no, tür, meta)
        # sıra_no = aynı öncelikli olaylarda kararlı sıralama (tie-breaker)
        self._heap: list[tuple[int, int, str, Optional[dict]]] = []
        self._counter = itertools.count()  # benzersiz sıra üreteci
        self._last_shown: dict[str, float] = {}
        self._cooldown = cooldown_seconds

    def push_alert(self, event_type: str, meta: Optional[dict] = None) -> None:
        """Olayı önceliklendirerek heap'e ekler. O(log n)."""
        priority = EVENT_PRIORITY.get(event_type, 99)
        heapq.heappush(
            self._heap,
            (priority, next(self._counter), event_type, meta)
        )

    def pop_next_alert(self) -> Optional[tuple[str, Optional[dict]]]:
        """
        En yüksek öncelikli uyarıyı döndürür. Cooldown'daki türleri atlar.
        Döndürürse (event_type, meta), yoksa None. O(log n) × atlanan sayısı.
        """
        while self._heap:
            priority, _, etype, meta = heapq.heappop(self._heap)
            last = self._last_shown.get(etype, 0)
            # Cooldown bitmediyse bu uyarıyı at (zaten gösterildi)
            if time() - last < self._cooldown:
                continue
            self._last_shown[etype] = time()
            return etype, meta
        return None

    def peek_priority(self) -> Optional[int]:
        """En öncelikli olayın puanı (göstermeden). O(1)."""
        return self._heap[0][0] if self._heap else None

    def __len__(self) -> int:
        return len(self._heap)

    def clear(self) -> None:
        self._heap.clear()


# ============ Self-test ============
if __name__ == "__main__":
    from config import EventType
    h = AlertHeap(cooldown_seconds=0)  # cooldown kapalı
    h.push_alert(EventType.LOOKING_AWAY)
    h.push_alert(EventType.SOCIAL_MEDIA)   # en yüksek öncelikli
    h.push_alert(EventType.PHONE_DETECTED)
    while len(h):
        print("Pop:", h.pop_next_alert())
