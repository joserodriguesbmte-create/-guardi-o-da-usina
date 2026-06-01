@echo off
title Guardiao da Usina
echo.
echo  Iniciando Guardiao da Usina - Sistema de Testes Eletricos...
echo.
cd /d "%~dp0"
python -m streamlit run app.py --server.port 8501 --browser.gatherUsageStats false
pause
