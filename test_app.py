import sqlite3
import pytest
from app import recalculate_next_workout

@pytest.fixture
def db_cursor():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS profile (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            next_workout TEXT NOT NULL DEFAULT 'A',
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS workout_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            workout_type TEXT NOT NULL,
            started_at TEXT NOT NULL,
            completed_at TEXT NOT NULL
        );
        """
    )

    cur.execute(
        "INSERT INTO profile (id, next_workout, created_at) VALUES (1, 'A', '2025-01-01T00:00:00')"
    )
    conn.commit()

    yield cur
    conn.close()

def test_recalculate_next_workout_no_sessions(db_cursor):
    next_workout = recalculate_next_workout(db_cursor)
    assert next_workout == "A"

    profile = db_cursor.execute("SELECT next_workout FROM profile WHERE id = 1").fetchone()
    assert profile["next_workout"] == "A"

def test_recalculate_next_workout_latest_a(db_cursor):
    db_cursor.execute(
        """
        INSERT INTO workout_sessions (workout_type, started_at, completed_at)
        VALUES ('A', '2025-01-01T10:00:00', '2025-01-01T11:00:00')
        """
    )

    next_workout = recalculate_next_workout(db_cursor)
    assert next_workout == "B"

    profile = db_cursor.execute("SELECT next_workout FROM profile WHERE id = 1").fetchone()
    assert profile["next_workout"] == "B"

def test_recalculate_next_workout_latest_b(db_cursor):
    db_cursor.execute(
        """
        INSERT INTO workout_sessions (workout_type, started_at, completed_at)
        VALUES ('B', '2025-01-01T10:00:00', '2025-01-01T11:00:00')
        """
    )

    next_workout = recalculate_next_workout(db_cursor)
    assert next_workout == "A"

    profile = db_cursor.execute("SELECT next_workout FROM profile WHERE id = 1").fetchone()
    assert profile["next_workout"] == "A"

def test_recalculate_next_workout_multiple_sessions(db_cursor):
    db_cursor.execute(
        """
        INSERT INTO workout_sessions (workout_type, started_at, completed_at)
        VALUES ('B', '2025-01-01T10:00:00', '2025-01-01T11:00:00')
        """
    )
    db_cursor.execute(
        """
        INSERT INTO workout_sessions (workout_type, started_at, completed_at)
        VALUES ('A', '2025-01-02T10:00:00', '2025-01-02T11:00:00')
        """
    )
    db_cursor.execute(
        """
        INSERT INTO workout_sessions (workout_type, started_at, completed_at)
        VALUES ('B', '2025-01-03T10:00:00', '2025-01-03T11:00:00')
        """
    )

    next_workout = recalculate_next_workout(db_cursor)
    assert next_workout == "A"

    profile = db_cursor.execute("SELECT next_workout FROM profile WHERE id = 1").fetchone()
    assert profile["next_workout"] == "A"

    db_cursor.execute(
        """
        INSERT INTO workout_sessions (workout_type, started_at, completed_at)
        VALUES ('A', '2025-01-04T10:00:00', '2025-01-04T11:00:00')
        """
    )

    next_workout = recalculate_next_workout(db_cursor)
    assert next_workout == "B"

    profile = db_cursor.execute("SELECT next_workout FROM profile WHERE id = 1").fetchone()
    assert profile["next_workout"] == "B"
