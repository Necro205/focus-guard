# 💿 EXE Üretme Rehberi — FocusGuard.exe

Bu rehber, projeyi çift tıkladığında açılan bir Windows uygulamasına (.exe) dönüştürür.

---

## 🎯 Sonuç

- `dist\FocusGuard.exe` — **~400-600 MB** tek dosya
- Çift tıkla → 10-15 saniyede açılır (ilk sefer yavaş, sonrası hızlı)
- Python kurulumuna **ihtiyaç yok** — başkasına da gönderebilirsin
- Konsol penceresi gözükmez

---

## ✅ Ön Koşullar

Python 3.11 kurulu olmalı ve kütüphaneler yüklü olmalı. Son mesajımızdaki adımları yaptıysan hazırsın.

---

## 🚀 Kurulum — 2 Adım

### Adım 1: Build dosyasını çalıştır

`focus_guard` klasörüne git, **`build.bat`** dosyasına çift tıkla.

Alternatif (komut isteminden):
```
build.bat
```

Şunlar olacak:
- PyInstaller otomatik yüklenecek (eğer yoksa)
- YOLOv8 modeli indirilecek (eğer yoksa)
- **5-15 dakika** build sürecek (dosya kütüphaneleri paketleniyor)
- Sonunda `dist\FocusGuard.exe` oluşacak

### Adım 2: EXE'yi kullan

```
dist\FocusGuard.exe
```

dosyasına çift tıkla. Uygulama doğrudan açılacak. Artık `python main.py` yazmana gerek yok.

---

## 📦 Çıkarılan Dosyaları İstediğin Yere Taşı

`dist\FocusGuard.exe` dosyasını:
- Masaüstüne kopyala → kısayol olarak kullan
- USB'ye at → başka bilgisayarda da çalışır
- Hocaya e-posta ile gönder (dosya büyük olduğu için WeTransfer / Google Drive ile)

Sadece `.exe` yeterli, başka dosya gerekmiyor — **her şey içinde paketli**.

---

## 🐛 Sorun Giderme

### Build sırasında "No module named 'xyz'" hatası

`FocusGuard.spec` dosyasını Not Defteri ile aç, `extra_hidden` listesine eksik modülü ekle:

```python
extra_hidden = [
    'PIL._tkinter_finder',
    'xyz',    # <-- Yeni eklenen
    ...
]
```

Tekrar `build.bat` çalıştır.

### EXE açılıyor ama hemen kapanıyor

Konsol çıktısını görmek için `FocusGuard.spec` dosyasında:
```python
console=False,    # Bunu True yap
```

Sonra build et, çalıştır — hata mesajı görünür pencerede kalacak.

### "Windows Defender uyarısı" çıkıyor

Windows Defender yeni build edilen exe'leri bilmediği için şüpheyle yaklaşır. **"More info" → "Run anyway"** de. Sadece ilk seferlik.

Kalıcı çözüm: Windows Ayarlar → Güvenlik → Virüs ve tehdit koruması → Hariç tutma → EXE dosyasını ekle.

### EXE çok büyük (600 MB+)

Normal. İçinde:
- MediaPipe modeli (~100 MB)
- YOLOv8n (~6 MB)
- OpenCV (~60 MB)
- PyTorch (~200 MB — YOLO'nun ihtiyacı)
- NumPy/Pandas/SciPy (~100 MB)
- Python runtime (~30 MB)

Daha küçük olması için:
1. `--onedir` moduna geç (tek dosya değil, klasör) → biraz daha küçük olur
2. PyTorch'u komple kaldır ve YOLO yerine Haar cascade kullan (zaten eski OpenCV sürümü bunu yapıyordu)

### İlk açılış yavaş

Normal. `--onefile` modunda exe her açılışta kendini geçici klasöre açıyor. İlk sefer 15-20 sn. Alternatif:

```
py -3.11 -m PyInstaller FocusGuard.spec --clean --onedir
```

Bu modda `dist\FocusGuard\` klasörü oluşur, içinde `FocusGuard.exe` var. Tek dosya değil, ama çalışması anında.

---

## 🎁 Bonus: Kısayol Oluştur

`dist\FocusGuard.exe` üzerinde sağ tık → **"Kısayol oluştur"** → kısayolu masaüstüne sürükle.

Kısayola sağ tık → **"Özellikler"** → **"Simgeyi değiştir"** → istediğin .ico'yu seç. (İstersen `assets\icon.ico` dosyasını oraya koyup kullanabilirsin.)

---

## 🎓 Sunum İpucu

Hocaya gösterirken EXE'nin avantajı:
- Hocanın bilgisayarında Python olması gerekmez
- "Kurulum" yok, tek dosya çift tık
- Profesyonel "ürün" izlenimi verir

Demo için masaüstünde `FocusGuard.exe` olsun, sunum sırasında çift tıkla — saniyeler içinde aç.
