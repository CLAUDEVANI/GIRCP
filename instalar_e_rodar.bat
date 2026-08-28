@echo off
TITLE Instalador e Inicializador - GIRCP Relatorios
COLOR 0B
echo ========================================================
echo   Configurando o ambiente para o GIRCP Relatorios...
echo ========================================================
echo.

REM Verifica se o Python esta instalado
python --version >nul 2>&1
if %errorlevel% neq 0 (
    color 0C
    echo [ERRO] O Python nao foi encontrado no seu computador!
    echo Por favor, instale o Python (versao 3.10 ou 3.11) e marque a opcao "Add Python to PATH".
    pause
    exit /b
)

echo [1/3] Atualizando o gerenciador de pacotes (pip)...
python -m pip install --upgrade pip

echo.
echo [2/3] Instalando as bibliotecas do requirements.txt (Streamlit e WeasyPrint)...
python -m pip install -r requirements.txt

echo.
echo ========================================================
echo   Tudo pronto! Iniciando o aplicativo Streamlit...
echo ========================================================
streamlit run app.py

pause