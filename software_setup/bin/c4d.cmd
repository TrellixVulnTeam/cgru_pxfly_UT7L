@echo off

call %CGRU_LOCATION%\software_setup\setup_c4d.cmd

start "C4D" "%APP_DIR%\CINEMA 4D.exe" %*