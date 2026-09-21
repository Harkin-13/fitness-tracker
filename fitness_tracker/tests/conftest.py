import pytest

from app import create_app
from database import get_db, init_db


@pytest.fixture
def app(tmp_path):
    database_path = (
        tmp_path
        / "test_fitness_tracker.db"
    )

    app = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret-key",
            "DATABASE": str(database_path)
        }
    )

    with app.app_context():
        init_db()

    yield app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def create_program(client, app):
    def _create_program(name="PPL"):
        client.post(
            "/program/add",
            data={
                "name": name
            }
        )

        with app.app_context():
            program = get_db().execute(
                """
                SELECT *
                FROM program
                WHERE name = ?
                """,
                (name,)
            ).fetchone()

        return program

    return _create_program


@pytest.fixture
def create_exercise(client, app):
    def _create_exercise(
        name="Bench Press",
        primary_muscle="Chest",
        equipment="Barbell"
    ):
        client.post(
            "/exercise/add",
            data={
                "name": name,
                "primary_muscle": primary_muscle,
                "equipment": equipment
            }
        )

        with app.app_context():
            exercise = get_db().execute(
                """
                SELECT *
                FROM exercise
                WHERE name = ?
                  AND equipment = ?
                """,
                (
                    name,
                    equipment
                )
            ).fetchone()

        return exercise

    return _create_exercise


@pytest.fixture
def create_workout(client, app):
    def _create_workout(
        program_id,
        name="Push"
    ):
        client.post(
            f"/program/{program_id}/workout/add",
            data={
                "name": name
            }
        )

        with app.app_context():
            workout = get_db().execute(
                """
                SELECT *
                FROM workout
                WHERE program_id = ?
                  AND name = ?
                """,
                (
                    program_id,
                    name
                )
            ).fetchone()

        return workout

    return _create_workout


@pytest.fixture
def assign_exercise(client, app):
    def _assign_exercise(
        program_id,
        workout_id,
        exercise_id
    ):
        client.post(
            (
                f"/program/{program_id}"
                f"/workout/{workout_id}"
                "/exercise/add"
            ),
            data={
                "exercise_id": exercise_id
            }
        )

        with app.app_context():
            assignment = get_db().execute(
                """
                SELECT *
                FROM workout_exercise
                WHERE workout_id = ?
                  AND exercise_id = ?
                """,
                (
                    workout_id,
                    exercise_id
                )
            ).fetchone()

        return assignment

    return _assign_exercise


@pytest.fixture
def complete_workout(client):
    def _complete_workout(
        program_id,
        workout_id,
        exercise_id,
        workout_date="2026-09-01",
        weights=None,
        reps=None
    ):
        if weights is None:
            weights = [
                "30",
                "30",
                "30"
            ]

        if reps is None:
            reps = [
                "8",
                "8",
                "7"
            ]

        data = {
            "workout_date": workout_date
        }

        for index in range(3):
            set_number = index + 1

            data[
                f"weight_{exercise_id}_{set_number}"
            ] = weights[index]

            data[
                f"reps_{exercise_id}_{set_number}"
            ] = reps[index]

        return client.post(
            (
                f"/program/{program_id}"
                f"/workout/{workout_id}"
                "/finish"
            ),
            data=data,
            follow_redirects=True
        )

    return _complete_workout


@pytest.fixture
def workout_setup(
    create_program,
    create_exercise,
    create_workout,
    assign_exercise
):
    program = create_program(
        "PPL"
    )

    exercise = create_exercise(
        "Incline Dumbbell Press",
        "Chest",
        "Dumbbell"
    )

    workout = create_workout(
        program["program_id"],
        "Push"
    )

    assignment = assign_exercise(
        program["program_id"],
        workout["workout_id"],
        exercise["exercise_id"]
    )

    return {
        "program": program,
        "workout": workout,
        "exercise": exercise,
        "assignment": assignment
    }