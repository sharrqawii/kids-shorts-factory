@echo off
setlocal
cd /d "%~dp0"
if not exist ".studio-venv\Scripts\python.exe" (
  py -3.11 -m venv .studio-venv
  if errorlevel 1 goto failed
  .studio-venv\Scripts\python.exe -m pip install -r requirements-studio.txt
  if errorlevel 1 goto failed
)
if exist "sample\pip-and-the-giant-strawberry.mp4" set "PIP_SAMPLE=%CD%\sample\pip-and-the-giant-strawberry.mp4"
if not defined BLENDER_PYTHON if exist ".venv\Scripts\python.exe" set "BLENDER_PYTHON=%CD%\.venv\Scripts\python.exe"
echo Open http://127.0.0.1:8765 in your browser. Keep this window open.
.studio-venv\Scripts\python.exe -m studio.server
goto :eof
:failed
echo Setup failed. See docs/STUDIO.md. No paid service was used.
pause
