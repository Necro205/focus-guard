@echo off
REM ============================================================
REM  FocusGuard — EXE builder for Windows
REM  Çift tıkla: exe üretilir ve dist\ klasörüne konur
REM ============================================================

setlocal
echo.
echo === FocusGuard EXE Builder ===
echo.

REM Python 3.11'in varligini kontrol et
py -3.11 --version >nul 2>&1
if errorlevel 1 (
    echo [HATA] Python 3.11 bulunamadi.
    echo Lutfen Python 3.11'i kurun: https://www.python.org/downloads/release/python-3119/
    echo.
    pause
    exit /b 1
)

echo [1/4] PyInstaller kurulum kontrolu...
py -3.11 -m pip install --quiet pyinstaller>=6.0.0
if errorlevel 1 (
    echo [HATA] PyInstaller kurulamadi.
    pause
    exit /b 1
)

echo [2/4] YOLO modeli indiriliyor (ilk kurulumda ~6MB)...
py -3.11 -c "from ultralytics import YOLO; YOLO('yolov8n.pt')" >nul 2>&1

echo [3/4] EXE olusturuluyor... (5-10 dakika surebilir)
echo     Bekle, bu ilk seferde uzun surer.
py -3.11 -m PyInstaller FocusGuard.spec --clean --noconfirm
if errorlevel 1 (
    echo [HATA] Build basarisiz. Yukaridaki mesaji kontrol et.
    pause
    exit /b 1
)

echo.
echo [4/4] Temizlik...
if exist build rmdir /s /q build
del /q *.spec.bak 2>nul

echo.
echo ============================================================
echo  BASARILI!
echo ============================================================
echo.
echo  EXE dosyasi: dist\FocusGuard.exe
echo.
echo  Bu dosyayi istedigin yere kopyalayabilirsin (Masaustu vs.).
echo  Cift tiklayarak calistir. Python kurulumuna gerek yok.
echo.
pause
