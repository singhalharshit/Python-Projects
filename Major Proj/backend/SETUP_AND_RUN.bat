@echo off
echo ========================================
echo   COMPLETE SETUP AND FIX
echo ========================================
echo.

cd "E:\Coding Practice\Python Projects\Python-Projects\Major Proj\backend"

echo Step 1: Installing Instagram scraper...
pip install instaloader
echo.

echo Step 2: Seeding database with real creators...
python seed_creators.py
echo.

echo Step 3: Starting backend...
echo Press Ctrl+C to stop the backend when you're done testing
echo.
python run_backend.py

pause
