rem Set CGRU ad_update root:
SET CGRU_UPDATE_LOCATION=%CD%

rem Get CGRU update server for the first time update:
For /F "Tokens=*" %%I in ('type update_server_name.txt') Do Set CGRU_UPDATESERVER=%%I
echo CGRU_UPDATESERVER %CGRU_UPDATESERVER%

pushd ..

rem Set CGRU root:
SET CGRU_LOCATION=%CD%

rem Get CGRU version:
For /F "Tokens=*" %%I in ('type version.txt') Do Set CGRU_VERSION=%%I
echo CGRU_VERSION %CGRU_VERSION%

popd

rem Python module path:
SET CGRU_PYTHON=%CGRU_LOCATION%\lib\python

if defined PYTHONPATH (
   SET PYTHONPATH=%CGRU_PYTHON%;%PYTHONPATH%
) else (
   SET PYTHONPATH=%CGRU_PYTHON%
)

set CGRU_PYTHONDIR=%CGRU_LOCATION%\python

rem copy config.json to CGRU root for the first time update
XCOPY "%CGRU_UPDATE_LOCATION%\config.json" "%CGRU_LOCATION%" /y

rem copy cgruupdate.py to python lib for the first time update
XCOPY "%CGRU_UPDATE_LOCATION%\cgruupdate.py" "%CGRU_PYTHON%" /y

rem copy cgruupdate.py to keeper for the first time update
XCOPY "%CGRU_UPDATE_LOCATION%\update.py" "%CGRU_LOCATION%\utilities\keeper" /y

set update=%CGRU_LOCATION%\utilities\keeper\update.py
rem set CGRU_UPDATE_CMD="%CGRU_PYTHONDIR%\pythonw.exe" "%update%"
start "Keeper" "%CGRU_PYTHONDIR%\pythonw.exe" "%update%"