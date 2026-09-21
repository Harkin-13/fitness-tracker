from database import get_db


def test_workout_can_move_right(
    client,
    app,
    create_program,
    create_workout
):
    program = create_program(
        "PPL"
    )

    push = create_workout(
        program["program_id"],
        "Push"
    )

    create_workout(
        program["program_id"],
        "Pull"
    )

    create_workout(
        program["program_id"],
        "Legs"
    )

    response = client.post(
        (
            f"/program/{program['program_id']}"
            f"/workout/{push['workout_id']}"
            "/move-right"
        )
    )

    assert response.status_code == 302

    with app.app_context():
        workouts = get_db().execute(
            """
            SELECT name, workout_order
            FROM workout
            WHERE program_id = ?
            ORDER BY workout_order
            """,
            (program["program_id"],)
        ).fetchall()

    assert [
        workout["name"]
        for workout in workouts
    ] == [
        "Pull",
        "Push",
        "Legs"
    ]

    assert [
        workout["workout_order"]
        for workout in workouts
    ] == [
        1,
        2,
        3
    ]


def test_workout_can_move_left(
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

    create_workout(
        program["program_id"],
        "Pull"
    )

    legs = create_workout(
        program["program_id"],
        "Legs"
    )

    response = client.post(
        (
            f"/program/{program['program_id']}"
            f"/workout/{legs['workout_id']}"
            "/move-left"
        )
    )

    assert response.status_code == 302

    with app.app_context():
        workouts = get_db().execute(
            """
            SELECT name, workout_order
            FROM workout
            WHERE program_id = ?
            ORDER BY workout_order
            """,
            (program["program_id"],)
        ).fetchall()

    assert [
        workout["name"]
        for workout in workouts
    ] == [
        "Push",
        "Legs",
        "Pull"
    ]

    assert [
        workout["workout_order"]
        for workout in workouts
    ] == [
        1,
        2,
        3
    ]


def test_first_workout_cannot_move_left(
    client,
    app,
    create_program,
    create_workout
):
    program = create_program(
        "PPL"
    )

    push = create_workout(
        program["program_id"],
        "Push"
    )

    create_workout(
        program["program_id"],
        "Pull"
    )

    response = client.post(
        (
            f"/program/{program['program_id']}"
            f"/workout/{push['workout_id']}"
            "/move-left"
        )
    )

    assert response.status_code == 302

    with app.app_context():
        workouts = get_db().execute(
            """
            SELECT name, workout_order
            FROM workout
            WHERE program_id = ?
            ORDER BY workout_order
            """,
            (program["program_id"],)
        ).fetchall()

    assert [
        workout["name"]
        for workout in workouts
    ] == [
        "Push",
        "Pull"
    ]

    assert [
        workout["workout_order"]
        for workout in workouts
    ] == [
        1,
        2
    ]


def test_exercise_can_move_down(
    client,
    app,
    create_program,
    create_exercise,
    create_workout,
    assign_exercise
):
    program = create_program(
        "PPL"
    )

    workout = create_workout(
        program["program_id"],
        "Push"
    )

    bench_press = create_exercise(
        "Bench Press",
        "Chest",
        "Barbell"
    )

    shoulder_press = create_exercise(
        "Shoulder Press",
        "Front Delts",
        "Dumbbell"
    )

    tricep_pushdown = create_exercise(
        "Tricep Pushdown",
        "Triceps",
        "Cable"
    )

    bench_assignment = assign_exercise(
        program["program_id"],
        workout["workout_id"],
        bench_press["exercise_id"]
    )

    assign_exercise(
        program["program_id"],
        workout["workout_id"],
        shoulder_press["exercise_id"]
    )

    assign_exercise(
        program["program_id"],
        workout["workout_id"],
        tricep_pushdown["exercise_id"]
    )

    response = client.post(
        (
            f"/program/{program['program_id']}"
            f"/workout/{workout['workout_id']}"
            "/exercise/"
            f"{bench_assignment['workout_exercise_id']}"
            "/move-down"
        )
    )

    assert response.status_code == 302

    with app.app_context():
        exercises = get_db().execute(
            """
            SELECT
                exercise.name,
                workout_exercise.exercise_order
            FROM workout_exercise
            JOIN exercise
                ON workout_exercise.exercise_id
                = exercise.exercise_id
            WHERE workout_exercise.workout_id = ?
            ORDER BY
                workout_exercise.exercise_order
            """,
            (workout["workout_id"],)
        ).fetchall()

    assert [
        exercise["name"]
        for exercise in exercises
    ] == [
        "Shoulder Press",
        "Bench Press",
        "Tricep Pushdown"
    ]

    assert [
        exercise["exercise_order"]
        for exercise in exercises
    ] == [
        1,
        2,
        3
    ]


def test_exercise_can_move_up(
    client,
    app,
    create_program,
    create_exercise,
    create_workout,
    assign_exercise
):
    program = create_program(
        "PPL"
    )

    workout = create_workout(
        program["program_id"],
        "Push"
    )

    bench_press = create_exercise(
        "Bench Press",
        "Chest",
        "Barbell"
    )

    shoulder_press = create_exercise(
        "Shoulder Press",
        "Front Delts",
        "Dumbbell"
    )

    tricep_pushdown = create_exercise(
        "Tricep Pushdown",
        "Triceps",
        "Cable"
    )

    assign_exercise(
        program["program_id"],
        workout["workout_id"],
        bench_press["exercise_id"]
    )

    assign_exercise(
        program["program_id"],
        workout["workout_id"],
        shoulder_press["exercise_id"]
    )

    tricep_assignment = assign_exercise(
        program["program_id"],
        workout["workout_id"],
        tricep_pushdown["exercise_id"]
    )

    response = client.post(
        (
            f"/program/{program['program_id']}"
            f"/workout/{workout['workout_id']}"
            "/exercise/"
            f"{tricep_assignment['workout_exercise_id']}"
            "/move-up"
        )
    )

    assert response.status_code == 302

    with app.app_context():
        exercises = get_db().execute(
            """
            SELECT
                exercise.name,
                workout_exercise.exercise_order
            FROM workout_exercise
            JOIN exercise
                ON workout_exercise.exercise_id
                = exercise.exercise_id
            WHERE workout_exercise.workout_id = ?
            ORDER BY
                workout_exercise.exercise_order
            """,
            (workout["workout_id"],)
        ).fetchall()

    assert [
        exercise["name"]
        for exercise in exercises
    ] == [
        "Bench Press",
        "Tricep Pushdown",
        "Shoulder Press"
    ]

    assert [
        exercise["exercise_order"]
        for exercise in exercises
    ] == [
        1,
        2,
        3
    ]


def test_last_exercise_cannot_move_down(
    client,
    app,
    create_program,
    create_exercise,
    create_workout,
    assign_exercise
):
    program = create_program(
        "PPL"
    )

    workout = create_workout(
        program["program_id"],
        "Push"
    )

    bench_press = create_exercise(
        "Bench Press",
        "Chest",
        "Barbell"
    )

    shoulder_press = create_exercise(
        "Shoulder Press",
        "Front Delts",
        "Dumbbell"
    )

    bench_assignment = assign_exercise(
        program["program_id"],
        workout["workout_id"],
        bench_press["exercise_id"]
    )

    shoulder_assignment = assign_exercise(
        program["program_id"],
        workout["workout_id"],
        shoulder_press["exercise_id"]
    )

    assert (
        bench_assignment["exercise_order"]
        == 1
    )

    assert (
        shoulder_assignment["exercise_order"]
        == 2
    )

    response = client.post(
        (
            f"/program/{program['program_id']}"
            f"/workout/{workout['workout_id']}"
            "/exercise/"
            f"{shoulder_assignment['workout_exercise_id']}"
            "/move-down"
        )
    )

    assert response.status_code == 302

    with app.app_context():
        exercises = get_db().execute(
            """
            SELECT
                exercise.name,
                workout_exercise.exercise_order
            FROM workout_exercise
            JOIN exercise
                ON workout_exercise.exercise_id
                = exercise.exercise_id
            WHERE workout_exercise.workout_id = ?
            ORDER BY
                workout_exercise.exercise_order
            """,
            (workout["workout_id"],)
        ).fetchall()

    assert [
        exercise["name"]
        for exercise in exercises
    ] == [
        "Bench Press",
        "Shoulder Press"
    ]

    assert [
        exercise["exercise_order"]
        for exercise in exercises
    ] == [
        1,
        2
    ]