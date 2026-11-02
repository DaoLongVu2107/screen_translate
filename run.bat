@echo off
setlocal
cd /d "%~dp0"

rem Dung chung bo thu vien voi build.bat, chi cai lai khi requirements.txt thay doi.
set "ENV=%LOCALAPPDATA%\ScreenTranslator\env"
set "MARK=%ENV%\installed-run.txt"

if exist "%ENV%\Scripts\python.exe" goto :have_env
echo [*] Tao moi truong Python lan dau, chi lam mot lan...
python -m venv "%ENV%" || goto :err
:have_env
call "%ENV%\Scripts\activate.bat"

fc /b requirements.txt "%MARK%" >nul 2>&1
if not errorlevel 1 goto :run
echo [*] Cai thu vien, chi khi danh sach thu vien thay doi...
python -m pip install --upgrade pip >nul
pip install -r requirements.txt || goto :err
copy /y requirements.txt "%MARK%" >nul

:run
start "" pythonw -m screentrans
goto :eof

:err
echo Loi cai dat. Hay chac chan da cai Python 3.10+ va tick "Add python.exe to PATH".
pause
