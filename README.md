# CampusFix

CampusFix is a Python + Flask campus issue tracking app that lets users report and monitor campus issues with status updates, dashboards, filters, and admin backup tools.

## Features
- Report campus issues
- View and filter issues by status
- Update issue status (Open, In Progress, Resolved)
- Dashboard with issue statistics
- Admin backup export and import for the SQLite database
- Tri-tone color scheme for UI

## Run Locally
1. Create and activate virtual environment:
   - Windows PowerShell:
     ```powershell
     python -m venv .venv
     .\.venv\Scripts\Activate.ps1
     ```
2. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
3. Start the server:
   ```powershell
   python app.py
   ```
4. Open in browser:
   `http://127.0.0.1:5000`

## Portable Windows App
1. Install dependencies in `.venv`:
   ```powershell
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   ```
2. Build the portable executable:
   ```powershell
   .\build_desktop_app.ps1
   ```
3. The script creates `CampusFix.exe` in `portable-release\CampusFix Portable`.
4. Copy that folder to another Windows laptop and run `CampusFix.exe`.

The packaged app stores its database in `.campusfix-data` next to the executable so it remains self-contained and portable. The build script also copies the current `campusfix.db` into the portable folder, so existing records move with the app.
