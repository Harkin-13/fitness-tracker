from database import get_db


def test_workout_can_be_created(
    app,
    create_program,
    create_workout
):
    program = create_program(
        "PPL"
    )

    workout = create_workout(
        program["program_id"],
        "Push"
    )

    assert workout is not None
    assert workout["name"] == "Push"


def test_duplicate_workout_is_rejected(
    client,
    app,
    create_program,
    create_workout
):
    program = create_program(
        "PPL"
    )

    create_workout(
        program["program_id"],
        "Push"
    )

    response = client.post(
        (
            f"/program/{program['program_id']}"
            "/workout/add"
        ),
        data={
            "name": "push"
        },
        follow_redirects=True
    )

    assert (
        b"already exists"
        in response.data
    )

    with app.app_context():
        count = get_db().execute(
            """
            SELECT COUNT(*)
            FROM workout
            WHERE program_id = ?
            """,
            (program["program_id"],)
        ).fetchone()[0]

    assert count == 1


def test_exercise_assignment_has_default_targets(
    workout_setup
):
    assignment = workout_setup[
        "assignment"
    ]

    assert assignment is not None

    assert (
        assignment["target_sets"]
        == 3
    )

    assert (
        assignment["target_reps"]
        == 10
    )


def test_exercise_targets_can_be_updated(
    client,
    app,
    workout_setup
):
    program = workout_setup[
        "program"
    ]

    workout = workout_setup[
        "workout"
    ]

    assignment = workout_setup[
        "assignment"
    ]

    client.post(
        (
            f"/program/{program['program_id']}"
            f"/workout/{workout['workout_id']}"
            f"/exercise/"
            f"{assignment['workout_exercise_id']}"
            "/update"
        ),
        data={
            "target_sets": "2",
            "target_reps": "8"
        }
    )

    with app.app_context():
        updated = get_db().execute(
            """
            SELECT *
            FROM workout_exercise
            WHERE workout_exercise_id = ?
            """,
            (
                assignment[
                    "workout_exercise_id"
                ],
            )
        ).fetchone()

    assert updated["target_sets"] == 2
    assert updated["target_reps"] == 8


def test_completed_workout_saves_history(
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
        workout_date="2026-09-05"
    )

    with app.app_context():
        db = get_db()

        log = db.execute(
            """
            SELECT *
            FROM workout_log
            WHERE workout_id = ?
            """,
            (workout["workout_id"],)
        ).fetchone()

        sets = db.execute(
            """
            SELECT *
            FROM exercise_set
            WHERE log_id = ?
            ORDER BY set_number
            """,
            (log["log_id"],)
        ).fetchall()

    assert log is not None

    assert (
        log["log_date"]
        == "2026-09-05"
    )

    assert (
        log["workout_name"]
        == "Push"
    )

    assert len(sets) == 3

    assert sets[0]["weight"] == 30
    assert sets[0]["reps"] == 8

    assert sets[2]["reps"] == 7


def test_future_workout_date_is_rejected(
    client,
    app,
    workout_setup
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

    response = client.post(
        (
            f"/program/{program['program_id']}"
            f"/workout/{workout['workout_id']}"
            "/finish"
        ),
        data={
            "workout_date": "2099-01-01",

            f"weight_{exercise['exercise_id']}_1": "30",
            f"reps_{exercise['exercise_id']}_1": "8",

            f"weight_{exercise['exercise_id']}_2": "30",
            f"reps_{exercise['exercise_id']}_2": "8",

            f"weight_{exercise['exercise_id']}_3": "30",
            f"reps_{exercise['exercise_id']}_3": "8"
        }
    )

    assert (
        b"Workout date cannot be in the future."
        in response.data
    )

    with app.app_context():
        count = get_db().execute(
            """
            SELECT COUNT(*)
            FROM workout_log
            """
        ).fetchone()[0]

    assert count == 0


def test_missing_reps_does_not_create_partial_history(
    client,
    app,
    workout_setup
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

    response = client.post(
        (
            f"/program/{program['program_id']}"
            f"/workout/{workout['workout_id']}"
            "/finish"
        ),
        data={
            "workout_date": "2026-09-01",

            f"weight_{exercise['exercise_id']}_1": "30",
            f"reps_{exercise['exercise_id']}_1": "8",

            f"weight_{exercise['exercise_id']}_2": "30",
            f"reps_{exercise['exercise_id']}_2": "",

            f"weight_{exercise['exercise_id']}_3": "30",
            f"reps_{exercise['exercise_id']}_3": "8"
        }
    )

    assert (
        b"Enter the repetitions completed"
        in response.data
    )

    with app.app_context():
        db = get_db()

        log_count = db.execute(
            """
            SELECT COUNT(*)
            FROM workout_log
            """
        ).fetchone()[0]

        set_count = db.execute(
            """
            SELECT COUNT(*)
            FROM exercise_set
            """
        ).fetchone()[0]

    assert log_count == 0
    assert set_count == 0


def test_negative_weight_is_rejected(
    client,
    app,
    workout_setup
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

    response = client.post(
        (
            f"/program/{program['program_id']}"
            f"/workout/{workout['workout_id']}"
            "/finish"
        ),
        data={
            "workout_date": "2026-09-01",

            f"weight_{exercise['exercise_id']}_1": "-5",
            f"reps_{exercise['exercise_id']}_1": "8",

            f"weight_{exercise['exercise_id']}_2": "30",
            f"reps_{exercise['exercise_id']}_2": "8",

            f"weight_{exercise['exercise_id']}_3": "30",
            f"reps_{exercise['exercise_id']}_3": "8"
        }
    )

    assert (
        b"Weight must be between 0 and 1000 kilograms."
        in response.data
    )

    with app.app_context():
        count = get_db().execute(
            """
            SELECT COUNT(*)
            FROM workout_log
            """
        ).fetchone()[0]

    assert count == 0


def test_deleting_workout_preserves_history(
    client,
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
        exercise["exercise_id"]
    )

    client.post(
        (
            f"/program/{program['program_id']}"
            f"/workout/{workout['workout_id']}"
            "/delete"
        )
    )

    with app.app_context():
        db = get_db()

        workout_result = db.execute(
            """
            SELECT *
            FROM workout
            WHERE workout_id = ?
            """,
            (workout["workout_id"],)
        ).fetchone()

        log = db.execute(
            """
            SELECT *
            FROM workout_log
            LIMIT 1
            """
        ).fetchone()

        set_count = db.execute(
            """
            SELECT COUNT(*)
            FROM exercise_set
            """
        ).fetchone()[0]

    assert workout_result is None

    assert log is not None

    assert log["workout_id"] is None

    assert (
        log["workout_name"]
        == "Push"
    )

    assert set_count == 3