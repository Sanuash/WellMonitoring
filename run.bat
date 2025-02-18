@echo off
cd /d .
call backend\venv\Scripts\activate
uvicorn backend.main:app --reload
pause
