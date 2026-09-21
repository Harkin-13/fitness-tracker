from database import get_db


def test_exercise_can_be_created(
    create_exercise
):
    exercise = create_exercise(
        "Lateral Raise",
        "Side Delts",
        "Cable"
    )

    assert exercise is not None

    assert (
        exercise["primary_muscle"]
        == "Side Delts"
    )

    assert (
        exercise["equipment"]
        == "Cable"
    )


def test_duplicate_exercise_is_rejected(
    client,
    app,
    create_exercise
):
    create_exercise(
        "Bench Press",
        "Chest",
        "Barbell"
    )

    response = client.post(
        "/exercise/add",
        data={
            "name": "bench press",
            "primary_muscle": "Chest",
            "equipment": "Barbell"
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
            FROM exercise
            """
        ).fetchone()[0]

    assert count == 1


def test_same_name_with_different_equipment_is_allowed(
    app,
    create_exercise
):
    create_exercise(
        "Chest Press",
        "Chest",
        "Machine"
    )

    create_exercise(
        "Chest Press",
        "Chest",
        "Dumbbell"
    )

    with app.app_context():
        count = get_db().execute(
            """
            SELECT COUNT(*)
            FROM exercise
            WHERE name = ?
            """,
            ("Chest Press",)
        ).fetchone()[0]

    assert count == 2


def test_exercise_can_be_edited(
    client,
    app,
    create_exercise
):
    exercise = create_exercise(
        "Cable Curl",
        "Biceps",
        "Cable"
    )

    client.post(
        (
            f"/exercise/"
            f"{exercise['exercise_id']}"
            "/edit"
        ),
        data={
            "name": "Cable Bicep Curl",
            "primary_muscle": "Biceps",
            "equipment": "Cable"
        }
    )

    with app.app_context():
        updated = get_db().execute(
            """
            SELECT *
            FROM exercise
            WHERE exercise_id = ?
            """,
            (exercise["exercise_id"],)
        ).fetchone()

    assert (
        updated["name"]
        == "Cable Bicep Curl"
    )


def test_deleting_exercise_removes_assignments_and_history(
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
            f"/exercise/"
            f"{exercise['exercise_id']}"
            "/delete"
        )
    )

    with app.app_context():
        db = get_db()

        exercise_result = db.execute(
            """
            SELECT *
            FROM exercise
            WHERE exercise_id = ?
            """,
            (exercise["exercise_id"],)
        ).fetchone()

        assignment_count = db.execute(
            """
            SELECT COUNT(*)
            FROM workout_exercise
            WHERE exercise_id = ?
            """,
            (exercise["exercise_id"],)
        ).fetchone()[0]

        history_count = db.execute(
            """
            SELECT COUNT(*)
            FROM exercise_set
            WHERE exercise_id = ?
            """,
            (exercise["exercise_id"],)
        ).fetchone()[0]

    assert exercise_result is None
    assert assignment_count == 0
    assert history_count == 0