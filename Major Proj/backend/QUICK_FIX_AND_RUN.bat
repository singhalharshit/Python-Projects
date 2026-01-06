@echo off
echo ========================================
echo   QUICK FIX - Adding Missing Function
echo ========================================
echo.

cd "E:\Coding Practice\Python Projects\Python-Projects\Major Proj\backend"

echo Step 1: Adding missing getter function...
python add_getter_function.py
echo.

echo Step 2: Installing requirements...
pip install instaloader --quiet
echo.

echo Step 3: Starting backend...
echo.
python run_backend.py

pause
