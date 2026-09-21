from database import get_db
from progress import build_progress_sessions


def test_graphs_page_handles_no_history(
    client
):
    response = client.get(
        "/graphs"
    )

    assert response.status_code == 200

    assert (
        b"No workout history yet"
        in response.data
    )


def test_only_exercises_with_history_are_tracked(
    client,
    app,
    workout_setup,
    create_exercise,
    complete_workout
):
    program = workout_setup[
        "program"
    ]

    workout = workout_setup[
        "workout"
    ]

    tracked_exercise = workout_setup[
        "exercise"
    ]

    untracked_exercise = create_exercise(
        "Lateral Raise",
        "Side Delts",
        "Cable"
    )

    complete_workout(
        program["program_id"],
        workout["workout_id"],
        tracked_exercise["exercise_id"]
    )

    response = client.get(
        "/graphs"
    )

    assert (
        tracked_exercise["name"].encode()
        in response.data
    )

    assert (
        untracked_exercise["name"].encode()
        not in response.data
    )


def test_weighted_progress_metrics_are_calculated(
    app,
    workout_setup,
    complete_workout
):
    program = workout_setup[
        "program"
    ]

    workout = workout_setup[
        "workout"
    ]

    exercise = workout_setup[
        "exercise"
    ]

    complete_workout(
        program["program_id"],
        workout["workout_id"],
        exercise["exercise_id"],
        weights=[
            "20",
            "20",
            "15"
        ],
        reps=[
            "8",
            "7",
            "10"
        ]
    )

    with app.app_context():
        sessions = build_progress_sessions(
            exercise["exercise_id"]
        )

    assert len(sessions) == 1

    session = sessions[0]

    assert session["best_weight"] == 20

    assert session["best_reps"] == 10

    assert session["volume"] == 450

    assert (
        session["best_set_weight"]
        == 20
    )

    assert (
        session["best_set_reps"]
        == 8
    )


def test_bodyweight_progress_uses_repetitions(
    app,
    create_program,
    create_exercise,
    create_workout,
    assign_exercise,
    complete_workout
):
    program = create_program(
        "Bodyweight"
    )

    exercise = create_exercise(
        "Push Up",
        "Chest",
        "Bodyweight"
    )

    workout = create_workout(
        program["program_id"],
        "Bodyweight Workout"
    )

    assign_exercise(
        program["program_id"],
        workout["workout_id"],
        exercise["exercise_id"]
    )

    complete_workout(
        program["program_id"],
        workout["workout_id"],
        exercise["exercise_id"],
        weights=[
            "",
            "",
            ""
        ],
        reps=[
            "10",
            "12",
            "15"
        ]
    )

    with app.app_context():
        sessions = build_progress_sessions(
            exercise["exercise_id"]
        )

    session = sessions[0]

    assert (
        session["best_weight"]
        is None
    )

    assert session["volume"] is None

    assert session["best_reps"] == 15

    assert (
        session["best_set_weight"]
        is None
    )

    assert (
        session["best_set_reps"]
        == 15
    )


def test_progress_sessions_are_ordered_by_date(
    app,
    workout_setup,
    complete_workout
):
    program = workout_setup[
        "program"
    ]

    workout = workout_setup[
        "workout"
    ]

    exercise = workout_setup[
        "exercise"
    ]

    complete_workout(
        program["program_id"],
        workout["workout_id"],
        exercise["exercise_id"],
        workout_date="2026-09-03",
        weights=[
            "30",
            "30",
            "30"
        ]
    )

    complete_workout(
        program["program_id"],
        workout["workout_id"],
        exercise["exercise_id"],
        workout_date="2026-09-01",
        weights=[
            "20",
            "20",
            "20"
        ]
    )

    complete_workout(
        program["program_id"],
        workout["workout_id"],
        exercise["exercise_id"],
        workout_date="2026-09-02",
        weights=[
            "25",
            "25",
            "25"
        ]
    )

    with app.app_context():
        sessions = build_progress_sessions(
            exercise["exercise_id"]
        )

    dates = [
        session["log_date"]
        for session in sessions
    ]

    assert dates == [
        "2026-09-01",
        "2026-09-02",
        "2026-09-03"
    ]