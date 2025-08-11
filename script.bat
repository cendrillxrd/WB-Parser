@echo off
chcp 65001 > nul
C:\Users\Admin\AppData\Local\Programs\Python\Python313\python.exe C:\Users\Admin\PycharmProjects\test_zadanie\main.py
if %errorlevel% neq 0 (
    echo Ошибка выполнения скрипта! Код: %errorlevel%
    pause
    exit /b %errorlevel%
)
echo Скрипт выполнен успешно.
timeout /t 5 >nul
exit