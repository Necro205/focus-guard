"""
face_detector.py — MediaPipe Face Mesh ile Yüz / Odak Tespiti
===============================================================
MediaPipe Face Mesh ile 468 yüz landmark'ı alır. Buradan türetir:
  1. Yüz mevcudiyeti
  2. Kafa pozu (yaw/pitch — solvePnP ile gerçek 3D tahmini)
  3. Göz kapalılığı (EAR — Eye Aspect Ratio, Soukupová & Čech 2016)
  4. Bunlardan türetilen durum: FOCUSED / LOOKING_AWAY / EYES_CLOSED / FACE_ABSENT

EAR formülü:
    EAR = ( ||p2-p6|| + ||p3-p5|| ) / ( 2 * ||p1-p4|| )
6 landmark ile göz yüksekliği/genişliği oranını verir; kapalıyken düşer.

Not: mediapipe 0.10.14 sürümü Python 3.11 ile önerilen kurulumdur.
"""

import math
import time
from dataclasses import dataclass

import cv2
import numpy as np

try:
    import mediapipe as mp
    _MP_AVAILABLE = True
except ImportError:
    _MP_AVAILABLE = False

from config import (
    MAX_YAW_DEGREES, MAX_PITCH_DEGREES,
    EYE_AR_THRESHOLD, EYE_AR_CONSEC_FRAMES,
    FACE_ABSENT_SECONDS, EventType,
)


# MediaPipe Face Mesh landmark indeksleri (468-lu modele göre)
LEFT_EYE_EAR  = [33, 160, 158, 133, 153, 144]      # p1..p6
RIGHT_EYE_EAR = [362, 385, 387, 263, 373, 380]

# Kafa pozu için 6 ana nokta (solvePnP girişi)
POSE_INDICES = {
    "nose_tip":               1,
    "chin":                   199,
    "left_eye_left_corner":   33,
    "right_eye_right_corner": 263,
    "left_mouth_corner":      61,
    "right_mouth_corner":     291,
}

# Bu noktaların gerçek dünya (3D) yaklaşık koordinatları (mm)
FACE_MODEL_3D = np.array([
    [0.0,    0.0,    0.0],      # nose tip
    [0.0,   -63.6,  -12.5],     # chin
    [-43.3,  32.7,  -26.0],     # left eye corner
    [43.3,   32.7,  -26.0],     # right eye corner
    [-28.9, -28.9,  -24.1],     # left mouth corner
    [28.9,  -28.9,  -24.1],     # right mouth corner
], dtype=np.float64)


@dataclass
class FaceState:
    present: bool
    looking_at_screen: bool
    eyes_closed: bool
    yaw: float = 0.0
    pitch: float = 0.0
    ear: float = 1.0

    def to_event_type(self) -> str:
        if not self.present:
            return EventType.FACE_ABSENT
        if self.eyes_closed:
            return EventType.EYES_CLOSED
        if not self.looking_at_screen:
            return EventType.LOOKING_AWAY
        return EventType.FOCUSED


class FaceDetector:
    """Bir frame alır, FaceState döndürür."""

    def __init__(self):
        if not _MP_AVAILABLE:
            raise ImportError(
                "mediapipe yüklü değil. "
                "`pip install mediapipe==0.10.14` ile kurun."
            )
        self._mp_face = mp.solutions.face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=False,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        self._consec_closed = 0
        self._last_seen = time.time()

    # ---------- Ana API ----------
    def analyze(self, frame_bgr: np.ndarray) -> FaceState:
        h, w = frame_bgr.shape[:2]
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        result = self._mp_face.process(rgb)

        if not result.multi_face_landmarks:
            absent = (time.time() - self._last_seen) > FACE_ABSENT_SECONDS
            return FaceState(
                present=not absent,
                looking_at_screen=False,
                eyes_closed=False,
            )

        self._last_seen = time.time()
        lmk = result.multi_face_landmarks[0].landmark

        # --- EAR hesapla (iki gözün ortalaması) ---
        ear_left  = self._eye_aspect_ratio(lmk, LEFT_EYE_EAR,  w, h)
        ear_right = self._eye_aspect_ratio(lmk, RIGHT_EYE_EAR, w, h)
        ear = (ear_left + ear_right) / 2.0

        if ear < EYE_AR_THRESHOLD:
            self._consec_closed += 1
        else:
            self._consec_closed = 0
        eyes_closed = self._consec_closed >= EYE_AR_CONSEC_FRAMES

        # --- Kafa pozu (solvePnP) ---
        yaw, pitch = self._head_pose(lmk, w, h)
        looking = (abs(yaw) < MAX_YAW_DEGREES and
                   abs(pitch) < MAX_PITCH_DEGREES)

        return FaceState(
            present=True,
            looking_at_screen=looking,
            eyes_closed=eyes_closed,
            yaw=yaw, pitch=pitch, ear=ear,
        )

    def close(self):
        self._mp_face.close()

    # ---------- Yardımcılar ----------
    @staticmethod
    def _eye_aspect_ratio(lmk, idx: list, w: int, h: int) -> float:
        pts = [(lmk[i].x * w, lmk[i].y * h) for i in idx]
        def d(a, b): return math.hypot(a[0] - b[0], a[1] - b[1])
        vert  = d(pts[1], pts[5]) + d(pts[2], pts[4])
        horiz = d(pts[0], pts[3])
        return vert / (2.0 * horiz) if horiz > 0 else 0.0

    @staticmethod
    def _head_pose(lmk, w: int, h: int):
        """solvePnP ile yaw ve pitch (derece cinsinden)."""
        img_pts = np.array([
            [lmk[POSE_INDICES["nose_tip"]].x * w,
             lmk[POSE_INDICES["nose_tip"]].y * h],
            [lmk[POSE_INDICES["chin"]].x * w,
             lmk[POSE_INDICES["chin"]].y * h],
            [lmk[POSE_INDICES["left_eye_left_corner"]].x * w,
             lmk[POSE_INDICES["left_eye_left_corner"]].y * h],
            [lmk[POSE_INDICES["right_eye_right_corner"]].x * w,
             lmk[POSE_INDICES["right_eye_right_corner"]].y * h],
            [lmk[POSE_INDICES["left_mouth_corner"]].x * w,
             lmk[POSE_INDICES["left_mouth_corner"]].y * h],
            [lmk[POSE_INDICES["right_mouth_corner"]].x * w,
             lmk[POSE_INDICES["right_mouth_corner"]].y * h],
        ], dtype=np.float64)

        # Kamera matrisi yaklaşık (lens kalibre edilmediyse makul varsayım)
        focal = w
        camera_matrix = np.array([
            [focal, 0,     w / 2.0],
            [0,     focal, h / 2.0],
            [0,     0,     1       ],
        ], dtype=np.float64)
        dist_coeffs = np.zeros((4, 1))

        ok, rvec, _tvec = cv2.solvePnP(
            FACE_MODEL_3D, img_pts, camera_matrix, dist_coeffs,
            flags=cv2.SOLVEPNP_ITERATIVE,
        )
        if not ok:
            return 0.0, 0.0

        rot_mat, _ = cv2.Rodrigues(rvec)
        # Euler açıları (yaw = Y ekseni, pitch = X ekseni)
        sy = math.sqrt(rot_mat[0, 0] ** 2 + rot_mat[1, 0] ** 2)
        singular = sy < 1e-6
        if not singular:
            pitch = math.atan2(-rot_mat[2, 0], sy)
            yaw   = math.atan2(rot_mat[1, 0], rot_mat[0, 0])
        else:
            pitch = math.atan2(-rot_mat[2, 0], sy)
            yaw   = 0.0
        return math.degrees(yaw), math.degrees(pitch)
