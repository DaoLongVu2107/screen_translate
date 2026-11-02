@echo off
setlocal
cd /d "%~dp0"

rem Thu vien nam trong .venv cua thu muc code, chi cai lai khi requirements.txt thay doi.
set "ENV=%~dp0.venv"
set "MARK=%ENV%\installed-build.txt"

if exist "%ENV%\Scripts\python.exe" goto :have_env
echo [*] Tao moi truong Python lan dau, chi lam mot lan...
python -m venv "%ENV%" || goto :err_python
:have_env
call "%ENV%\Scripts\activate.bat"

fc /b requirements.txt "%MARK%" >nul 2>&1
if not errorlevel 1 goto :deps_ok
echo [*] Cai thu vien, chi khi danh sach thu vien thay doi...
python -m pip install --upgrade pip >nul
pip install -r requirements.txt pyinstaller || goto :err
copy /y requirements.txt "%MARK%" >nul
goto :build
:deps_ok
echo [*] Thu vien da co san, bo qua buoc cai dat.

:build
echo [*] Dang build exe...
pyinstaller --noconfirm --onefile --windowed --name ScreenTranslator ^
    --collect-all winocr --collect-all winrt --collect-data sv_ttk ^
    --hidden-import pystray._win32 ^
    "%~dp0screentrans\__main__.py" || goto :err
echo.
echo Xong! File exe nam o dist\ScreenTranslator.exe
pause
goto :eof

:err_python
echo Khong tao duoc moi truong Python. Hay cai Python 3.10+ va tick "Add python.exe to PATH".
pause
goto :eof

:err
echo Build that bai. Neu loi do thu vien, xoa thu muc .venv roi chay lai.
pause
