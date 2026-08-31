@echo off
REM 밤 11시 업로드가 제대로 끝났는지 점검 (작업 스케줄러가 23:10에 호출)
cd /d "D:\.CODE\AXdata\axdata_13_auto_upload"
set PYTHONIOENCODING=utf-8
"%LOCALAPPDATA%\Programs\Python\Launcher\py.exe" -u check_upload.py >> "D:\.CODE\AXdata\axdata_13_auto_upload\upload_log.txt" 2>&1
echo [%date% %time%] check exit=%errorlevel% >> "D:\.CODE\AXdata\axdata_13_auto_upload\upload_log.txt"
