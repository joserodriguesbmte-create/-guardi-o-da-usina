Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "cmd /c cd /d C:\Users\joser\guardiao-da-usina && py -3.12 -m streamlit run app.py --server.port 8501 --browser.gatherUsageStats false", 0, False
