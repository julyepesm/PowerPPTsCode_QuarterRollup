@echo off
start "Buick GMC Rollup" /D "%~dp0Scripts" python -m streamlit run rollup_ui.py --server.port 8502