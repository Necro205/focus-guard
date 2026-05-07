"""
feedback.py — Gerçek Zamanlı Kullanıcı Uyarıları
==================================================
AlertHeap'ten en öncelikli uyarıyı alır ve kullanıcıya gösterir.

Mekanizmalar:
1. Sistem bildirimi (plyer.notification) — platform bağımsız toast
2. Terminal konsol çıktısı (renkli)
3. Opsiyonel bip sesi (platform bağımlı, sessizce fail-safe)
"""

import os
import platform
import sys
from typing import Optional

try:
    from plyer import notification
    _PLYER = True
except Exception:
    _PLYER = False

from config import (
    ENABLE_POPUP_ALERTS, ENABLE_SOUND_ALERTS, EventType,
)


# Kullanıcıya gösterilecek mesajlar (Türkçe)
ALERT_MESSAGES = {
    EventType.LOOKING_AWAY:   ("👀 Ekrandan uzaklaştın",
                               "Başını çevireli bir süre oldu. Geri dön!"),
    EventType.EYES_CLOSED:    ("😴 Uyuklama tespit edildi",
                               "Gözlerin kapalı. Biraz mola vermek ister misin?"),
    EventType.FACE_ABSENT:    ("🚶 Masada değilsin",
                               "Webcam yüzünü göremiyor. Oturum duraklayacak."),
    EventType.PHONE_DETECTED: ("📱 Telefon tespit edildi",
                               "Telefonu bırak, odaklanmaya devam et."),
    EventType.SOCIAL_MEDIA:   ("🚨 Sosyal medyadasın",
                               "Aktif pencere dikkat dağıtıcı görünüyor."),
    EventType.UNKNOWN_APP:    ("❓ Tanımlanmamış uygulama",
                               "Bu pencere verimli listende yok."),
}


class FeedbackManager:
    """Uyarıları platform uygun yöntemlerle gösterir."""

    def __init__(self, app_name: str = "FocusGuard"):
        self.app_name = app_name

    def show(self, event_type: str, meta: Optional[dict] = None) -> None:
        msg = ALERT_MESSAGES.get(event_type)
        if msg is None:
            return
        title, body = msg
        if meta and "detail" in meta:
            body = f"{body}\n({meta['detail']})"

        # 1) Konsol
        self._print_colored(title, body)
        # 2) Sistem bildirimi
        if ENABLE_POPUP_ALERTS and _PLYER:
            try:
                notification.notify(
                    title=title,
                    message=body,
                    app_name=self.app_name,
                    timeout=5,
                )
            except Exception:
                pass
        # 3) Bip
        if ENABLE_SOUND_ALERTS:
            self._beep()

    # -------- internals --------
    @staticmethod
    def _print_colored(title: str, body: str) -> None:
        RED = "\033[91m"; YEL = "\033[93m"; END = "\033[0m"
        print(f"{RED}[UYARI]{END} {YEL}{title}{END} — {body}")

    @staticmethod
    def _beep() -> None:
        try:
            sys_name = platform.system()
            if sys_name == "Windows":
                import winsound
                winsound.Beep(750, 200)
            else:
                # macOS / Linux: ASCII BEL karakteri, terminal destekliyorsa
                sys.stdout.write("\a")
                sys.stdout.flush()
        except Exception:
            pass
