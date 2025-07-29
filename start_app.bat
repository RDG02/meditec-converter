@echo off
echo Starting Routemeister Converter Tool...
echo.
echo The application will open in your browser at: http://localhost:8501
echo.
echo Press Ctrl+C to stop the application
echo.
py -m streamlit run simple_app.py --server.port 8501 --server.headless true
pause 