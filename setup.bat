@echo off
REM ICFES Dashboard - Setup Script
echo Creating virtual environment...
python -m venv .venv

REM activating
call .venv\Scripts\activate

REM Installing dependencies
echo Installing dependencies...
pip install -r requirements.txt

echo.
echo Setup complete! Run the app with:
echo   streamlit run app.py --server.port 3000
echo.
pause