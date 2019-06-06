cd %CD%
powershell -command ".\run.bat | Tee-Object -file .\Out\QaLog.txt"
