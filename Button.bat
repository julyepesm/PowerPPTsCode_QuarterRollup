@echo off
cd /d "%~dp0Scripts"
python -m streamlit run app_ui.py
pause
