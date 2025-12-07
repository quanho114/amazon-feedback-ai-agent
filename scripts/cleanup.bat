@echo off
REM Script cleanup project - Xoa file cu va sap xep lai

echo ========================================
echo  CLEANUP PROJECT
echo ========================================
echo.

echo [BUOC 1] Tao thu muc archive de backup files cu...
if not exist "archive" mkdir archive
echo.

echo [BUOC 2] Di chuyen files cu vao archive...
move app.py archive\ 2>nul
move main.py archive\ 2>nul
move FULLSTACK_SETUP.md archive\ 2>nul
move CHAT_CONFIG_GUIDE.md archive\ 2>nul
move PERFORMANCE_FIXES.md archive\ 2>nul
move OPTIMIZATIONS.md archive\ 2>nul
move frontend\test.html archive\ 2>nul
move frontend\README.md archive\ 2>nul
move src\analytics\charts.py archive\ 2>nul
echo.

echo [BUOC 3] Xoa __pycache__ folders...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"
echo.

echo ========================================
echo  HOAN THANH!
echo ========================================
echo.
echo Files cu da duoc chuyen vao folder "archive"
echo Ban co the xoa folder nay sau khi check lai
echo.

pause
