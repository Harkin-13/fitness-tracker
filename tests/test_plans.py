from database import get_db


def test_plans_page_loads(client):
    response = client.get(
        "/plans"
    )

    assert response.status_code == 200

    assert (
        b"Select a plan"
        in response.data
    )


def test_first_plan_becomes_active(
    app,
    create_program
):
    program = create_program(
        "PPL"
    )

    assert program is not None
    assert program["is_active"] == 1


def test_duplicate_plan_is_rejected(
    client,
    app,
    create_program
):
    create_program(
        "PPL"
    )

    response = client.post(
        "/program/add",
        data={
            "name": "ppl"
        },
        follow_redirects=True
    )

    assert (
        b"A plan with that name already exists."
        in response.data
    )

    with app.app_context():
        count = get_db().execute(
            """
            SELECT COUNT(*)
            FROM program
            """
        ).fetchone()[0]

    assert count == 1


def test_plan_can_be_made_active(
    client,
    app,
    create_program
):
    first = create_program(
        "PPL"
    )

    second = create_program(
        "Upper Lower"
    )

    client.post(
        (
            f"/program/{second['program_id']}"
            "/set-active"
        )
    )

    with app.app_context():
        db = get_db()

        first_result = db.execute(
            """
            SELECT is_active
            FROM program
            WHERE program_id = ?
            """,
            (first["program_id"],)
        ).fetchone()

        second_result = db.execute(
            """
            SELECT is_active
            FROM program
            WHERE program_id = ?
            """,
            (second["program_id"],)
        ).fetchone()

    assert first_result["is_active"] == 0
    assert second_result["is_active"] == 1


def test_deleting_active_plan_promotes_another(
    client,
    app,
    create_program
):
    first = create_program(
        "PPL"
    )

    second = create_program(
        "Upper Lower"
    )

    client.post(
        (
            f"/program/{first['program_id']}"
            "/delete"
        )
    )

    with app.app_context():
        remaining = get_db().execute(
            """
            SELECT *
            FROM program
            WHERE program_id = ?
            """,
            (second["program_id"],)
        ).fetchone()

    assert remaining is not None
    assert remaining["is_active"] == 1


def test_deleting_plan_preserves_history(
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
            "/delete"
        )
    )

    with app.app_context():
        db = get_db()

        program_result = db.execute(
            """
            SELECT *
            FROM program
            WHERE program_id = ?
            """,
            (program["program_id"],)
        ).fetchone()

        workout_log = db.execute(
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

    assert program_result is None

    assert workout_log is not None

    assert (
        workout_log["workout_id"]
        is None
    )

    assert (
        workout_log["workout_name"]
        == "Push"
    )

    assert set_count == 3