@echo off
REM 매일 6편 자동 공개 업로드 (작업 스케줄러가 호출)
cd /d "D:\.CODE\AXdata\axdata_13_auto_upload"
set PYTHONIOENCODING=utf-8
REM -u : 출력 버퍼링 끔. 중간에 강제 종료돼도 어디까지 올렸는지 로그에 남습니다.
"C:\Users\gimsf\AppData\Local\Programs\Python\Python314\python.exe" -u upload_batch.py 3 >> "D:\.CODE\AXdata\axdata_13_auto_upload\upload_log.txt" 2>&1
echo [%date% %time%] exit=%errorlevel% >> "D:\.CODE\AXdata\axdata_13_auto_upload\upload_log.txt"
