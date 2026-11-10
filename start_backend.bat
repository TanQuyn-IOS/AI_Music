@echo off
chcp 65001 >nul
echo ====================================
echo   Sonavia AI Music - Backend
echo ====================================
cd /d "%~dp0backend"

:: Kich hoat moi truong ao
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
) else (
    echo [1/5] Tao moi truong ao moi...
    python -m venv venv
    call venv\Scripts\activate.bat
    echo [2/5] Cai dat thu vien co ban...
    pip install -r requirements.txt
    echo [3/5] Cai dat PyTorch CUDA...
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
    echo [4/5] Cai dat AI packages...
    pip install scipy soundfile
)

echo [Migrations] Chay migrations...
python manage.py migrate --run-syncdb

echo [Data] Tao du lieu mau (neu chua co)...
python seed_data.py

echo.
echo ========================================
echo  Backend dang chay tai:
echo  http://localhost:8000
echo  Admin:  http://localhost:8000/admin
echo ========================================
echo.
echo  AI Music Generator:
echo  - MusicGen warm-up tu dong khi khoi dong
echo  - Tao nhac 15s: ~8-12 giay (sau warm-up)
echo  - Tao nhac 30s: ~18-25 giay (sau warm-up)
echo ========================================
echo.
set DJANGO_WARMUP=1
set PYTHONUTF8=1
python manage.py runserver 127.0.0.1:8000

pause
