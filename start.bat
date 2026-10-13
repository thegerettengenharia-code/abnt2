@echo off
setlocal
cd /d "%~dp0"

echo ============================================
echo   Formatador ABNT - iniciando o site
echo ============================================
echo.

where python >nul 2>nul
if errorlevel 1 (
  echo [ERRO] Python nao foi encontrado. Instale em https://www.python.org/downloads/
  echo        e marque a opcao "Add Python to PATH".
  pause
  exit /b 1
)

if not exist ".venv" (
  echo Criando ambiente e instalando dependencias (primeira vez)...
  python -m venv .venv
  call ".venv\Scripts\activate.bat"
  python -m pip install --upgrade pip >nul
  python -m pip install -r requirements.txt
  if errorlevel 1 (
    echo [ERRO] Falha ao instalar as dependencias.
    pause
    exit /b 1
  )
) else (
  call ".venv\Scripts\activate.bat"
)

if not exist ".env.local" (
  where vercel >nul 2>nul
  if not errorlevel 1 (
    echo Baixando as variaveis de ambiente (token do Vercel Blob)...
    call vercel env pull .env.local
  ) else (
    echo [AVISO] Arquivo .env.local nao encontrado e o Vercel CLI nao esta instalado.
    echo         O envio de arquivos pode falhar. Rode:
    echo           vercel link --project abnt-formatador
    echo           vercel env pull .env.local
  )
)

echo.
echo Abrindo o navegador em http://localhost:8000
echo Para encerrar, feche esta janela ou pressione Ctrl+C.
echo.

start "" "http://localhost:8000"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

pause
