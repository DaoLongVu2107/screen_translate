@echo off
cd /d "%~dp0"
if not exist .venv (
    echo [*] Tao moi truong Python...
    python -m venv .venv || goto :err
    call .venv\Scripts\activate.bat
    python -m pip install --upgrade pip
    pip install -r requirements.txt || goto :err
) else (
    call .venv\Scripts\activate.bat
)
pythonw -m screentrans
goto :eof
:err
echo Loi cai dat. Hay chac chan da cai Python 3.10+ va tick "Add to PATH".
pause
