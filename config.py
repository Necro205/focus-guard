"""
config.py — FocusGuard Yapılandırma Sabitleri
Tüm ayarlar buradan yönetilir; böylece modüller arası bağımlılık minimumda kalır.
"""

# ============ KAMERA ============
# CAMERA_INDEX = None ise tüm indeksler otomatik denenir (önerilen)
# Belirli bir kameraya bağlanmak için sayı ver: 0, 1, 2 ...
CAMERA_INDEX = 1
CAMERA_MAX_INDEX_TO_TRY = 4   # Auto-search modunda 0..3 arasını dener
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
PROCESS_EVERY_N_FRAMES = 3
import platform as _platform
CAMERA_BACKEND = "dshow" if _platform.system() == "Windows" else None

# ============ YÜZ / ODAK TESPİTİ ============
# Kafanın ekrana yönlenmiş sayılması için maksimum dönme açıları (derece)
MAX_YAW_DEGREES = 25           # Sağa/sola
MAX_PITCH_DEGREES = 20         # Aşağı/yukarı
EYE_AR_THRESHOLD = 0.21        # Eye Aspect Ratio (EAR) - göz kapalı eşiği
EYE_AR_CONSEC_FRAMES = 15      # Bu kadar ardışık kare boyunca kapalıysa "uyukluyor"
FACE_ABSENT_SECONDS = 3        # Bu kadar yüz görünmezse "masadan kalktı"

# ============ TELEFON TESPİTİ ============
PHONE_DETECTION_INTERVAL = 2.0 # Saniyede bir kez kontrol (YOLO pahalı)
PHONE_CONFIDENCE_THRESHOLD = 0.45
YOLO_MODEL = "yolov8n.pt"      # nano model (hızlı). yolov8s.pt daha doğru.
PHONE_CLASS_ID = 67            # COCO datasetinde "cell phone" sınıfı

# ============ AKTİF PENCERE İZLEME ============
WINDOW_CHECK_INTERVAL = 1.5    # Saniyede bir pencere başlığı kontrolü
DISTRACTION_KEYWORDS = [
    "instagram", "tiktok", "facebook", "twitter", "x.com",
    "youtube", "netflix", "reddit", "twitch",
    "whatsapp", "telegram", "discord",
    "9gag", "pinterest", "snapchat",
]
PRODUCTIVE_KEYWORDS = [
    "code", "pycharm", "vscode", "visual studio",
    "overleaf", "notion", "obsidian", "anki",
    "pdf", "word", "libreoffice", "docs.google",
    "stackoverflow", "github", "gitlab",
    "jupyter", "colab",
    "focusguard",   # kendi uygulamamız da verimli sayılsın
]

# ============ VERİ YAPILARI ============
EVENT_WINDOW_SECONDS = 60      # Deque kayar pencere boyutu (saniye)
ALERT_COOLDOWN_SECONDS = 20    # Aynı tür uyarı arası minimum süre

# ============ UYARI / GERİ BİLDİRİM ============
ENABLE_SOUND_ALERTS = True
ENABLE_POPUP_ALERTS = True
FOCUS_SCORE_WARN_THRESHOLD = 50  # Bu skorun altına düşünce uyar

# ============ RAPORLAMA ============
REPORT_DIR = "reports"
REPORT_OPEN_AUTOMATICALLY = True

# ============ OLAY TÜRLERİ (enum yerine string sabitler) ============
class EventType:
    FOCUSED = "focused"
    LOOKING_AWAY = "looking_away"
    EYES_CLOSED = "eyes_closed"
    FACE_ABSENT = "face_absent"
    PHONE_DETECTED = "phone_detected"
    SOCIAL_MEDIA = "social_media"
    PRODUCTIVE_APP = "productive_app"
    UNKNOWN_APP = "unknown_app"

# Her olay türünün odak skoruna katkısı (0-100).
# Yüksek değer = daha odaklı. Skor bu değerlerin pencere içi ortalamasıdır.
EVENT_FOCUS_CONTRIBUTION = {
    EventType.FOCUSED:         100.0,    # ideal: ekrana bakıyor, gözler açık
    EventType.PRODUCTIVE_APP:  100.0,    # verimli uygulama aktif
    EventType.LOOKING_AWAY:     55.0,    # kısa bakış kaybı: hafif distraksiyon
    EventType.EYES_CLOSED:      40.0,    # göz kapalı: uyuklama belirtisi
    EventType.FACE_ABSENT:      30.0,    # masada yok: ciddi kesinti
    EventType.PHONE_DETECTED:   15.0,    # telefon görünür: ağır distraksiyon
    EventType.SOCIAL_MEDIA:      0.0,    # sosyal medya: en kötü durum
    EventType.UNKNOWN_APP:      70.0,    # bilinmeyen: nötr-iyimser (orta)
}

# Legacy ceza puanı (bazı modüllerde hâlâ referans alınıyor olabilir)
EVENT_PENALTIES = {
    EventType.FOCUSED: 0,
    EventType.LOOKING_AWAY: 2,
    EventType.EYES_CLOSED: 3,
    EventType.FACE_ABSENT: 5,
    EventType.PHONE_DETECTED: 8,
    EventType.SOCIAL_MEDIA: 10,
    EventType.PRODUCTIVE_APP: 0,
    EventType.UNKNOWN_APP: 1,
}

# Uyarı önceliği (düşük sayı = yüksek öncelik, min-heap için)
EVENT_PRIORITY = {
    EventType.SOCIAL_MEDIA: 1,
    EventType.PHONE_DETECTED: 2,
    EventType.FACE_ABSENT: 3,
    EventType.EYES_CLOSED: 4,
    EventType.LOOKING_AWAY: 5,
    EventType.UNKNOWN_APP: 6,
}
