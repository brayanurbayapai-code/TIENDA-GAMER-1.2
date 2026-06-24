@echo off
chcp 65001 >nul
title Tienda Gemer Profesional
cd /d "%~dp0"

echo ==================================================
echo       TIENDA GEMER PROFESIONAL - INICIO LOCAL
echo ==================================================
echo.

where python >nul 2>nul
if %errorlevel%==0 (
    set "PYTHON_CMD=python"
) else (
    where py >nul 2>nul
    if %errorlevel%==0 (
        set "PYTHON_CMD=py -3"
    ) else (
        echo ERROR: No se encontro Python instalado.
        echo Descarga Python desde python.org y marca Add Python to PATH.
        pause
        exit /b 1
    )
)

echo Verificando dependencias...
%PYTHON_CMD% -c "import flask" >nul 2>nul
if errorlevel 1 (
    echo Instalando Flask y dependencias. Esto solo tarda la primera vez...
    %PYTHON_CMD% -m pip install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo ERROR: No se pudieron instalar las dependencias.
        pause
        exit /b 1
    )
)

echo.
echo Iniciando la tienda en http://127.0.0.1:5000
echo No cierres esta ventana mientras uses la pagina.
echo Para detener el servidor, presiona CTRL+C.
echo.
%PYTHON_CMD% app.py

echo.
echo El servidor se detuvo.
pause
