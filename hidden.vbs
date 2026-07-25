' 배치 파일을 창 없이 실행합니다 (작업 스케줄러 전용 실행기)
Dim rc
rc = CreateObject("WScript.Shell").Run("""" & WScript.Arguments(0) & """", 0, True)
WScript.Quit rc
