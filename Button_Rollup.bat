@echo off
setlocal
cd /d "%~dp0Scripts"
title Buick GMC Rollup
echo Starting Buick/GMC rollup UI...
echo Open http://localhost:8502 in your browser.
echo Keep this window open while using the UI.
echo.
python -m streamlit run rollup_ui.py --server.port 8502 --server.headless true
echo.
echo Streamlit stopped. Exit code: %ERRORLEVEL%
pause
endlocal