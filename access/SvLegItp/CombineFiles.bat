@echo off
set Dest_Folder=%1
set Dest_File=%2
set /a MaxFileCnt=%3

if exist %Dest_File% del %Dest_File%

copy /y /b %Dest_Folder%\MemDump_0.txt %Dest_File% 1>NUL
for /l %%F in (1, 1, %MaxFileCnt%) do (
  copy /y /b %Dest_File%+%Dest_Folder%\MemDump_%%F.txt %Dest_File% 1>NUL
	del %Dest_Folder%\MemDump_%%F.txt 1>NUL
)
del %Dest_Folder%\*.inc 1>NUL
del %Dest_Folder%\*.txt 1>NUL
