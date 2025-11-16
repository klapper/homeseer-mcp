@echo off
REM Test runner script for HomeSeer MCP Server (Windows Batch)
REM Run this script to execute all unit tests

echo ========================================
echo HomeSeer MCP Server - Test Runner
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo WARNING: Virtual environment not found!
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Could not activate virtual environment
    exit /b 1
)

REM Check if pytest is installed
python -c "import pytest" 2>nul
if errorlevel 1 (
    echo Installing test dependencies...
    pip install -r requirements.txt
)

echo.
echo Running tests...
echo ========================================
echo.

REM Run pytest with options
python -m pytest tests/ --verbose --color=yes --tb=short %*

set TEST_EXIT_CODE=%ERRORLEVEL%

echo.
echo ========================================
if %TEST_EXIT_CODE% equ 0 (
    echo All tests passed!
) else (
    echo Some tests failed (exit code: %TEST_EXIT_CODE%^)
)
echo ========================================

exit /b %TEST_EXIT_CODE%
