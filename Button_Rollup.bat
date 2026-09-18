@echo off
setlocal
cd /d "%~dp0"
title Buick GMC Rollup
echo Starting Buick/GMC rollup UI...
echo Open http://localhost:8502 in your browser.
echo Keep this window open while using the UI.
echo.
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -m streamlit run Scripts\rollup_ui.py --server.port 8502 --server.headless true
) else (
    python -m streamlit run Scripts\rollup_ui.py --server.port 8502 --server.headless true
)
echo.
echo Streamlit stopped. Exit code: %ERRORLEVEL%
pause
endlocal
