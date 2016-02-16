@echo off

cd "%0\.."
call setup.cmd
set update=%CGRU_LOCATION%\utilities\keeper\update.py

cd "%HOMEPATH%"

start /wait "Update" "%CGRU_PYTHONDIR%\pythonw.exe" "%update%"

setlocal enableDelayedExpansion
for /l %%N in (30 -1 1) do (
  set /a "min=%%N/60, sec=%%N%%60, n-=1"
  if !sec! lss 10 set sec=0!sec!
  cls
  echo Afanasy update completed.
  choice /c cn1 /n /m "Windows will Restart in !min!:!sec! - Press N to restart [N]ow, or C to [C]ancel." /t:1 /d:1
  if not errorlevel 3 goto :break
)
cls
echo Afanasy update completed.
echo Windows will Restart in 0:00 - Press N to restart [N]ow, or C to [C]ancel.
:break
if errorlevel 2 (shutdown /r /t 0) else echo Restart Canceled.