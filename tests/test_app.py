import sqlite3
import pytest
from datetime import datetime
from app import write_session_sets_and_weights

def test_write_session_sets_and_weights_valid():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.executescript(
        """
        CREATE TABLE workout_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            workout_type TEXT NOT NULL,
            started_at TEXT NOT NULL,
            completed_at TEXT NOT NULL
        );

        CREATE TABLE session_sets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            exercise_name TEXT NOT NULL,
            set_number INTEGER NOT NULL,
            target_reps INTEGER NOT NULL,
            completed_reps INTEGER NOT NULL,
            weight REAL NOT NULL,
            FOREIGN KEY(session_id) REFERENCES workout_sessions(id)
        );

        CREATE TABLE exercise_weights (
            exercise_name TEXT PRIMARY KEY,
            weight REAL NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE session_exercise_notes (
            session_id INTEGER NOT NULL,
            exercise_name TEXT NOT NULL,
            notes TEXT NOT NULL DEFAULT '',
            PRIMARY KEY(session_id, exercise_name),
            FOREIGN KEY(session_id) REFERENCES workout_sessions(id)
        );
        """
    )

    cur.execute(
        "INSERT INTO workout_sessions (workout_type, started_at, completed_at) VALUES (?, ?, ?)",
        ('A', '2023-01-01T12:00:00', '2023-01-01T13:00:00')
    )
    session_id = cur.lastrowid

    exercises = [
        {
            "name": "Squat",
            "weight": 200,
            "sets": [5, 5, 5, 5, 5],
            "notes": "Felt good"
        },
        {
            "name": "Bench Press",
            "weight": 150,
            "sets": [5, 5, 5, 4, 3]
            # No notes provided intentionally
        }
    ]

    now_iso = datetime.utcnow().isoformat()
    write_session_sets_and_weights(cur, session_id, exercises, now_iso)

    # Verify session_sets
    sets = cur.execute("SELECT * FROM session_sets WHERE session_id=?", (session_id,)).fetchall()
    assert len(sets) == 10

    squats = [s for s in sets if s["exercise_name"] == "Squat"]
    assert len(squats) == 5
    for s in squats:
        assert s["completed_reps"] == 5
        assert s["weight"] == 200

    benches = [s for s in sets if s["exercise_name"] == "Bench Press"]
    assert len(benches) == 5
    for i, reps in enumerate([5, 5, 5, 4, 3]):
        assert benches[i]["completed_reps"] == reps
        assert benches[i]["weight"] == 150

    # Verify exercise_weights
    weights = cur.execute("SELECT * FROM exercise_weights").fetchall()
    assert len(weights) == 2
    weight_dict = {w["exercise_name"]: w["weight"] for w in weights}
    assert weight_dict["Squat"] == 200
    assert weight_dict["Bench Press"] == 150

    # Verify notes
    notes = cur.execute("SELECT * FROM session_exercise_notes WHERE session_id=?", (session_id,)).fetchall()
    assert len(notes) == 2
    notes_dict = {n["exercise_name"]: n["notes"] for n in notes}
    assert notes_dict["Squat"] == "Felt good"
    assert notes_dict["Bench Press"] == ""

    conn.close()

def test_write_session_sets_and_weights_update_notes():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.executescript(
        """
        CREATE TABLE workout_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            workout_type TEXT NOT NULL,
            started_at TEXT NOT NULL,
            completed_at TEXT NOT NULL
        );

        CREATE TABLE session_sets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            exercise_name TEXT NOT NULL,
            set_number INTEGER NOT NULL,
            target_reps INTEGER NOT NULL,
            completed_reps INTEGER NOT NULL,
            weight REAL NOT NULL,
            FOREIGN KEY(session_id) REFERENCES workout_sessions(id)
        );

        CREATE TABLE exercise_weights (
            exercise_name TEXT PRIMARY KEY,
            weight REAL NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE session_exercise_notes (
            session_id INTEGER NOT NULL,
            exercise_name TEXT NOT NULL,
            notes TEXT NOT NULL DEFAULT '',
            PRIMARY KEY(session_id, exercise_name),
            FOREIGN KEY(session_id) REFERENCES workout_sessions(id)
        );
        """
    )

    cur.execute(
        "INSERT INTO workout_sessions (workout_type, started_at, completed_at) VALUES (?, ?, ?)",
        ('A', '2023-01-01T12:00:00', '2023-01-01T13:00:00')
    )
    session_id = cur.lastrowid

    cur.execute(
        "INSERT INTO session_exercise_notes (session_id, exercise_name, notes) VALUES (?, ?, ?)",
        (session_id, "Squat", "Old notes")
    )

    exercises = [
        {
            "name": "Squat",
            "weight": 205,
            "sets": [5, 5, 5, 5, 5],
            "notes": "New notes"
        }
    ]

    now_iso = "2023-01-01T12:00:00"
    write_session_sets_and_weights(cur, session_id, exercises, now_iso)

    notes = cur.execute("SELECT * FROM session_exercise_notes WHERE session_id=?", (session_id,)).fetchall()
    assert len(notes) == 1
    assert notes[0]["exercise_name"] == "Squat"
    assert notes[0]["notes"] == "New notes"

    conn.close()

def test_write_session_sets_and_weights_update_weights():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.executescript(
        """
        CREATE TABLE workout_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            workout_type TEXT NOT NULL,
            started_at TEXT NOT NULL,
            completed_at TEXT NOT NULL
        );

        CREATE TABLE session_sets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            exercise_name TEXT NOT NULL,
            set_number INTEGER NOT NULL,
            target_reps INTEGER NOT NULL,
            completed_reps INTEGER NOT NULL,
            weight REAL NOT NULL,
            FOREIGN KEY(session_id) REFERENCES workout_sessions(id)
        );

        CREATE TABLE exercise_weights (
            exercise_name TEXT PRIMARY KEY,
            weight REAL NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE session_exercise_notes (
            session_id INTEGER NOT NULL,
            exercise_name TEXT NOT NULL,
            notes TEXT NOT NULL DEFAULT '',
            PRIMARY KEY(session_id, exercise_name),
            FOREIGN KEY(session_id) REFERENCES workout_sessions(id)
        );
        """
    )

    cur.execute(
        "INSERT INTO workout_sessions (workout_type, started_at, completed_at) VALUES (?, ?, ?)",
        ('A', '2023-01-01T12:00:00', '2023-01-01T13:00:00')
    )
    session_id = cur.lastrowid

    cur.execute(
        "INSERT INTO exercise_weights (exercise_name, weight, updated_at) VALUES (?, ?, ?)",
        ("Squat", 200, "2023-01-01T11:00:00")
    )

    exercises = [
        {
            "name": "Squat",
            "weight": 205,
            "sets": [5, 5, 5, 5, 5]
        }
    ]

    now_iso = "2023-01-01T12:00:00"
    write_session_sets_and_weights(cur, session_id, exercises, now_iso)

    weights = cur.execute("SELECT * FROM exercise_weights WHERE exercise_name=?", ("Squat",)).fetchall()
    assert len(weights) == 1
    assert weights[0]["weight"] == 205
    assert weights[0]["updated_at"] == "2023-01-01T12:00:00"

    conn.close()
