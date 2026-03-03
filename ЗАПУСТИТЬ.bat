@echo off
chcp 65001 >nul
title Маркетинговый агент

echo.
echo  Запускаю платформу...
echo.

cd /d "%~dp0"

:: Устанавливаем зависимости
pip install fastapi uvicorn python-dotenv -q 2>nul

:: Запускаем сервер
start /b python -m uvicorn web.app:app --host 127.0.0.1 --port 8000 2>server.log

:: Ждём старта
timeout /t 3 /nobreak >nul

:: Открываем браузер
start http://localhost:8000

echo  Платформа открыта: http://localhost:8000
echo.
echo  Нажмите любую клавишу чтобы ОСТАНОВИТЬ сервер...
pause >nul

:: Останавливаем по порту
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000') do taskkill /F /PID %%a >nul 2>&1
echo  Готово.
