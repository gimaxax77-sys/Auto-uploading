@echo off
REM 매일 6편 자동 공개 업로드 (작업 스케줄러가 호출)
cd /d "D:\.CODE\AXdata\axdata_13"
set PYTHONIOENCODING=utf-8
"C:\Users\gimsf\AppData\Local\Programs\Python\Python314\python.exe" upload_batch.py 12 >> "D:\.CODE\AXdata\axdata_13\upload_log.txt" 2>&1
echo [%date% %time%] exit=%errorlevel% >> "D:\.CODE\AXdata\axdata_13\upload_log.txt"
