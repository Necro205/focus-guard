"""
activity_monitor.py — Aktif Pencere / Uygulama İzleme
=======================================================
Aktif pencerenin başlığına bakar; config'deki anahtar kelimelerle eşleşir.

Platform notu:
--------------
- Windows/Mac: pygetwindow kolayca çalışır
- Linux/Wayland: pygetwindow çalışmayabilir → fallback olarak None döner
  (projede çalışmaması kullanıcının işlevselliğini tamamen bozmaz)
"""

import time
from dataclasses import dataclass
from typing import Optional

try:
    import pygetwindow as gw
    _PGW_AVAILABLE = True
except Exception:
    _PGW_AVAILABLE = False

from config import (
    DISTRACTION_KEYWORDS, PRODUCTIVE_KEYWORDS,
    WINDOW_CHECK_INTERVAL, EventType,
)


@dataclass
class WindowInfo:
    title: str
    classification: str  # EventType.SOCIAL_MEDIA / PRODUCTIVE_APP / UNKNOWN_APP


class ActivityMonitor:
    def __init__(self):
        self._last_check = 0.0
        self._last_info: Optional[WindowInfo] = None

    def should_check(self) -> bool:
        return time.time() - self._last_check >= WINDOW_CHECK_INTERVAL

    def get_active_window_info(self) -> Optional[WindowInfo]:
        """Aktif pencerenin başlığını alır ve sınıflandırır."""
        if not self.should_check():
            return self._last_info
        self._last_check = time.time()

        title = self._fetch_active_title()
        if not title:
            return None

        title_low = title.lower()
        # Önce sosyal medya mı?
        for kw in DISTRACTION_KEYWORDS:
            if kw in title_low:
                self._last_info = WindowInfo(title, EventType.SOCIAL_MEDIA)
                return self._last_info
        # Sonra verimli mi?
        for kw in PRODUCTIVE_KEYWORDS:
            if kw in title_low:
                self._last_info = WindowInfo(title, EventType.PRODUCTIVE_APP)
                return self._last_info
        self._last_info = WindowInfo(title, EventType.UNKNOWN_APP)
        return self._last_info

    def _fetch_active_title(self) -> Optional[str]:
        if not _PGW_AVAILABLE:
            return None
        try:
            w = gw.getActiveWindow()
            if w is None:
                return None
            return w.title or None
        except Exception:
            # Bazı platformlarda erişim reddedilebilir
            return None
