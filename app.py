import os
import re
import sqlite3
from datetime import datetime
from functools import wraps
from pathlib import Path

from flask import (
    Flask,
    flash,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

APP_DIR = Path(__file__).resolve().parent
DB_PATH = APP_DIR / "data" / "meatheadlifts.db"

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-me-in-production")

WORKOUTS = {
    "A": [
        "Squat",
        "Bench Press",
        "Barbell Row",
    ],
    "B": [
        "Squat",
        "Overhead Press",
        "Deadlift",
    ],
}

DEFAULT_WEIGHTS = {
    "Squat": 45,
    "Bench Press": 45,
    "Barbell Row": 45,
    "Overhead Press": 45,
    "Deadlift": 95,
}

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def get_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS profile (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            next_workout TEXT NOT NULL DEFAULT 'A',
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS exercise_weights (
            exercise_name TEXT PRIMARY KEY,
            weight REAL NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS workout_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            workout_type TEXT NOT NULL,
            started_at TEXT NOT NULL,
            completed_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS session_sets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            exercise_name TEXT NOT NULL,
            set_number INTEGER NOT NULL,
            target_reps INTEGER NOT NULL,
            completed_reps INTEGER NOT NULL,
            weight REAL NOT NULL,
            FOREIGN KEY(session_id) REFERENCES workout_sessions(id)
        );

        CREATE TABLE IF NOT EXISTS session_exercise_notes (
            session_id INTEGER NOT NULL,
            exercise_name TEXT NOT NULL,
            notes TEXT NOT NULL DEFAULT '',
            PRIMARY KEY(session_id, exercise_name),
            FOREIGN KEY(session_id) REFERENCES workout_sessions(id)
        );

        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS permission_groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        );

        CREATE TABLE IF NOT EXISTS user_permission_groups (
            user_id INTEGER NOT NULL,
            group_id INTEGER NOT NULL,
            PRIMARY KEY(user_id, group_id),
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(group_id) REFERENCES permission_groups(id)
        );
        """
    )

    now = datetime.utcnow().isoformat()
    cur.execute(
        "INSERT OR IGNORE INTO profile (id, next_workout, created_at) VALUES (1, 'A', ?)",
        (now,),
    )

    for exercise, weight in DEFAULT_WEIGHTS.items():
        cur.execute(
            """
            INSERT OR IGNORE INTO exercise_weights (exercise_name, weight, updated_at)
            VALUES (?, ?, ?)
            """,
            (exercise, weight, now),
        )

    cur.execute("INSERT OR IGNORE INTO permission_groups (name) VALUES ('admin')")

    user_count = cur.execute("SELECT COUNT(*) AS count FROM users").fetchone()["count"]
    if user_count == 0:
        username = os.environ.get("INITIAL_ADMIN_USERNAME", "admin@meatheadlifts.local")
        password = os.environ.get("INITIAL_ADMIN_PASSWORD", "ChangeMe123")
        password_hash = generate_password_hash(password)
        cur.execute(
            """
            INSERT INTO users (username, password_hash, active, created_at)
            VALUES (?, ?, 1, ?)
            """,
            (username, password_hash, now),
        )
        admin_user_id = cur.lastrowid
        admin_group_id = cur.execute(
            "SELECT id FROM permission_groups WHERE name = 'admin'"
        ).fetchone()["id"]
        cur.execute(
            """
            INSERT OR IGNORE INTO user_permission_groups (user_id, group_id)
            VALUES (?, ?)
            """,
            (admin_user_id, admin_group_id),
        )

    conn.commit()
    conn.close()


def get_user_by_id(conn, user_id):
    if not user_id:
        return None

    row = conn.execute(
        """
        SELECT u.id, u.username, u.active,
               EXISTS(
                 SELECT 1
                 FROM user_permission_groups upg
                 JOIN permission_groups pg ON pg.id = upg.group_id
                 WHERE upg.user_id = u.id AND pg.name = 'admin'
               ) AS is_admin
        FROM users u
        WHERE u.id = ?
        """,
        (user_id,),
    ).fetchone()

    if row is None or not row["active"]:
        return None

    return {
        "id": row["id"],
        "username": row["username"],
        "is_admin": bool(row["is_admin"]),
    }


def get_user_by_username(conn, username):
    normalized = (username or "").strip().lower()
    return conn.execute(
        """
        SELECT id, username, password_hash, active
        FROM users
        WHERE username = ?
        """,
        (normalized,),
    ).fetchone()


def validate_email(email):
    value = (email or "").strip().lower()
    if not value:
        return None, "Email is required"
    if not EMAIL_RE.match(value):
        return None, "Invalid email format"
    return value, None


def validate_password(password):
    value = password or ""
    if len(value) < 8:
        return "Password must be at least 8 characters"
    if not re.search(r"[a-z]", value):
        return "Password must include a lowercase letter"
    if not re.search(r"[A-Z]", value):
        return "Password must include an uppercase letter"
    if not re.search(r"\d", value):
        return "Password must include a number"
    return None


def render_login_page(error=None, next_url=""):
    return render_template(
        "login.html",
        error=error,
        next_url=next_url,
    )


def render_signup_page(error=None, success=None):
    return render_template(
        "signup.html",
        error=error,
        success=success,
    )


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if g.current_user is None:
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)

    return wrapped


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if g.current_user is None:
            return redirect(url_for("login", next=request.path))
        if not g.current_user["is_admin"]:
            return redirect(url_for("index"))
        return view(*args, **kwargs)

    return wrapped


def api_login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if g.current_user is None:
            return jsonify({"error": "Unauthorized"}), 401
        return view(*args, **kwargs)

    return wrapped


def api_admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if g.current_user is None:
            return jsonify({"error": "Unauthorized"}), 401
        if not g.current_user["is_admin"]:
            return jsonify({"error": "Forbidden"}), 403
        return view(*args, **kwargs)

    return wrapped


@app.before_request
def load_current_user():
    conn = get_db()
    g.current_user = get_user_by_id(conn, session.get("user_id"))
    conn.close()


def get_next_workout(conn):
    row = conn.execute("SELECT next_workout FROM profile WHERE id = 1").fetchone()
    return row["next_workout"] if row else "A"


def validate_workout_payload(data):
    workout_type = data.get("workout")
    exercises = data.get("exercises", [])

    if workout_type not in WORKOUTS:
        return None, None, "Invalid workout type"

    expected_exercises = WORKOUTS[workout_type]
    expected = set(expected_exercises)
    received = {ex.get("name") for ex in exercises}
    if expected != received:
        return None, None, "Exercises do not match workout"

    normalized = []
    for name in expected_exercises:
        ex = next((item for item in exercises if item.get("name") == name), None)
        if ex is None:
            return None, None, f"Missing exercise {name}"

        try:
            weight = float(ex.get("weight", 0))
        except (TypeError, ValueError):
            return None, None, f"Invalid weight for {name}"

        reps = ex.get("sets", [])
        if not isinstance(reps, list) or not reps:
            return None, None, f"Invalid sets for {name}"

        expected_set_count = 1 if name == "Deadlift" else 5
        if len(reps) != expected_set_count:
            return None, None, f"Unexpected set count for {name}"

        normalized_reps = []
        for rep_value in reps:
            try:
                rep_num = int(rep_value)
            except (TypeError, ValueError):
                return None, None, f"Invalid rep value for {name}"
            if rep_num < 0 or rep_num > 5:
                return None, None, f"Rep value out of range for {name}"
            normalized_reps.append(rep_num)

        normalized.append(
            {
                "name": name,
                "weight": weight,
                "sets": normalized_reps,
                "notes": str(ex.get("notes", "")).strip(),
            }
        )

    return workout_type, normalized, None


def write_session_sets_and_weights(cur, session_id, exercises, now_iso):
    for ex in exercises:
        name = ex["name"]
        weight = ex["weight"]
        reps = ex["sets"]
        notes = ex.get("notes", "")

        for i, rep_num in enumerate(reps, start=1):
            cur.execute(
                """
                INSERT INTO session_sets
                (session_id, exercise_name, set_number, target_reps, completed_reps, weight)
                VALUES (?, ?, ?, 5, ?, ?)
                """,
                (session_id, name, i, rep_num, weight),
            )

        cur.execute(
            """
            INSERT INTO exercise_weights (exercise_name, weight, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(exercise_name) DO UPDATE SET
                weight=excluded.weight,
                updated_at=excluded.updated_at
            """,
            (name, weight, now_iso),
        )

        cur.execute(
            """
            INSERT INTO session_exercise_notes (session_id, exercise_name, notes)
            VALUES (?, ?, ?)
            ON CONFLICT(session_id, exercise_name) DO UPDATE SET
                notes=excluded.notes
            """,
            (session_id, name, notes),
        )


def recalculate_next_workout(cur):
    latest = cur.execute(
        """
        SELECT workout_type
        FROM workout_sessions
        ORDER BY completed_at DESC, id DESC
        LIMIT 1
        """
    ).fetchone()
    next_workout = "A" if latest is None else ("B" if latest["workout_type"] == "A" else "A")
    cur.execute("UPDATE profile SET next_workout = ? WHERE id = 1", (next_workout,))
    return next_workout


def get_workout_payload(conn):
    workout_type = get_next_workout(conn)
    exercises = WORKOUTS[workout_type]

    weight_rows = conn.execute(
        "SELECT exercise_name, weight FROM exercise_weights"
    ).fetchall()
    weight_map = {row["exercise_name"]: row["weight"] for row in weight_rows}

    payload_exercises = []
    for ex in exercises:
        set_count = 1 if ex == "Deadlift" else 5
        payload_exercises.append(
            {
                "name": ex,
                "weight": weight_map.get(ex, DEFAULT_WEIGHTS[ex]),
                "sets": [5] * set_count,
                "notes": "",
            }
        )

    return {"workout": workout_type, "exercises": payload_exercises}


@app.get("/logo.png")
def logo_from_templates():
    return send_from_directory(APP_DIR / "templates", "logo.png")


@app.route("/")
@login_required
def index():
    return render_template(
        "index.html",
        current_user=g.current_user,
        is_admin=g.current_user["is_admin"],
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    if g.current_user is not None:
        return redirect(url_for("index"))

    error = None
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""

        conn = get_db()
        user = get_user_by_username(conn, email)
        conn.close()

        if user is None or not user["active"] or not check_password_hash(user["password_hash"], password):
            error = "Invalid email or password"
        else:
            session.clear()
            session["user_id"] = user["id"]
            next_url = request.args.get("next") or request.form.get("next") or url_for("index")
            return redirect(next_url)

    return render_login_page(error=error, next_url=request.args.get("next", ""))


@app.get("/signup")
def signup_page():
    if g.current_user is not None:
        return redirect(url_for("index"))
    return render_signup_page()


@app.post("/signup")
def signup():
    if g.current_user is not None:
        return redirect(url_for("index"))

    email, email_err = validate_email(request.form.get("email"))
    password = request.form.get("password") or ""
    confirm_password = request.form.get("confirm_password") or ""
    if email_err:
        return render_signup_page(error=email_err)

    password_err = validate_password(password)
    if password_err:
        return render_signup_page(error=password_err)

    if password != confirm_password:
        return render_signup_page(error="Passwords do not match")

    conn = get_db()
    cur = conn.cursor()
    exists = cur.execute("SELECT id FROM users WHERE username = ?", (email,)).fetchone()
    if exists is not None:
        conn.close()
        return render_signup_page(error="An account with that email already exists")

    now = datetime.utcnow().isoformat()
    cur.execute(
        """
        INSERT INTO users (username, password_hash, active, created_at)
        VALUES (?, ?, 1, ?)
        """,
        (email, generate_password_hash(password), now),
    )
    conn.commit()
    conn.close()
    return render_signup_page(success="Account created. You can now sign in.")


@app.post("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.get("/admin")
@admin_required
def admin_page():
    conn = get_db()
    rows = conn.execute(
        """
        SELECT u.id, u.username, u.active,
               EXISTS(
                 SELECT 1
                 FROM user_permission_groups upg
                 JOIN permission_groups pg ON pg.id = upg.group_id
                 WHERE upg.user_id = u.id AND pg.name = 'admin'
               ) AS is_admin
        FROM users u
        ORDER BY u.username ASC
        """
    ).fetchall()
    conn.close()

    users = [
        {
            "id": row["id"],
            "username": row["username"],
            "active": bool(row["active"]),
            "is_admin": bool(row["is_admin"]),
        }
        for row in rows
    ]

    return render_template("admin.html", users=users, current_user=g.current_user)


@app.post("/admin/users")
@admin_required
def admin_create_user():
    email, email_err = validate_email(request.form.get("email"))
    password = request.form.get("password") or ""
    make_admin = bool(request.form.get("is_admin"))

    if email_err:
        flash(email_err, "error")
        return redirect(url_for("admin_page"))

    password_err = validate_password(password)
    if password_err:
        flash(password_err, "error")
        return redirect(url_for("admin_page"))

    conn = get_db()
    cur = conn.cursor()

    exists = cur.execute("SELECT id FROM users WHERE username = ?", (email,)).fetchone()
    if exists is not None:
        conn.close()
        flash("An account with that email already exists", "error")
        return redirect(url_for("admin_page"))

    now = datetime.utcnow().isoformat()
    cur.execute(
        """
        INSERT INTO users (username, password_hash, active, created_at)
        VALUES (?, ?, 1, ?)
        """,
        (email, generate_password_hash(password), now),
    )
    user_id = cur.lastrowid

    if make_admin:
        group_id = cur.execute(
            "SELECT id FROM permission_groups WHERE name = 'admin'"
        ).fetchone()["id"]
        cur.execute(
            "INSERT OR IGNORE INTO user_permission_groups (user_id, group_id) VALUES (?, ?)",
            (user_id, group_id),
        )

    conn.commit()
    conn.close()
    flash(f"User created: {email}", "success")
    return redirect(url_for("admin_page"))


@app.post("/admin/users/<int:user_id>/password")
@admin_required
def admin_change_user_password(user_id):
    new_password = request.form.get("new_password") or ""
    password_err = validate_password(new_password)
    if password_err:
        return redirect(url_for("admin_page"))

    conn = get_db()
    cur = conn.cursor()
    existing = cur.execute("SELECT id FROM users WHERE id = ?", (user_id,)).fetchone()
    if existing is None:
        conn.close()
        return redirect(url_for("admin_page"))

    cur.execute(
        "UPDATE users SET password_hash = ? WHERE id = ?",
        (generate_password_hash(new_password), user_id),
    )
    conn.commit()
    conn.close()
    return redirect(url_for("admin_page"))


@app.post("/admin/users/<int:user_id>/delete")
@admin_required
def admin_delete_user(user_id):
    if user_id == g.current_user["id"]:
        return redirect(url_for("admin_page"))

    conn = get_db()
    cur = conn.cursor()
    user = cur.execute(
        """
        SELECT u.id,
               EXISTS(
                 SELECT 1
                 FROM user_permission_groups upg
                 JOIN permission_groups pg ON pg.id = upg.group_id
                 WHERE upg.user_id = u.id AND pg.name = 'admin'
               ) AS is_admin
        FROM users u
        WHERE u.id = ?
        """,
        (user_id,),
    ).fetchone()

    if user is None:
        conn.close()
        return redirect(url_for("admin_page"))

    if user["is_admin"]:
        admin_count = cur.execute(
            """
            SELECT COUNT(*) AS count
            FROM users u
            WHERE EXISTS(
              SELECT 1
              FROM user_permission_groups upg
              JOIN permission_groups pg ON pg.id = upg.group_id
              WHERE upg.user_id = u.id AND pg.name = 'admin'
            )
            """
        ).fetchone()["count"]
        if admin_count <= 1:
            conn.close()
            return redirect(url_for("admin_page"))

    cur.execute("DELETE FROM user_permission_groups WHERE user_id = ?", (user_id,))
    cur.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("admin_page"))


@app.get("/api/state")
@api_login_required
def api_state():
    conn = get_db()
    payload = get_workout_payload(conn)
    conn.close()
    return jsonify(payload)


@app.post("/api/complete")
@api_login_required
def api_complete():
    data = request.get_json(silent=True) or {}
    workout_type, exercises, err = validate_workout_payload(data)
    if err:
        return jsonify({"error": err}), 400

    now = datetime.utcnow().isoformat()
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO workout_sessions (workout_type, started_at, completed_at)
        VALUES (?, ?, ?)
        """,
        (workout_type, now, now),
    )
    session_id = cur.lastrowid

    write_session_sets_and_weights(cur, session_id, exercises, now)
    next_workout = recalculate_next_workout(cur)

    conn.commit()
    conn.close()

    return jsonify({"status": "ok", "next_workout": next_workout})


@app.get("/api/history")
@api_login_required
def api_history():
    conn = get_db()
    rows = conn.execute(
        """
        SELECT id, workout_type, completed_at
        FROM workout_sessions
        ORDER BY completed_at DESC
        LIMIT 20
        """
    ).fetchall()

    history = []
    for row in rows:
        history.append(
            {
                "id": row["id"],
                "workout": row["workout_type"],
                "completed_at": row["completed_at"],
            }
        )

    conn.close()
    return jsonify(history)


@app.get("/api/history/<int:session_id>")
@api_login_required
def api_history_session(session_id):
    conn = get_db()

    row = conn.execute(
        """
        SELECT id, workout_type, completed_at
        FROM workout_sessions
        WHERE id = ?
        """,
        (session_id,),
    ).fetchone()

    if row is None:
        conn.close()
        return jsonify({"error": "Workout session not found"}), 404

    set_rows = conn.execute(
        """
        SELECT exercise_name, set_number, completed_reps, weight
        FROM session_sets
        WHERE session_id = ?
        ORDER BY id ASC
        """,
        (session_id,),
    ).fetchall()

    note_rows = conn.execute(
        """
        SELECT exercise_name, notes
        FROM session_exercise_notes
        WHERE session_id = ?
        """,
        (session_id,),
    ).fetchall()

    conn.close()
    notes = {row["exercise_name"]: row["notes"] for row in note_rows}
    return jsonify(
        {
            "id": row["id"],
            "workout": row["workout_type"],
            "completed_at": row["completed_at"],
            "sets": [dict(s) for s in set_rows],
            "notes": notes,
        }
    )


@app.put("/api/history/<int:session_id>")
@api_login_required
def api_update_history_session(session_id):
    data = request.get_json(silent=True) or {}
    workout_type, exercises, err = validate_workout_payload(data)
    if err:
        return jsonify({"error": err}), 400

    now = datetime.utcnow().isoformat()
    conn = get_db()
    cur = conn.cursor()

    existing = cur.execute(
        "SELECT id FROM workout_sessions WHERE id = ?",
        (session_id,),
    ).fetchone()
    if existing is None:
        conn.close()
        return jsonify({"error": "Workout session not found"}), 404

    cur.execute(
        "UPDATE workout_sessions SET workout_type = ? WHERE id = ?",
        (workout_type, session_id),
    )
    cur.execute("DELETE FROM session_sets WHERE session_id = ?", (session_id,))
    cur.execute("DELETE FROM session_exercise_notes WHERE session_id = ?", (session_id,))
    write_session_sets_and_weights(cur, session_id, exercises, now)
    next_workout = recalculate_next_workout(cur)

    conn.commit()
    conn.close()
    return jsonify({"status": "ok", "next_workout": next_workout})


@app.delete("/api/history/<int:session_id>")
@api_login_required
def api_delete_history_session(session_id):
    conn = get_db()
    cur = conn.cursor()

    existing = cur.execute(
        "SELECT id FROM workout_sessions WHERE id = ?",
        (session_id,),
    ).fetchone()
    if existing is None:
        conn.close()
        return jsonify({"error": "Workout session not found"}), 404

    cur.execute("DELETE FROM session_sets WHERE session_id = ?", (session_id,))
    cur.execute("DELETE FROM session_exercise_notes WHERE session_id = ?", (session_id,))
    cur.execute("DELETE FROM workout_sessions WHERE id = ?", (session_id,))
    next_workout = recalculate_next_workout(cur)

    conn.commit()
    conn.close()
    return jsonify({"status": "ok", "next_workout": next_workout})


@app.get("/api/admin/users")
@api_admin_required
def api_admin_users():
    conn = get_db()
    rows = conn.execute(
        """
        SELECT u.id, u.username, u.active,
               EXISTS(
                 SELECT 1
                 FROM user_permission_groups upg
                 JOIN permission_groups pg ON pg.id = upg.group_id
                 WHERE upg.user_id = u.id AND pg.name = 'admin'
               ) AS is_admin
        FROM users u
        ORDER BY u.username ASC
        """
    ).fetchall()
    conn.close()

    return jsonify(
        [
            {
                "id": row["id"],
                "username": row["username"],
                "active": bool(row["active"]),
                "is_admin": bool(row["is_admin"]),
            }
            for row in rows
        ]
    )


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=8000)
