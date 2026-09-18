@echo off
cd /d "%~dp0Scripts"
python -m streamlit run rollup_ui.py
pause