# 🚀 FocusGuard — Sıfırdan Kurulum Rehberi (Windows)

> Bu rehber; Python, terminal, pip gibi kavramları hiç duymamış birinin bile uygulamayı çalıştırabilmesi için yazıldı. Adım adım, aceleci olmadan takip et.

---

## 🧭 Neye İhtiyacın Var?

1. ✅ Windows 10 veya 11 bilgisayar
2. ✅ Çalışan bir webcam (dahili laptop kamerası yeterli)
3. ✅ İnternet bağlantısı (sadece ilk kurulum için)

Tahmini süre: **15-20 dakika**. Adımların %90'ı "kur ve bekle" şeklinde, yazı yazma işi çok az.

---

## 📦 ADIM 1 — Python'u Kur (5 dakika)

Python, bu projenin çalışmasını sağlayan programlama dilidir. Tıpkı bir Word dosyasını açmak için Word'e ihtiyacın olması gibi, `.py` dosyalarını çalıştırmak için Python'a ihtiyacın var.

### 1.1. İndir

1. Tarayıcıda şu adrese git: **https://www.python.org/downloads/**
2. Büyük sarı buton: **"Download Python 3.12.x"** — tıkla. `.exe` dosyası inecek (yaklaşık 25 MB).

### 1.2. Kur — ⚠️ BU ADIM ÇOK KRİTİK

İndirilen dosyaya çift tıkla. Bir pencere açılacak. **Aşağı tamam tuşuna basmadan ÖNCE** şu kutucuğu mutlaka işaretle:

```
☑ Add python.exe to PATH
```

Bu kutucuğu unutursan sistem "python" komutunu tanımaz, her şey baştan olur. **Ekranın en altındaki bu kutucuğu işaretlemeden ilerleme.**

Sonra: **"Install Now"** → bekle → **"Close"**.

### 1.3. Kurulumu Doğrula

"Başlat" menüsünü aç, **"cmd"** yaz, **"Komut İstemi"**ni aç. Siyah bir pencere gelecek. İçine şunu yaz ve Enter'a bas:

```
python --version
```

Eğer **`Python 3.12.x`** gibi bir çıktı gördüysen başardın! 🎉

Eğer **"python is not recognized"** gibi bir hata aldıysan: Python yüklenirken PATH kutucuğunu işaretlememişsin demektir. Bilgisayarı yeniden başlat; hâlâ olmuyorsa Python'u denetim masasından kaldırıp 1.2 adımını tekrar yap (kutucuğu işaretleyerek).

---

## 📁 ADIM 2 — Projeyi Aç (1 dakika)

1. Sana gönderdiğim `focus_guard.zip` dosyasını indir.
2. Üstüne sağ tık → **"Tümünü Ayıkla"** (Extract All) → **"Ayıkla"**.
3. Klasörün yerini not et. Örneğin **Masaüstüne** koyarsan yol şu olur:
   ```
   C:\Users\Ramazan\Desktop\focus_guard
   ```

Bu klasörün içine girdiğinde şunları görmelisin: `main.py`, `config.py`, `requirements.txt`, `modules/`, `data_structures/`, `analysis/`, `README.md`.

---

## 💻 ADIM 3 — Komut İstemini Proje Klasöründe Aç (1 dakika)

Python kodlarını çalıştırmak için terminal gerekli. En kolay yol:

1. `focus_guard` klasörünü Dosya Gezgini'nde aç.
2. Adres çubuğuna (yukarıda `C:\Users\...\focus_guard` yazan yer) tıkla — yazıları sil — yerine şunu yaz:
   ```
   cmd
   ```
3. Enter'a bas. Siyah Komut İstemi penceresi **tam proje klasöründe açılacak**.

Emin olmak için içine şunu yaz:

```
dir
```

`main.py`, `config.py`, `requirements.txt` isimlerini görmelisin. Gördüysen doğru yerdesin.

---

## 📚 ADIM 4 — Kütüphaneleri Kur (5-10 dakika)

Projemiz MediaPipe (yüz takibi), YOLOv8 (telefon tanıma), OpenCV (kamera), Pandas (istatistik) gibi hazır kütüphaneler kullanıyor. Hepsini tek komutla yükleyelim. Komut İstemine yapıştır:

```
pip install -r requirements.txt
```

Enter'a bas. **Kurulum 5-10 dakika sürebilir.** Toplam ~500 MB indirilecek. Ekranda satır satır "Downloading..." yazılar akacak. Sabırla bekle.

Sonunda başarılı olursa şunu göreceksin:
```
Successfully installed opencv-python-4.10.0 mediapipe-0.10.14 ultralytics-8.3.0 ...
```

### Sık Karşılaşılan Sorunlar

**"pip is not recognized"** → Python PATH'e eklenmemiş. Adım 1.2'yi tekrar yap.

**"error: Microsoft Visual C++ 14.0 is required"** → Bu, bazı kütüphaneler için C++ derleyicisi lazım demek. Şunu indir ve kur: https://visualstudio.microsoft.com/visual-cpp-build-tools/ (kurulum sırasında "Desktop development with C++" kutusunu seç). Sonra bu adımı tekrar dene.

**Çok yavaş / zaman aşımı** → İnternetin yavaşsa veya okulun/ofisin proxy'si varsa olabilir. Şu komutu dene:
```
pip install -r requirements.txt --timeout 300
```

---

## 🎯 ADIM 5 — Uygulamayı Çalıştır (30 saniye)

Hâlâ Komut İsteminde, `focus_guard` klasörünün içindeyken, şunu yaz:

```
python main.py
```

**İlk çalıştırmada** YOLOv8 modeli (~6 MB) internetten inecek, bu yüzden 10-15 saniye bekleyeceksin. Sonraki çalıştırmalarda anında açılır.

Pencereler açılacak:
1. **"FocusGuard"** adında bir pencere — sağda skor, solda "kamera bekleniyor" yazısı
2. **"OTURUMU BAŞLAT"** butonuna bas → kamera aktif olacak, skor hesaplanmaya başlayacak
3. Bitince **"BİTİR"** → tarayıcıda otomatik rapor açılacak 📊

---

## 🐛 Sorun Giderme

### "Webcam açılamadı" hatası
- Zoom, Teams, OBS, Discord gibi kamerayı kullanan tüm programları kapat
- Windows Ayarlar → Gizlilik ve Güvenlik → Kamera → "Uygulamaların kameraya erişmesine izin ver" **AÇIK** olmalı
- Kameran başka bir numarada olabilir: `config.py` dosyasını Not Defteri ile aç, `CAMERA_INDEX = 0` satırını bul, `0` yerine `1` yaz, kaydet, tekrar dene

### "Bu tür bir dosya açılamıyor" — main.py çift tıklamak işe yaramıyor
Bu normal. Python dosyaları çift tıklayarak çalıştırılmaz; **her zaman komut isteminden `python main.py`** diye çalıştırman gerek. Adım 3 ve 5'i tekrarla.

### Rapor tarayıcıda açılmıyor
`focus_guard\reports\` klasörüne git, en son tarihli `.html` dosyasını çift tıkla.

### GUI çok yavaş, dondu gibi
`config.py` dosyasını aç, `PROCESS_EVERY_N_FRAMES = 3` satırını `PROCESS_EVERY_N_FRAMES = 6` yap. Bu, CPU yükünü yarıya indirir.

---

## 🎬 Webcam'siz Demo

Hocaya veya arkadaşlarına projeyi göstermek istiyorsun ama kameranı açmak istemiyor musun? Sentetik (yapay) veri üreten bir demo var:

```
python demo_without_webcam.py
```

60 saniye boyunca gerçekçi olaylar üretir, bildirimler verir, ve sonunda rapor açar. Sunum için ideal.

---

## 📂 Dosya Yapısı (Neyin Ne Olduğunu Anla)

```
focus_guard/
├── main.py                   ← Bunu çalıştırıyoruz
├── demo_without_webcam.py    ← Kamera olmadan demo
├── config.py                 ← Ayarlar (hassasiyet, eşikler vb.)
├── requirements.txt          ← Kütüphane listesi
│
├── data_structures/          ← 🎓 Veri Yapıları dersinin kalbi
│   ├── event_deque.py        ← Son 60 sn olayları (kayar pencere)
│   ├── session_hashmap.py    ← Dakika bazlı hash tablosu
│   ├── alert_heap.py         ← Önceliklendirilmiş uyarılar (min-heap)
│   └── interval_tree.py      ← Zaman aralığı sorguları (BST)
│
├── modules/                  ← Algılama modülleri
│   ├── face_detector.py      ← Yüz + kafa pozu (MediaPipe)
│   ├── phone_detector.py     ← Telefon tespiti (YOLOv8)
│   ├── activity_monitor.py   ← Aktif pencere izleme
│   └── feedback.py           ← Kullanıcıya uyarı gösterimi
│
├── analysis/                 ← İstatistiksel analiz
│   ├── statistics_engine.py  ← Tanımlayıcı + hipotez testleri
│   └── report_generator.py   ← HTML rapor üretimi
│
└── reports/                  ← Oturum raporlarının kaydedildiği yer
```

---

## 🎓 Hocaya Sunum Notu

Projeyi sunarken dikkat çekmek istediğin noktalar:

1. **Veri Yapıları Katmanı** — `data_structures/` klasörünü aç, her dosyanın başındaki açıklamalarda Big-O analizi var.
2. **Canlı Demo** — `main.py`'yi çalıştır, bilerek telefon göster → uyarı gelecek, sosyal medyaya gir → uyarı gelecek.
3. **İstatistik Raporu** — Shapiro-Wilk testi, Pearson korelasyonu, linear regresyon trend eğimi — hepsi otomatik üretilen HTML raporda var.
4. **Webcam'siz Demo** — Kamera çekilmesi utandırırsa `demo_without_webcam.py` ile sentetik veriden rapor üretebilirsin.

Başarılar! 🍀
