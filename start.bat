@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================
echo   Doraemon LOG Dashboard - LIVE Server
echo ============================================
echo.
echo Dang mo http://127.0.0.1:8765 ...
echo Giữ cửa sổ này mở. Nhan Ctrl+C de tat.
echo.
py -3 server.py
if errorlevel 1 (
  echo.
  echo Loi: khong chay duoc. Thu: python server.py
  python server.py
)
pause
