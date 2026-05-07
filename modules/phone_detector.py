"""
phone_detector.py — YOLOv8 ile Cep Telefonu Tespiti
======================================================
Ultralytics YOLOv8 nano modeli kullanır. COCO sınıfı 67 = "cell phone".

Performans notu:
----------------
YOLO her frame'de çalıştırılmaz — her ~2 saniyede bir tek frame'e uygulanır
(config.PHONE_DETECTION_INTERVAL). Bu sayede CPU'ya minimum yük biner.
"""

import time
from dataclasses import dataclass
from typing import Optional

import numpy as np

try:
    from ultralytics import YOLO
    _YOLO_AVAILABLE = True
except ImportError:
    _YOLO_AVAILABLE = False

from config import (
    YOLO_MODEL, PHONE_CLASS_ID,
    PHONE_CONFIDENCE_THRESHOLD, PHONE_DETECTION_INTERVAL,
)


@dataclass
class PhoneDetection:
    found: bool
    confidence: float = 0.0
    bbox: Optional[tuple[int, int, int, int]] = None  # x1,y1,x2,y2


class PhoneDetector:
    def __init__(self):
        if not _YOLO_AVAILABLE:
            raise ImportError(
                "ultralytics yüklü değil. `pip install ultralytics` deneyin."
            )
        # Model ilk çağrıda internetten indirilir (~6MB, nano)
        self._model = YOLO(YOLO_MODEL)
        self._last_check = 0.0
        self._last_result = PhoneDetection(found=False)

    def should_check(self) -> bool:
        """Rate limiter: son kontrolden yeterince zaman geçti mi?"""
        return time.time() - self._last_check >= PHONE_DETECTION_INTERVAL

    def detect(self, frame_bgr: np.ndarray) -> PhoneDetection:
        """
        Frame'de telefon var mı? Cooldown'dan önce çağrılırsa önceki
        sonucu döndürür (cache).
        """
        if not self.should_check():
            return self._last_result

        self._last_check = time.time()
        # YOLO BGR kabul eder; ancak biz emin olmak için dönüştürüyoruz.
        results = self._model.predict(
            source=frame_bgr,
            conf=PHONE_CONFIDENCE_THRESHOLD,
            classes=[PHONE_CLASS_ID],
            verbose=False,
            imgsz=416,            # daha küçük → daha hızlı
        )

        phones = []
        for r in results:
            if r.boxes is None:
                continue
            for box in r.boxes:
                cls_id = int(box.cls[0])
                if cls_id == PHONE_CLASS_ID:
                    conf = float(box.conf[0])
                    xyxy = box.xyxy[0].cpu().numpy().astype(int)
                    phones.append((conf, tuple(xyxy)))

        if phones:
            phones.sort(reverse=True)  # en yüksek confidence başta
            conf, bbox = phones[0]
            self._last_result = PhoneDetection(True, conf, bbox)
        else:
            self._last_result = PhoneDetection(False)

        return self._last_result
