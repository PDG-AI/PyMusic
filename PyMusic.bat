@echo off
REM --- Ruta al venv ---
set VENV_PATH=.\venv

REM --- Activar entorno virtual ---
call "%VENV_PATH%\Scripts\activate.bat"

REM --- Ejecutar script ---
python "D:\PyMusic\PyMusic"

REM --- Mantener ventana abierta ---
pause
