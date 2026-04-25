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

## GitHub Hosting
This repository now includes a GitHub Pages site in `docs/` and an automated workflow in `.github/workflows/pages.yml`.

- GitHub Pages can host the project website and documentation
- GitHub Pages cannot run the full Flask + SQLite app backend
- To publish the static site, push this repo to GitHub and enable Pages with the source set to `GitHub Actions`

Once enabled, the project website will deploy from the `main` branch workflow. For the full live app, use a Python-capable host such as Render, Railway, or PythonAnywhere.

## Deploy The Flask App
This repo is now prepared for Render deployment with:

- `wsgi.py` for a production WSGI entrypoint
- `gunicorn` in `requirements.txt`
- `render.yaml` for one-click infrastructure setup
- environment-based `SECRET_KEY`, `PORT`, and persistent database storage

### Render
1. Push the latest code to GitHub.
2. In Render, create a new Blueprint instance from this repository.
3. Render will read `render.yaml` and create the web service plus a persistent disk.
4. After the first deploy finishes, open the generated Render URL.

The SQLite database will be stored on the mounted disk at `/var/data/CampusFix/campusfix.db`, so your app data persists across restarts.

Render note: persistent disks currently require a paid web service. If you switch this service to Render's free tier, the app can still run, but the local SQLite database will be ephemeral and may be lost on restart or redeploy.
