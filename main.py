"""
main.py — FocusGuard Ana Uygulaması
=====================================
Modern, two-screen tasarım:
  1. Welcome screen — karşılama + başlatma
  2. Session screen — canlı izleme + metrikler
"""

import threading
import time
import tkinter as tk
import webbrowser
from tkinter import messagebox

import cv2
from PIL import Image, ImageTk, ImageDraw, ImageFont

from config import (
    CAMERA_INDEX, FRAME_WIDTH, FRAME_HEIGHT, CAMERA_BACKEND,
    PROCESS_EVERY_N_FRAMES, REPORT_OPEN_AUTOMATICALLY, EventType,
)
from data_structures import (
    EventDeque, Event, SessionHashMap, AlertHeap,
    IntervalTree, Interval,
)
from modules.face_detector import FaceDetector
from modules.phone_detector import PhoneDetector
from modules.activity_monitor import ActivityMonitor
from modules.feedback import FeedbackManager

from analysis.statistics_engine import StatisticsEngine
from analysis.report_generator import ReportGenerator


# ============ Design tokens ============
BG          = "#0A0E13"
SURFACE     = "#131A22"
SURFACE_2   = "#1A2330"
SURFACE_3   = "#222E3E"
BORDER      = "#1F2A38"
BORDER_SOFT = "#2A3645"
TEXT        = "#E6EDF3"
TEXT_MUTED  = "#8B98A5"
TEXT_DIM    = "#5D6975"
ACCENT      = "#E8B923"
ACCENT_HOV  = "#F5CE4A"
ACCENT_DIM  = "#8A6D16"
OK          = "#3FB950"
WARN        = "#D29922"
BAD         = "#F85149"

# Gösterim meta
EVENT_PRETTY = {
    EventType.FOCUSED:        ("Focused",        OK),
    EventType.PRODUCTIVE_APP: ("Productive",     OK),
    EventType.LOOKING_AWAY:   ("Looking away",   WARN),
    EventType.EYES_CLOSED:    ("Eyes closed",    WARN),
    EventType.FACE_ABSENT:    ("Not at desk",    WARN),
    EventType.PHONE_DETECTED: ("Phone",          BAD),
    EventType.SOCIAL_MEDIA:   ("Social media",   BAD),
    EventType.UNKNOWN_APP:    ("Other",          TEXT_DIM),
}


class FocusGuardApp:

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("FocusGuard")
        self.root.geometry("1080x720")
        self.root.configure(bg=BG)
        self.root.minsize(960, 640)

        # Data structures
        self.event_window  = EventDeque()
        self.session_map   = SessionHashMap()
        self.alert_heap    = AlertHeap()
        self.interval_tree = IntervalTree()

        # Detection modules
        self.face_detector:  FaceDetector  | None = None
        self.phone_detector: PhoneDetector | None = None
        self.activity_monitor = ActivityMonitor()
        self.feedback = FeedbackManager()

        # State
        self.running = False
        self.cap: cv2.VideoCapture | None = None
        self.worker: threading.Thread | None = None
        self.latest_frame_for_ui = None
        self.frame_lock = threading.Lock()
        self._session_start_time: float | None = None
        self._rec_blink_on = True
        self._rec_blink_counter = 0
        self._placeholder_img = self._make_placeholder()
        self._logo_img = self._make_logo()

        # Pre-created widgets for metrics
        self._stat_row_widgets: dict = {}
        self._last_active_window_sig: tuple | None = None

        # Screen management
        self.welcome_frame: tk.Frame | None = None
        self.session_frame: tk.Frame | None = None

        self._build_welcome_screen()
        self._schedule_ui_updates()

    # ========== GRAPHICS ASSETS ==========
    def _make_logo(self) -> ImageTk.PhotoImage:
        """FocusGuard logo - concentric circles with center dot."""
        size = 80
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        cx, cy = size // 2, size // 2
        # Outer rings
        for i, r in enumerate([36, 26, 16]):
            alpha = 255 - i * 40
            draw.ellipse([cx - r, cy - r, cx + r, cy + r],
                         outline=(232, 185, 35, alpha), width=2)
        # Center dot
        draw.ellipse([cx - 4, cy - 4, cx + 4, cy + 4],
                     fill=(232, 185, 35, 255))
        return ImageTk.PhotoImage(img)

    def _make_placeholder(self) -> ImageTk.PhotoImage:
        w, h = FRAME_WIDTH // 2 + 40, FRAME_HEIGHT // 2 + 20
        img = Image.new("RGB", (w, h), (10, 14, 19))
        draw = ImageDraw.Draw(img)
        cx, cy = w // 2, h // 2 - 8
        for r in (46, 32, 18):
            draw.ellipse([cx - r, cy - r, cx + r, cy + r],
                         outline=(60, 68, 78), width=1)
        draw.ellipse([cx - 4, cy - 4, cx + 4, cy + 4],
                     fill=(139, 152, 165))
        try:
            font = ImageFont.truetype("arial.ttf", 12)
        except Exception:
            font = ImageFont.load_default()
        text = "awaiting camera"
        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        draw.text((cx - tw // 2, cy + 60), text,
                  fill=(110, 120, 132), font=font)
        return ImageTk.PhotoImage(img)

    # ========== WELCOME SCREEN ==========
    def _build_welcome_screen(self):
        """Karşılama ekranı — logo, başlık, özellikler, Start butonu."""
        if self.session_frame is not None:
            self.session_frame.destroy()
            self.session_frame = None

        self.welcome_frame = tk.Frame(self.root, bg=BG)
        self.welcome_frame.pack(fill="both", expand=True)

        # Merkezi içerik kutusu
        center = tk.Frame(self.welcome_frame, bg=BG)
        center.place(relx=0.5, rely=0.5, anchor="center")

        # Logo
        logo_label = tk.Label(center, image=self._logo_img, bg=BG)
        logo_label.image = self._logo_img
        logo_label.pack(pady=(0, 16))

        # Brand
        tk.Label(center, text="FOCUS / GUARD",
                 bg=BG, fg=TEXT,
                 font=("Georgia", 32, "bold")).pack()

        tk.Label(center, text="Intelligent study session monitor",
                 bg=BG, fg=TEXT_MUTED,
                 font=("Georgia", 13, "italic")).pack(pady=(4, 0))

        # Separator
        sep = tk.Frame(center, bg=BORDER, height=1, width=320)
        sep.pack(pady=28)

        # Feature list
        features_frame = tk.Frame(center, bg=BG)
        features_frame.pack()

        features = [
            ("◎",  "Live webcam-based focus tracking"),
            ("⊡",  "Phone & social media detection"),
            ("▤",  "Real-time statistics & alerts"),
            ("◈",  "Detailed session report on exit"),
        ]
        for icon, text in features:
            row = tk.Frame(features_frame, bg=BG)
            row.pack(anchor="w", pady=6)
            tk.Label(row, text=icon, bg=BG, fg=ACCENT,
                     font=("Georgia", 16),
                     width=2).pack(side="left", padx=(0, 14))
            tk.Label(row, text=text, bg=BG, fg=TEXT,
                     font=("Georgia", 12)).pack(side="left")

        # Start button
        tk.Frame(center, bg=BG, height=32).pack()
        self.welcome_start_btn = self._make_button(
            center, "▸   BEGIN SESSION",
            bg_normal=ACCENT, fg_normal="#0A0E13",
            bg_hover=ACCENT_HOV, fg_hover="#0A0E13",
            command=self._on_welcome_start,
            font_weight="bold",
            padx=36, pady=16, font_size=12,
        )
        self.welcome_start_btn.pack()

        # Footer hint
        tk.Frame(center, bg=BG, height=24).pack()
        tk.Label(center,
                 text="camera will activate · press End Session to stop",
                 bg=BG, fg=TEXT_DIM,
                 font=("Georgia", 10, "italic")).pack()

    def _on_welcome_start(self):
        """Welcome ekranından Start'a basıldı — session ekranına geç ve başlat."""
        # Önce session ekranını inşa et
        self.welcome_frame.destroy()
        self.welcome_frame = None
        self._build_session_screen()
        # Oturumu başlat
        self.root.after(100, self.start_session)

    # ========== SESSION SCREEN ==========
    def _build_session_screen(self):
        """Canlı oturum ekranı — kamera + metrikler."""
        self.session_frame = tk.Frame(self.root, bg=BG)
        self.session_frame.pack(fill="both", expand=True)

        # --- HEADER ---
        header = tk.Frame(self.session_frame, bg=BG)
        header.pack(fill="x", padx=28, pady=(20, 12))

        # Left: brand
        left_hdr = tk.Frame(header, bg=BG)
        left_hdr.pack(side="left")

        tk.Label(left_hdr, text="FOCUS / GUARD",
                 bg=BG, fg=TEXT,
                 font=("Georgia", 18, "bold")).pack(side="left")

        tk.Label(left_hdr, text="  ·  live session",
                 bg=BG, fg=TEXT_MUTED,
                 font=("Georgia", 11, "italic")
                 ).pack(side="left", pady=(6, 0))

        # Right: timer + status
        right_hdr = tk.Frame(header, bg=BG)
        right_hdr.pack(side="right")

        self.status_dot = tk.Canvas(right_hdr, width=12, height=12,
                                     bg=BG, highlightthickness=0)
        self._dot_oval = self.status_dot.create_oval(
            2, 2, 10, 10, fill=OK, outline=""
        )
        self.status_dot.pack(side="left", padx=(0, 10), pady=(4, 0))

        self.session_time_label = tk.Label(right_hdr, text="00:00",
                                            bg=BG, fg=TEXT,
                                            font=("Consolas", 15))
        self.session_time_label.pack(side="left")

        # Divider
        tk.Frame(self.session_frame, bg=BORDER, height=1).pack(fill="x", padx=28)

        # --- MAIN CONTENT ---
        main = tk.Frame(self.session_frame, bg=BG)
        main.pack(fill="both", expand=True, padx=28, pady=18)

        # LEFT: camera + controls
        left_col = tk.Frame(main, bg=BG)
        left_col.pack(side="left", fill="both", expand=True)

        cam_card = tk.Frame(left_col, bg=SURFACE,
                             highlightthickness=1,
                             highlightbackground=BORDER)
        cam_card.pack(fill="both", expand=True, pady=(0, 16))

        cam_hdr = tk.Frame(cam_card, bg=SURFACE)
        cam_hdr.pack(fill="x", padx=20, pady=(16, 6))
        tk.Label(cam_hdr, text="◎  live camera",
                 bg=SURFACE, fg=TEXT_MUTED,
                 font=("Georgia", 10, "italic")).pack(side="left")
        self.rec_indicator = tk.Label(cam_hdr, text="● REC",
                                       bg=SURFACE, fg=BAD,
                                       font=("Consolas", 9, "bold"))
        self.rec_indicator.pack(side="right")

        cam_body = tk.Frame(cam_card, bg=SURFACE)
        cam_body.pack(fill="both", expand=True, padx=20, pady=(2, 20))

        self.video_label = tk.Label(cam_body, bg="#000",
                                     image=self._placeholder_img,
                                     borderwidth=0)
        self.video_label.image = self._placeholder_img
        self.video_label.pack(expand=True)

        # End session button (prominent)
        ctl = tk.Frame(left_col, bg=BG)
        ctl.pack(fill="x")

        self.stop_btn = self._make_button(
            ctl, "■   END SESSION",
            bg_normal=BAD, fg_normal="#fff",
            bg_hover="#FF6B60", fg_hover="#fff",
            command=self.stop_session,
            font_weight="bold",
            padx=32, pady=14,
        )
        self.stop_btn.pack(side="left")

        tk.Label(ctl, text="   generates a detailed report on finish",
                 bg=BG, fg=TEXT_DIM,
                 font=("Georgia", 10, "italic")).pack(side="left")

        # RIGHT: metrics panel
        right_col = tk.Frame(main, bg=BG, width=340)
        right_col.pack(side="right", fill="y", padx=(22, 0))
        right_col.pack_propagate(False)

        # Focus score card
        score_card = tk.Frame(right_col, bg=SURFACE,
                               highlightthickness=1,
                               highlightbackground=BORDER)
        score_card.pack(fill="x", pady=(0, 16))

        tk.Label(score_card, text="LIVE FOCUS SCORE",
                 bg=SURFACE, fg=ACCENT,
                 font=("Consolas", 9, "bold")
                 ).pack(anchor="w", padx=22, pady=(18, 2))

        self.score_label = tk.Label(score_card, text="100",
                                     bg=SURFACE, fg=OK,
                                     font=("Georgia", 56, "bold"))
        self.score_label.pack(anchor="w", padx=18, pady=(0, 0))

        self.score_caption = tk.Label(score_card, text="session starting…",
                                       bg=SURFACE, fg=TEXT_MUTED,
                                       font=("Georgia", 10, "italic"))
        self.score_caption.pack(anchor="w", padx=22, pady=(0, 20))

        # Progress bar
        self.score_bar_canvas = tk.Canvas(
            score_card, height=4, bg=SURFACE_2,
            highlightthickness=0, bd=0
        )
        self.score_bar_canvas.pack(fill="x", padx=22, pady=(0, 18))
        self.score_bar_rect = self.score_bar_canvas.create_rectangle(
            0, 0, 0, 4, fill=OK, outline=""
        )

        # Last 60s card
        window_card = tk.Frame(right_col, bg=SURFACE,
                                highlightthickness=1,
                                highlightbackground=BORDER)
        window_card.pack(fill="x", pady=(0, 16))

        tk.Label(window_card, text="LAST 60 SECONDS",
                 bg=SURFACE, fg=ACCENT,
                 font=("Consolas", 9, "bold")
                 ).pack(anchor="w", padx=22, pady=(16, 12))

        stats_body = tk.Frame(window_card, bg=SURFACE)
        stats_body.pack(fill="x", padx=22, pady=(0, 18))

        stable_order = [
            EventType.FOCUSED,
            EventType.PRODUCTIVE_APP,
            EventType.LOOKING_AWAY,
            EventType.EYES_CLOSED,
            EventType.FACE_ABSENT,
            EventType.PHONE_DETECTED,
            EventType.SOCIAL_MEDIA,
            EventType.UNKNOWN_APP,
        ]
        for etype in stable_order:
            label_text, dot_color = EVENT_PRETTY[etype]
            row = tk.Frame(stats_body, bg=SURFACE)
            dot = tk.Label(row, text="●", bg=SURFACE, fg=dot_color,
                            font=("Georgia", 10))
            dot.pack(side="left")
            txt = tk.Label(row, text=f"  {label_text}",
                            bg=SURFACE, fg=TEXT,
                            font=("Georgia", 10))
            txt.pack(side="left")
            cnt = tk.Label(row, text="0", bg=SURFACE, fg=TEXT_MUTED,
                            font=("Consolas", 10))
            cnt.pack(side="right")
            self._stat_row_widgets[etype] = (row, cnt)

        self._empty_label = tk.Label(
            stats_body, text="collecting data…",
            bg=SURFACE, fg=TEXT_MUTED,
            font=("Georgia", 10, "italic")
        )
        self._empty_label.pack(anchor="w")

        # Active window card
        active_card = tk.Frame(right_col, bg=SURFACE,
                                highlightthickness=1,
                                highlightbackground=BORDER)
        active_card.pack(fill="x")

        tk.Label(active_card, text="ACTIVE WINDOW",
                 bg=SURFACE, fg=ACCENT,
                 font=("Consolas", 9, "bold")
                 ).pack(anchor="w", padx=22, pady=(16, 4))

        self.active_classification = tk.Label(
            active_card, text="—",
            bg=SURFACE, fg=TEXT,
            font=("Georgia", 13, "italic"))
        self.active_classification.pack(anchor="w", padx=22)

        self.active_title = tk.Label(
            active_card, text="",
            bg=SURFACE, fg=TEXT_MUTED,
            font=("Consolas", 9),
            wraplength=280, justify="left")
        self.active_title.pack(anchor="w", padx=22, pady=(2, 18))

    # ========== BUTTON BUILDER WITH HOVER ==========
    def _make_button(self, parent, text, bg_normal, fg_normal,
                      bg_hover, fg_hover, command,
                      font_weight="normal", padx=28, pady=14, font_size=11):
        btn = tk.Button(parent, text=text, command=command,
                         bg=bg_normal, fg=fg_normal,
                         font=("Georgia", font_size, font_weight),
                         bd=0, padx=padx, pady=pady,
                         cursor="hand2",
                         activebackground=bg_hover,
                         activeforeground=fg_hover)

        def on_enter(_):
            if btn["state"] != "disabled":
                btn.configure(bg=bg_hover, fg=fg_hover)
        def on_leave(_):
            if btn["state"] != "disabled":
                btn.configure(bg=bg_normal, fg=fg_normal)

        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        return btn

    # ========== CAMERA OPEN ==========
    def _open_camera(self) -> cv2.VideoCapture | None:
        attempts = []
        if CAMERA_BACKEND == "dshow":
            attempts.append(("DirectShow", cv2.CAP_DSHOW))
            attempts.append(("MSMF", cv2.CAP_MSMF))
        attempts.append(("Default", cv2.CAP_ANY))

        for name, flag in attempts:
            try:
                cap = cv2.VideoCapture(CAMERA_INDEX, flag)
                if cap.isOpened():
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
                    for _ in range(3):
                        cap.read()
                    ok, _ = cap.read()
                    if ok:
                        print(f"[FocusGuard] Camera opened (backend: {name})")
                        return cap
                cap.release()
            except Exception as e:
                print(f"[FocusGuard] {name} backend error: {e}")
        return None

    # ========== SESSION LIFECYCLE ==========
    def start_session(self):
        if self.running:
            return
        try:
            self.score_caption.config(text="loading models…")
            self.root.update_idletasks()
            self.face_detector  = FaceDetector()
            self.phone_detector = PhoneDetector()
        except ImportError as e:
            messagebox.showerror(
                "Missing library",
                f"{e}\n\nRun:\npip install -r requirements.txt"
            )
            self._return_to_welcome()
            return
        except Exception as e:
            messagebox.showerror("Error", f"Model load failed:\n{e}")
            self._return_to_welcome()
            return

        self.cap = self._open_camera()
        if self.cap is None:
            messagebox.showerror(
                "Camera unavailable",
                "Could not open webcam. Checklist:\n\n"
                "• Close other apps using the camera "
                "(Zoom, Teams, OBS)\n"
                "• Settings > Privacy > Camera access enabled\n"
                "• Try CAMERA_INDEX = 1 in config.py"
            )
            self._return_to_welcome()
            return

        self.session_map.start_session()
        self._session_start_time = time.time()
        self.running = True

        self.status_dot.itemconfig(self._dot_oval, fill=OK)
        self.score_caption.config(text="session in progress")

        self.worker = threading.Thread(target=self._detection_loop,
                                        daemon=True)
        self.worker.start()

    def _return_to_welcome(self):
        """Hata durumunda welcome ekranına geri dön."""
        if self.session_frame is not None:
            self.session_frame.destroy()
            self.session_frame = None
        self._build_welcome_screen()

    def stop_session(self):
        if not self.running:
            return
        self.running = False
        self.stop_btn.configure(state="disabled",
                                 bg=SURFACE_2, fg=TEXT_DIM)
        self.score_caption.config(text="generating report…")
        self.status_dot.itemconfig(self._dot_oval, fill=WARN)
        self.rec_indicator.config(text="")
        self.root.update_idletasks()

        if self.worker:
            self.worker.join(timeout=2.0)
        if self.cap:
            self.cap.release()
        if self.face_detector:
            self.face_detector.close()

        self.video_label.configure(image=self._placeholder_img)
        self.video_label.image = self._placeholder_img

        df = self.session_map.to_dataframe()
        duration = self.session_map.session_duration_seconds()

        engine = StatisticsEngine()
        stats = engine.analyze(df, duration_sec=duration)

        generator = ReportGenerator()
        report_path = generator.generate(stats, df)
        print(f"\n[FocusGuard] Report: {report_path.resolve()}")

        self.status_dot.itemconfig(self._dot_oval, fill="#4B5563")

        if REPORT_OPEN_AUTOMATICALLY:
            try:
                webbrowser.open(f"file://{report_path.resolve()}")
            except Exception:
                pass

        # 2 saniye sonra welcome ekranına dön
        self.root.after(1500, self._return_to_welcome)

    # ========== DETECTION LOOP ==========
    def _detection_loop(self):
        frame_idx = 0
        consecutive_failures = 0
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                consecutive_failures += 1
                if consecutive_failures > 30:
                    print("[FocusGuard] Camera lost.")
                    break
                time.sleep(0.05)
                continue
            consecutive_failures = 0
            frame_idx += 1

            with self.frame_lock:
                self.latest_frame_for_ui = frame.copy()

            if frame_idx % PROCESS_EVERY_N_FRAMES != 0:
                continue

            try:
                face_state = self.face_detector.analyze(frame)
                self._register_event(face_state.to_event_type())
            except Exception as e:
                print(f"[face] {e}")

            try:
                phone = self.phone_detector.detect(frame)
                if phone.found:
                    self._register_event(
                        EventType.PHONE_DETECTED,
                        meta={"detail": f"conf: {phone.confidence:.2f}"},
                    )
            except Exception as e:
                print(f"[phone] {e}")

            try:
                win_info = self.activity_monitor.get_active_window_info()
                if win_info is not None:
                    self._register_event(
                        win_info.classification,
                        meta={"detail": win_info.title[:60]},
                    )
            except Exception:
                pass

    # ========== EVENT RECORDING ==========
    def _register_event(self, event_type: str, meta: dict | None = None):
        self.event_window.push(Event(type=event_type, meta=meta))
        current_score = self.event_window.get_focus_score()
        self.session_map.record_event(event_type, current_score)
        now = time.time()
        self.interval_tree.insert(Interval(
            start=now, end=now + 1.0, event_type=event_type, meta=meta,
        ))
        distracting = {
            EventType.LOOKING_AWAY, EventType.EYES_CLOSED,
            EventType.FACE_ABSENT, EventType.PHONE_DETECTED,
            EventType.SOCIAL_MEDIA,
        }
        if event_type in distracting:
            self.alert_heap.push_alert(event_type, meta)

    # ========== UI UPDATES ==========
    def _schedule_ui_updates(self):
        if self.session_frame is not None:
            self._update_video_frame()
            self._update_metrics()
            self._update_session_time()
            self._update_rec_blink()
            self._process_alerts()
        self.root.after(150, self._schedule_ui_updates)

    def _update_video_frame(self):
        with self.frame_lock:
            frame = (self.latest_frame_for_ui.copy()
                     if self.latest_frame_for_ui is not None else None)
        if frame is None:
            return
        target_w = FRAME_WIDTH // 2 + 40
        target_h = FRAME_HEIGHT // 2 + 20
        small = cv2.resize(frame, (target_w, target_h))
        rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
        img = ImageTk.PhotoImage(Image.fromarray(rgb))
        self.video_label.configure(image=img)
        self.video_label.image = img

    def _update_metrics(self):
        if not self.running:
            return
        score = self.event_window.get_focus_score()
        color = OK if score >= 75 else WARN if score >= 50 else BAD
        self.score_label.configure(text=f"{score:.0f}", fg=color)

        # Update progress bar
        try:
            self.score_bar_canvas.update_idletasks()
            bar_w = self.score_bar_canvas.winfo_width()
            if bar_w > 1:
                fill_w = int(bar_w * (score / 100))
                self.score_bar_canvas.coords(
                    self.score_bar_rect, 0, 0, fill_w, 4
                )
                self.score_bar_canvas.itemconfig(
                    self.score_bar_rect, fill=color
                )
        except Exception:
            pass

        # Last-60s rows: widgets are pre-created, only toggle + update
        any_visible = False
        for etype, (row, cnt_label) in self._stat_row_widgets.items():
            c = self.event_window.count_of(etype)
            if c > 0:
                cnt_label.configure(text=str(c))
                if not row.winfo_ismapped():
                    row.pack(fill="x", pady=3)
                any_visible = True
            else:
                if row.winfo_ismapped():
                    row.pack_forget()

        if any_visible and self._empty_label.winfo_ismapped():
            self._empty_label.pack_forget()
        elif not any_visible and not self._empty_label.winfo_ismapped():
            self._empty_label.pack(anchor="w")

        # Active window
        win_info = self.activity_monitor._last_info
        if win_info:
            sig = (win_info.classification, win_info.title[:80])
            if sig != self._last_active_window_sig:
                self._last_active_window_sig = sig
                label, color = EVENT_PRETTY.get(
                    win_info.classification,
                    (win_info.classification, TEXT)
                )
                self.active_classification.configure(text=label, fg=color)
                self.active_title.configure(text=win_info.title[:90])

    def _update_session_time(self):
        if self._session_start_time and self.running:
            elapsed = int(time.time() - self._session_start_time)
            self.session_time_label.configure(
                text=f"{elapsed//60:02d}:{elapsed%60:02d}", fg=TEXT
            )

    def _update_rec_blink(self):
        if not self.running:
            return
        self._rec_blink_counter += 1
        if self._rec_blink_counter >= 5:
            self._rec_blink_counter = 0
            self._rec_blink_on = not self._rec_blink_on
            self.rec_indicator.configure(
                text="● REC" if self._rec_blink_on else "    "
            )

    def _process_alerts(self):
        if not self.running:
            return
        alert = self.alert_heap.pop_next_alert()
        if alert is not None:
            etype, meta = alert
            self.feedback.show(etype, meta)


# ============ Entry point ============
def main():
    root = tk.Tk()
    try:
        import sys, os
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(base_path, "assets", "icon.ico")
        if os.path.exists(icon_path):
            root.iconbitmap(icon_path)
    except Exception:
        pass

    app = FocusGuardApp(root)

    def on_close():
        if app.running:
            if messagebox.askyesno(
                "Close", "Session still active. End and generate report?"
            ):
                app.stop_session()
                # Geri dönüşü beklemek için biraz gecikme
                root.after(2000, root.destroy)
                return
            else:
                return
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()


if __name__ == "__main__":
    main()
