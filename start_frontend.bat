@echo off
chcp 65001 >nul
echo ====================================
echo   Sonavia AI Music - Frontend
echo ====================================
cd /d "%~dp0frontend"

if not exist node_modules (
    echo Cai dat dependencies...
    npm install
)

echo.
echo ========================================
echo  Frontend dang chay tai:
echo  http://localhost:5173
echo ========================================
echo.
npm run dev

pause
