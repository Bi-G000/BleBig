@echo off
title BleBig - Tạo bộ cài Windows
cd /d "%~dp0"
echo BleBig dang kiem tra va cai cac thanh phan can thiet.
echo Qua trinh nay can Internet va co the mat 10-30 phut.
echo.
if not exist "%~dp0scripts\build_windows.ps1" (
  echo LOI: Khong tim thay scripts\build_windows.ps1
  echo Goi ma nguon co the chua duoc giai nen day du hoac dang la ban cu.
  echo Hay tai lai BleBig v0.2.0 va chon Extract All truoc khi chay.
  pause
  exit /b 2
)
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\build_windows.ps1"
set "BUILD_EXIT=%ERRORLEVEL%"
if not "%BUILD_EXIT%"=="0" (
  echo.
  echo TAO BO CAI THAT BAI. Ma loi: %BUILD_EXIT%
  echo Hay xem thu muc build-logs.
  pause
  exit /b %BUILD_EXIT%
)
if not exist "%~dp0release\BleBig-Setup.exe" (
  echo.
  echo TAO BO CAI THAT BAI: Khong tim thay release\BleBig-Setup.exe
  echo Hay xem thu muc build-logs.
  pause
  exit /b 3
)
echo.
echo HOAN TAT. Dang mo thu muc release...
explorer.exe "%~dp0release"
pause
