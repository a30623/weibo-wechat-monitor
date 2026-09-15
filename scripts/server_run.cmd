@echo off
setlocal
cd /d "%~dp0.."
if not exist logs mkdir logs
runtime\python\python.exe -u main.py 1>>logs\monitor.stdout.log 2>>logs\monitor.stderr.log
exit /b %ERRORLEVEL%
