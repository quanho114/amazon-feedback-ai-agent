@echo off
REM Script push code len GitHub

echo ========================================
echo  Push Code to GitHub
echo ========================================
echo.

REM Check git status
echo [1/5] Checking git status...
git status
echo.

REM Add all files
echo [2/5] Adding files to git...
git add .
echo.

REM Commit
echo [3/5] Creating commit...
set /p commit_msg="Nhap commit message (Enter = 'Update code'): "
if "%commit_msg%"=="" set commit_msg=Update code

git commit -m "%commit_msg%"
echo.

REM Push to GitHub
echo [4/5] Pushing to GitHub...
git push origin Quan
echo.

echo [5/5] Done!
echo.
echo ========================================
echo  Code da duoc push len GitHub!
echo  Repository: github.com/quanho114/amazon-feedback-ai-agent
echo  Branch: Quan
echo ========================================
echo.

pause
