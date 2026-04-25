from functools import wraps
import os
import sys
import tempfile
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory, send_file, jsonify
import sqlite3
from pathlib import Path
from werkzeug.security import check_password_hash, generate_password_hash

PROJECT_DIR = Path(__file__).resolve().parent
RESOURCE_DIR = Path(getattr(sys, "_MEIPASS", PROJECT_DIR))
APP_DIR = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else PROJECT_DIR
DEFAULT_DATA_DIR = Path(os.environ.get("LOCALAPPDATA", PROJECT_DIR)) / "CampusFix"
PORTABLE_DATA_DIR = APP_DIR / ".campusfix-data"
HOSTED_DATA_ROOT = os.environ.get("CAMPUSFIX_DATA_DIR") or os.environ.get("RENDER_DISK_PATH") or os.environ.get("RENDER_DISK_MOUNT_PATH")


def can_write_to_dir(candidate_dir: Path) -> bool:
    try:
        candidate_dir.mkdir(parents=True, exist_ok=True)
        probe_path = candidate_dir / ".campusfix-write-test"
        file_descriptor = os.open(str(probe_path), os.O_WRONLY | os.O_CREAT | os.O_TRUNC)
        os.close(file_descriptor)
        probe_path.unlink(missing_ok=True)
        return True
    except OSError:
        return False


def resolve_data_dir() -> Path:
    if HOSTED_DATA_ROOT:
        hosted_dir = Path(HOSTED_DATA_ROOT) / "CampusFix"
        if can_write_to_dir(hosted_dir):
            return hosted_dir

    preferred_dir = PORTABLE_DATA_DIR if getattr(sys, "frozen", False) else DEFAULT_DATA_DIR
    for candidate_dir in (preferred_dir, PORTABLE_DATA_DIR, PROJECT_DIR / ".campusfix-data"):
        if can_write_to_dir(candidate_dir):
            return candidate_dir

    fallback_dir = Path(tempfile.gettempdir()) / "CampusFix"
    fallback_dir.mkdir(parents=True, exist_ok=True)
    return fallback_dir


DATA_DIR = resolve_data_dir()
DB_PATH = DATA_DIR / "campusfix.db"

app = Flask(
    __name__,
    template_folder=str(RESOURCE_DIR / "templates"),
    static_folder=str(RESOURCE_DIR / "static"),
)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "campusfix-dev-key")
app.config["DATABASE"] = DB_PATH


def get_database_path() -> Path:
    return Path(app.config["DATABASE"])


def json_error(message: str, status_code: int):
    response = jsonify({"error": message})
    response.status_code = status_code
    return response

DEMO_ISSUES = [
    (
        "Broken classroom projector",
        "Classroom",
        "Engineering Block A - Room 204",
        "Projector flickers and shuts off after 5 minutes of use.",
        "Open",
    ),
    (
        "Leaking water cooler",
        "Water",
        "Library 1st Floor",
        "Water cooler is leaking near the power socket.",
        "In Progress",
    ),
    (
        "Damaged footpath tiles",
        "Infrastructure",
        "Main Quad Pathway",
        "Several tiles are cracked and uneven, causing trip risk.",
        "Open",
    ),
    (
        "Wi-Fi dead zone",
        "Internet",
        "Hostel C - 3rd Floor",
        "No Wi-Fi signal in corridor and nearby rooms.",
        "Resolved",
    ),
    (
        "Library AC not cooling",
        "Electrical",
        "Central Library - Reading Hall",
        "Air conditioning is running but not cooling effectively.",
        "In Progress",
    ),
    (
        "Flickering corridor lights",
        "Electrical",
        "Science Block - Ground Floor",
        "Lights flicker continuously after 6 PM.",
        "Open",
    ),
    (
        "Washroom door lock broken",
        "Sanitation",
        "Admin Block - 2nd Floor Washroom",
        "Door lock is jammed and cannot be secured.",
        "Resolved",
    ),
    (
        "Overflowing dustbins",
        "Cleanliness",
        "Cafeteria Entrance",
        "Bins are not cleared regularly during lunch hours.",
        "Open",
    ),
    (
        "Basketball court net torn",
        "Sports",
        "Sports Complex - Court 2",
        "Net is torn and rim is slightly bent.",
        "In Progress",
    ),
    (
        "Parking area streetlight off",
        "Safety",
        "Student Parking Lot B",
        "Streetlight near the exit gate remains off at night.",
        "Open",
    ),
]


def get_db_connection():
    db_path = get_database_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def is_valid_backup(candidate_path: Path) -> bool:
    if not candidate_path.is_file():
        return False

    conn = None
    try:
        conn = sqlite3.connect(candidate_path)
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
    except sqlite3.Error:
        return False
    finally:
        if conn is not None:
            conn.close()

    return {"users", "issues"}.issubset(tables)


def init_db():
    conn = get_db_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('admin', 'student')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS issues (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            location TEXT NOT NULL,
            description TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Open',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    existing_count = conn.execute("SELECT COUNT(*) AS count FROM issues").fetchone()["count"]
    if existing_count == 0:
        conn.executemany(
            """
            INSERT INTO issues (title, category, location, description, status)
            VALUES (?, ?, ?, ?, ?)
            """,
            DEMO_ISSUES,
        )

    conn.commit()
    conn.close()


def current_user():
    username = session.get("username")
    role = session.get("role")
    if not username or not role:
        return None
    return {
        "username": username,
        "role": role,
        "label": session.get("label", username.title()),
    }


def login_required(view_func):
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        if not current_user():
            flash("Please log in to continue.", "error")
            return redirect(url_for("login"))
        return view_func(*args, **kwargs)

    return wrapped_view


def role_required(required_role):
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(*args, **kwargs):
            user = current_user()
            if not user:
                flash("Please log in to continue.", "error")
                return redirect(url_for("login"))
            if user["role"] != required_role:
                flash("You do not have permission to access that page.", "error")
                return redirect(url_for("index"))
            return view_func(*args, **kwargs)

        return wrapped_view

    return decorator


@app.context_processor
def inject_user():
    return {"current_user": current_user()}


@app.after_request
def add_cache_headers(response):
    if not request.path.startswith("/static/"):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response


def get_user_by_username(username):
    conn = get_db_connection()
    user = conn.execute(
        "SELECT username, password_hash, role FROM users WHERE username = ?",
        (username,),
    ).fetchone()
    conn.close()
    return user


def create_user(username, password, role):
    conn = get_db_connection()
    try:
        conn.execute(
            """
            INSERT INTO users (username, password_hash, role)
            VALUES (?, ?, ?)
            """,
            (username, generate_password_hash(password), role),
        )
        conn.commit()
    finally:
        conn.close()


def validate_issue_fields(title, category, location, description):
    cleaned = {
        "title": (title or "").strip(),
        "category": (category or "").strip(),
        "location": (location or "").strip(),
        "description": (description or "").strip(),
    }
    if not all(cleaned.values()):
        return None
    return cleaned


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "").strip()
        account = get_user_by_username(username)

        if not account or not check_password_hash(account["password_hash"], password):
            flash("Invalid username or password.", "error")
            return render_template("login.html")

        session["username"] = account["username"]
        session["role"] = account["role"]
        session["label"] = account["username"].title()
        flash(f"Logged in as {account['role'].title()}.", "success")
        return redirect(url_for("index"))

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "").strip()
        confirm_password = request.form.get("confirm_password", "").strip()
        role = request.form.get("role", "").strip().lower()

        if not username or not password or not confirm_password or role not in {"admin", "student"}:
            flash("Please fill in all fields.", "error")
            return render_template("register.html")

        if len(username) < 3:
            flash("Username must be at least 3 characters long.", "error")
            return render_template("register.html")

        if len(password) < 6:
            flash("Password must be at least 6 characters long.", "error")
            return render_template("register.html")

        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return render_template("register.html")

        if get_user_by_username(username):
            flash("That username is already taken.", "error")
            return render_template("register.html")

        try:
            create_user(username, password, role)
        except sqlite3.IntegrityError:
            flash("That username is already taken.", "error")
            return render_template("register.html")

        flash("Account created successfully. Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.post("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))


@app.get("/admin")
@role_required("admin")
def admin_redirect():
    return redirect(url_for("issues"))


@app.get("/user")
@role_required("student")
def user_redirect():
    return redirect(url_for("report_issue"))


@app.route("/")
@login_required
def index():
    conn = get_db_connection()
    stats = conn.execute(
        """
        SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN status = 'Open' THEN 1 ELSE 0 END) AS open_count,
            SUM(CASE WHEN status = 'In Progress' THEN 1 ELSE 0 END) AS progress_count,
            SUM(CASE WHEN status = 'Resolved' THEN 1 ELSE 0 END) AS resolved_count
        FROM issues
        """
    ).fetchone()

    recent = conn.execute(
        """
        SELECT id, title, category, location, status, created_at
        FROM issues
        ORDER BY datetime(created_at) DESC
        LIMIT 5
        """
    ).fetchall()
    conn.close()

    safe_stats = {
        "total": stats["total"] or 0,
        "open_count": stats["open_count"] or 0,
        "progress_count": stats["progress_count"] or 0,
        "resolved_count": stats["resolved_count"] or 0,
    }
    return render_template("index.html", stats=safe_stats, recent=recent)


@app.route("/report", methods=["GET", "POST"])
@role_required("student")
def report_issue():
    if request.method == "POST":
        issue_data = validate_issue_fields(
            request.form.get("title"),
            request.form.get("category"),
            request.form.get("location"),
            request.form.get("description"),
        )
        if not issue_data:
            flash("Please fill in all fields.", "error")
            return render_template("report.html")

        conn = get_db_connection()
        conn.execute(
            """
            INSERT INTO issues (title, category, location, description)
            VALUES (?, ?, ?, ?)
            """,
            (
                issue_data["title"],
                issue_data["category"],
                issue_data["location"],
                issue_data["description"],
            ),
        )
        conn.commit()
        conn.close()
        flash("Issue submitted successfully.", "success")
        return redirect(url_for("issues"))

    return render_template("report.html")


@app.route("/issues")
@login_required
def issues():
    status_filter = request.args.get("status", "All")

    conn = get_db_connection()
    if status_filter in {"Open", "In Progress", "Resolved"}:
        issue_rows = conn.execute(
            """
            SELECT *
            FROM issues
            WHERE status = ?
            ORDER BY datetime(created_at) DESC
            """,
            (status_filter,),
        ).fetchall()
    else:
        issue_rows = conn.execute(
            """
            SELECT *
            FROM issues
            ORDER BY datetime(created_at) DESC
            """
        ).fetchall()
    conn.close()

    return render_template("issues.html", issues=issue_rows, active_filter=status_filter)


@app.post("/issues/<int:issue_id>/status")
@role_required("admin")
def update_status(issue_id):
    new_status = request.form.get("status", "").strip()
    if new_status not in {"Open", "In Progress", "Resolved"}:
        flash("Invalid status selected.", "error")
        return redirect(url_for("issues"))

    conn = get_db_connection()
    conn.execute("UPDATE issues SET status = ? WHERE id = ?", (new_status, issue_id))
    conn.commit()
    conn.close()

    flash("Issue status updated.", "success")
    return redirect(url_for("issues"))


@app.get("/api/issues")
def api_list_issues():
    if not current_user():
        return json_error("Please log in to continue.", 401)

    status_filter = request.args.get("status", "All")
    conn = get_db_connection()
    query = """
        SELECT id, title, category, location, description, status, created_at
        FROM issues
    """
    params = ()
    if status_filter in {"Open", "In Progress", "Resolved"}:
        query += " WHERE status = ?"
        params = (status_filter,)
    query += " ORDER BY datetime(created_at) DESC, id DESC"
    issue_rows = conn.execute(query, params).fetchall()
    conn.close()

    return jsonify([dict(issue) for issue in issue_rows])


@app.post("/api/issues")
def api_create_issue():
    user = current_user()
    if not user:
        return json_error("Please log in to continue.", 401)
    if user["role"] != "student":
        return json_error("Only student accounts can submit issues.", 403)

    payload = request.get_json(silent=True) or request.form
    issue_data = validate_issue_fields(
        payload.get("title"),
        payload.get("category"),
        payload.get("location"),
        payload.get("description"),
    )
    if not issue_data:
        return json_error("Please fill in all fields.", 400)

    conn = get_db_connection()
    cursor = conn.execute(
        """
        INSERT INTO issues (title, category, location, description)
        VALUES (?, ?, ?, ?)
        """,
        (
            issue_data["title"],
            issue_data["category"],
            issue_data["location"],
            issue_data["description"],
        ),
    )
    conn.commit()
    issue_id = cursor.lastrowid
    issue = conn.execute(
        """
        SELECT id, title, category, location, description, status, created_at
        FROM issues
        WHERE id = ?
        """,
        (issue_id,),
    ).fetchone()
    conn.close()

    response = jsonify(dict(issue))
    response.status_code = 201
    return response


@app.patch("/api/issues/<int:issue_id>/status")
def api_update_status(issue_id):
    user = current_user()
    if not user:
        return json_error("Please log in to continue.", 401)
    if user["role"] != "admin":
        return json_error("Only admin accounts can update issue status.", 403)

    payload = request.get_json(silent=True) or request.form
    new_status = (payload.get("status") or "").strip()
    if new_status not in {"Open", "In Progress", "Resolved"}:
        return json_error("Invalid status selected.", 400)

    conn = get_db_connection()
    cursor = conn.execute("UPDATE issues SET status = ? WHERE id = ?", (new_status, issue_id))
    conn.commit()
    if cursor.rowcount == 0:
        conn.close()
        return json_error("Issue not found.", 404)

    issue = conn.execute(
        """
        SELECT id, title, category, location, description, status, created_at
        FROM issues
        WHERE id = ?
        """,
        (issue_id,),
    ).fetchone()
    conn.close()

    return jsonify(dict(issue))


@app.get("/backup/export")
@role_required("admin")
def export_backup():
    init_db()
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    db_path = get_database_path()
    return send_file(
        db_path,
        as_attachment=True,
        download_name=f"campusfix-backup-{timestamp}.db",
        mimetype="application/octet-stream",
    )


@app.post("/backup/import")
@role_required("admin")
def import_backup():
    upload = request.files.get("backup_file")
    if not upload or not upload.filename:
        flash("Choose a backup file to import.", "error")
        return redirect(url_for("index"))

    temp_path = None
    try:
        suffix = Path(upload.filename).suffix or ".db"
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, dir=DATA_DIR) as temp_file:
            upload.save(temp_file)
            temp_path = Path(temp_file.name)

        if not is_valid_backup(temp_path):
            flash("The selected file is not a valid CampusFix backup.", "error")
            return redirect(url_for("index"))

        db_path = get_database_path()
        db_path.parent.mkdir(parents=True, exist_ok=True)
        os.replace(temp_path, db_path)
        temp_path = None
        flash("Backup imported successfully.", "success")
    except OSError:
        flash("Backup import failed while replacing the database file.", "error")
    finally:
        if temp_path and temp_path.exists():
            temp_path.unlink(missing_ok=True)

    return redirect(url_for("index"))


@app.get("/manifest.webmanifest")
def web_manifest():
    return send_from_directory(app.static_folder, "manifest.webmanifest")


@app.get("/service-worker.js")
def service_worker():
    response = send_from_directory(app.static_folder, "service-worker.js")
    response.headers["Service-Worker-Allowed"] = "/"
    response.headers["Cache-Control"] = "no-cache"
    return response


def main():
    init_db()
    host = os.environ.get("CAMPUSFIX_HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", os.environ.get("CAMPUSFIX_PORT", "5000")))
    app.run(host=host, port=port, debug=False, use_reloader=False)


if __name__ == "__main__":
    main()
