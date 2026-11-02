@echo off
cd /d "%~dp0"
if not exist .venv (
    python -m venv .venv
)
call .venv\Scripts\activate.bat
pip install -r requirements.txt pyinstaller || goto :err
pyinstaller --noconfirm --onefile --windowed --name ScreenTranslator ^
    --collect-all winocr --collect-all winrt --collect-data sv_ttk ^
    --hidden-import pystray._win32 ^
    screentrans\__main__.py || goto :err
echo.
echo Xong! File exe nam o dist\ScreenTranslator.exe
pause
goto :eof
:err
echo Build that bai.
pause
