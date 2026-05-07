# 🎯 FocusGuard — Akıllı Odaklanma Asistanı

Üniversite bitirme/entegrasyon projesi. Webcam, nesne tanıma ve sistem izleme kullanarak çalışma oturumlarındaki dikkat dağınıklıklarını gerçek zamanlı tespit eder; oturum sonunda detaylı istatistiksel rapor üretir.

## 📚 Kapsadığı Ders Konuları

| Ders | Uygulanan Konular |
|------|-------------------|
| **Veri Yapıları** | Deque (kayar pencere), Hash Map (O(1) erişim), Min-Heap (öncelik kuyruğu), Interval Tree (zaman aralığı sorgusu) |
| **Bilgisayarla Görme** | Yüz landmark tespiti, kafa pozu tahmini (solvePnP), Eye Aspect Ratio (EAR), YOLOv8 nesne tanıma |
| **İstatistik** | Tanımlayıcı istatistikler, zaman serisi analizi, korelasyon matrisi, hipotez testi |
| **Yazılım Mühendisliği** | Modüler mimari, thread yönetimi, GUI tasarımı, rapor üretimi |

## 🚀 Kurulum

```bash
python -m venv venv
source venv/bin/activate      # Linux/Mac
venv\Scripts\activate         # Windows

pip install -r requirements.txt
python main.py
```

## 🗂 Proje Yapısı

```
focus_guard/
├── main.py                      # Ana uygulama (GUI + orchestration)
├── config.py                    # Yapılandırma sabitleri
├── requirements.txt
├── modules/
│   ├── face_detector.py         # MediaPipe ile yüz + kafa pozu
│   ├── phone_detector.py        # YOLOv8 ile telefon tespiti
│   ├── activity_monitor.py      # Aktif pencere + sosyal medya tespiti
│   └── feedback.py              # Gerçek zamanlı kullanıcı uyarıları
├── data_structures/
│   ├── event_deque.py           # Kayar pencere için deque
│   ├── session_hashmap.py       # Dakika-bazlı istatistik hash map
│   ├── alert_heap.py            # Öncelikli uyarı kuyruğu (min-heap)
│   └── interval_tree.py         # Zaman aralığı sorgusu için BST
└── analysis/
    ├── statistics_engine.py     # İstatistiksel analiz
    └── report_generator.py      # HTML raporu
```

## 🎮 Kullanım

1. `python main.py` ile başlat
2. "Oturumu Başlat" → webcam aktif olur
3. Çalışmaya başla; sistem arka planda odaklanma puanını takip eder
4. Dikkat dağıldığında anında uyarı (popup + ses)
5. "Oturumu Bitir" → detaylı HTML raporu otomatik açılır
