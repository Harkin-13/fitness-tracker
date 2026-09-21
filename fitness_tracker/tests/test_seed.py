from database import get_db, seed_default_data


def test_seed_creates_default_exercises(app):
    with app.app_context():
        seed_default_data()

        exercises = get_db().execute(
            """
            SELECT *
            FROM exercise
            ORDER BY name
            """
        ).fetchall()

    assert len(exercises) == 14

    assert all(
        exercise["is_custom"] == 0
        for exercise in exercises
    )

    exercise_names = {
        exercise["name"]
        for exercise in exercises
    }

    assert "Barbell Bench Press" in exercise_names
    assert "Press Up" in exercise_names
    assert "Dumbbell Bicep Curl" in exercise_names
    assert "Barbell Squat" in exercise_names
    assert "Cable Tricep Pushdown" in exercise_names
    assert "Lat Pulldown" in exercise_names


def test_seed_creates_example_ppl(app):
    with app.app_context():
        seed_default_data()

        db = get_db()

        program = db.execute(
            """
            SELECT *
            FROM program
            WHERE name = ?
            """,
            ("Example PPL",)
        ).fetchone()

        assert program is not None
        assert program["is_active"] == 1

        workouts = db.execute(
            """
            SELECT *
            FROM workout
            WHERE program_id = ?
            ORDER BY workout_order
            """,
            (program["program_id"],)
        ).fetchall()

        workout_names = [
            workout["name"]
            for workout in workouts
        ]

        assert workout_names == [
            "Push",
            "Pull",
            "Legs"
        ]

        expected_exercise_counts = {
            "Push": 4,
            "Pull": 4,
            "Legs": 5
        }

        for workout in workouts:
            exercise_count = db.execute(
                """
                SELECT COUNT(*)
                FROM workout_exercise
                WHERE workout_id = ?
                """,
                (workout["workout_id"],)
            ).fetchone()[0]

            assert exercise_count == (
                expected_exercise_counts[
                    workout["name"]
                ]
            )


def test_seed_creates_expected_workout_targets(app):
    with app.app_context():
        seed_default_data()

        db = get_db()

        bench_press = db.execute(
            """
            SELECT
                workout_exercise.target_sets,
                workout_exercise.target_reps
            FROM workout_exercise
            JOIN workout
                ON workout_exercise.workout_id
                = workout.workout_id
            JOIN exercise
                ON workout_exercise.exercise_id
                = exercise.exercise_id
            WHERE workout.name = ?
              AND exercise.name = ?
            """,
            (
                "Push",
                "Barbell Bench Press"
            )
        ).fetchone()

        assert bench_press is not None
        assert bench_press["target_sets"] == 3
        assert bench_press["target_reps"] == 8

        calf_raise = db.execute(
            """
            SELECT
                workout_exercise.target_sets,
                workout_exercise.target_reps
            FROM workout_exercise
            JOIN workout
                ON workout_exercise.workout_id
                = workout.workout_id
            JOIN exercise
                ON workout_exercise.exercise_id
                = exercise.exercise_id
            WHERE workout.name = ?
              AND exercise.name = ?
            """,
            (
                "Legs",
                "Calf Raise"
            )
        ).fetchone()

        assert calf_raise is not None
        assert calf_raise["target_sets"] == 3
        assert calf_raise["target_reps"] == 12


def test_seed_does_not_create_fake_history(app):
    with app.app_context():
        seed_default_data()

        db = get_db()

        workout_log_count = db.execute(
            """
            SELECT COUNT(*)
            FROM workout_log
            """
        ).fetchone()[0]

        exercise_set_count = db.execute(
            """
            SELECT COUNT(*)
            FROM exercise_set
            """
        ).fetchone()[0]

    assert workout_log_count == 0
    assert exercise_set_count == 0


def test_seed_can_be_run_twice_without_duplicates(app):
    with app.app_context():
        seed_default_data()
        seed_default_data()

        db = get_db()

        exercise_count = db.execute(
            """
            SELECT COUNT(*)
            FROM exercise
            """
        ).fetchone()[0]

        program_count = db.execute(
            """
            SELECT COUNT(*)
            FROM program
            WHERE name = ?
            """,
            ("Example PPL",)
        ).fetchone()[0]

        workout_count = db.execute(
            """
            SELECT COUNT(*)
            FROM workout
            """
        ).fetchone()[0]

        assignment_count = db.execute(
            """
            SELECT COUNT(*)
            FROM workout_exercise
            """
        ).fetchone()[0]

    assert exercise_count == 14
    assert program_count == 1
    assert workout_count == 3
    assert assignment_count == 13


def test_seed_cli_command(app):
    runner = app.test_cli_runner()

    result = runner.invoke(
        args=[
            "seed-data"
        ]
    )

    assert result.exit_code == 0

    assert (
        "Default exercises and example plan added."
        in result.output
    )

    with app.app_context():
        program = get_db().execute(
            """
            SELECT *
            FROM program
            WHERE name = ?
            """,
            ("Example PPL",)
        ).fetchone()

    assert program is not None