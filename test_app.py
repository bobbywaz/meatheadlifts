import pytest
from app import validate_workout_payload

def test_valid_payload_workout_A():
    payload = {
        "workout": "A",
        "exercises": [
            {"name": "Squat", "weight": 45, "sets": [5, 5, 5, 5, 5], "notes": "easy"},
            {"name": "Bench Press", "weight": 45, "sets": [5, 5, 5, 5, 5]},
            {"name": "Barbell Row", "weight": 45, "sets": [5, 5, 5, 5, 5]}
        ]
    }
    workout_type, normalized, err = validate_workout_payload(payload)
    assert workout_type == "A"
    assert err is None
    assert len(normalized) == 3
    assert normalized[0]["name"] == "Squat"

def test_valid_payload_workout_B():
    payload = {
        "workout": "B",
        "exercises": [
            {"name": "Squat", "weight": 45, "sets": [5, 5, 5, 5, 5]},
            {"name": "Overhead Press", "weight": 45, "sets": [5, 5, 5, 5, 5]},
            {"name": "Deadlift", "weight": 95, "sets": [5]}
        ]
    }
    workout_type, normalized, err = validate_workout_payload(payload)
    assert workout_type == "B"
    assert err is None
    assert len(normalized) == 3
    assert normalized[2]["name"] == "Deadlift"
    assert len(normalized[2]["sets"]) == 1

def test_invalid_workout_type():
    payload = {
        "workout": "C",
        "exercises": []
    }
    workout_type, normalized, err = validate_workout_payload(payload)
    assert workout_type is None
    assert err == "Invalid workout type"

def test_missing_workout_type():
    payload = {
        "exercises": []
    }
    workout_type, normalized, err = validate_workout_payload(payload)
    assert workout_type is None
    assert err == "Invalid workout type"

def test_exercises_not_match_workout():
    payload = {
        "workout": "A",
        "exercises": [
            {"name": "Squat", "weight": 45, "sets": [5, 5, 5, 5, 5]},
            {"name": "Bench Press", "weight": 45, "sets": [5, 5, 5, 5, 5]}
        ]
    }
    workout_type, normalized, err = validate_workout_payload(payload)
    assert workout_type is None
    assert err == "Exercises do not match workout"

def test_missing_name_in_exercise():
    payload = {
        "workout": "A",
        "exercises": [
            {"weight": 45, "sets": [5, 5, 5, 5, 5]},
            {"name": "Bench Press", "weight": 45, "sets": [5, 5, 5, 5, 5]},
            {"name": "Barbell Row", "weight": 45, "sets": [5, 5, 5, 5, 5]}
        ]
    }
    workout_type, normalized, err = validate_workout_payload(payload)
    assert workout_type is None
    assert err == "Exercises do not match workout"

def test_invalid_weight():
    payload = {
        "workout": "A",
        "exercises": [
            {"name": "Squat", "weight": "heavy", "sets": [5, 5, 5, 5, 5]},
            {"name": "Bench Press", "weight": 45, "sets": [5, 5, 5, 5, 5]},
            {"name": "Barbell Row", "weight": 45, "sets": [5, 5, 5, 5, 5]}
        ]
    }
    workout_type, normalized, err = validate_workout_payload(payload)
    assert workout_type is None
    assert err == "Invalid weight for Squat"

def test_missing_or_invalid_sets():
    payload = {
        "workout": "A",
        "exercises": [
            {"name": "Squat", "weight": 45, "sets": "5 sets"},
            {"name": "Bench Press", "weight": 45, "sets": [5, 5, 5, 5, 5]},
            {"name": "Barbell Row", "weight": 45, "sets": [5, 5, 5, 5, 5]}
        ]
    }
    workout_type, normalized, err = validate_workout_payload(payload)
    assert workout_type is None
    assert err == "Invalid sets for Squat"

def test_unexpected_set_count():
    payload = {
        "workout": "A",
        "exercises": [
            {"name": "Squat", "weight": 45, "sets": [5, 5, 5, 5]}, # Only 4 sets
            {"name": "Bench Press", "weight": 45, "sets": [5, 5, 5, 5, 5]},
            {"name": "Barbell Row", "weight": 45, "sets": [5, 5, 5, 5, 5]}
        ]
    }
    workout_type, normalized, err = validate_workout_payload(payload)
    assert workout_type is None
    assert err == "Unexpected set count for Squat"

def test_invalid_rep_value():
    payload = {
        "workout": "A",
        "exercises": [
            {"name": "Squat", "weight": 45, "sets": [5, 5, "five", 5, 5]},
            {"name": "Bench Press", "weight": 45, "sets": [5, 5, 5, 5, 5]},
            {"name": "Barbell Row", "weight": 45, "sets": [5, 5, 5, 5, 5]}
        ]
    }
    workout_type, normalized, err = validate_workout_payload(payload)
    assert workout_type is None
    assert err == "Invalid rep value for Squat"

def test_rep_value_out_of_range():
    payload = {
        "workout": "A",
        "exercises": [
            {"name": "Squat", "weight": 45, "sets": [6, 5, 5, 5, 5]},
            {"name": "Bench Press", "weight": 45, "sets": [5, 5, 5, 5, 5]},
            {"name": "Barbell Row", "weight": 45, "sets": [5, 5, 5, 5, 5]}
        ]
    }
    workout_type, normalized, err = validate_workout_payload(payload)
    assert workout_type is None
    assert err == "Rep value out of range for Squat"

def test_invalid_exercises_format():
    payload = {
        "workout": "A",
        "exercises": "not a list"
    }
    workout_type, normalized, err = validate_workout_payload(payload)
    assert workout_type is None
    assert err == "Invalid exercises format"
