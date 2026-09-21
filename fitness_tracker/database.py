import sqlite3
from pathlib import Path

import click
from flask import current_app, g
from flask.cli import with_appcontext


def get_db():
    """Return the database connection for the current request."""

    if "db" not in g:
        connection = sqlite3.connect(
            current_app.config["DATABASE"]
        )

        connection.row_factory = sqlite3.Row

        connection.execute(
            "PRAGMA foreign_keys = ON"
        )

        g.db = connection

    return g.db


def close_db(error=None):
    """Close the database connection after a request."""

    connection = g.pop(
        "db",
        None
    )

    if connection is not None:
        connection.close()


def init_db():
    """Create the database tables using schema.sql."""

    connection = get_db()

    schema_path = (
        Path(current_app.root_path)
        / "schema.sql"
    )

    with schema_path.open(
        "r",
        encoding="utf-8"
    ) as schema_file:
        connection.executescript(
            schema_file.read()
        )

    connection.commit()


def seed_default_data():
    """Add the starter exercise library and example PPL plan."""

    db = get_db()

    default_exercises = [
        (
            "Barbell Bench Press",
            "Chest",
            "Barbell"
        ),
        (
            "Press Up",
            "Chest",
            "Bodyweight"
        ),
        (
            "Dumbbell Shoulder Press",
            "Front Delts",
            "Dumbbell"
        ),
        (
            "Dumbbell Lateral Raise",
            "Side Delts",
            "Dumbbell"
        ),
        (
            "Cable Tricep Pushdown",
            "Triceps",
            "Cable"
        ),
        (
            "Lat Pulldown",
            "Lats",
            "Machine"
        ),
        (
            "Barbell Row",
            "Upper Back",
            "Barbell"
        ),
        (
            "Close Grip Row",
            "Lats",
            "Machine"
        ),
        (
            "Dumbbell Bicep Curl",
            "Biceps",
            "Dumbbell"
        ),
        (
            "Barbell Squat",
            "Quads",
            "Barbell"
        ),
        (
            "Leg Press",
            "Quads",
            "Machine"
        ),
        (
            "Romanian Deadlift",
            "Hamstrings",
            "Barbell"
        ),
        (
            "Leg Curl",
            "Hamstrings",
            "Machine"
        ),
        (
            "Calf Raise",
            "Calves",
            "Machine"
        )
    ]

    try:
        for name, muscle, equipment in default_exercises:
            db.execute(
                """
                INSERT OR IGNORE INTO exercise (
                    name,
                    primary_muscle,
                    equipment,
                    is_custom
                )
                VALUES (?, ?, ?, 0)
                """,
                (
                    name,
                    muscle,
                    equipment
                )
            )

        existing_program = db.execute(
            """
            SELECT program_id
            FROM program
            WHERE name = ? COLLATE NOCASE
            """,
            ("Example PPL",)
        ).fetchone()

        if existing_program is None:
            active_program = db.execute(
                """
                SELECT program_id
                FROM program
                WHERE is_active = 1
                LIMIT 1
                """
            ).fetchone()

            is_active = (
                1
                if active_program is None
                else 0
            )

            cursor = db.execute(
                """
                INSERT INTO program (
                    name,
                    is_active,
                    created_date
                )
                VALUES (?, ?, DATE('now'))
                """,
                (
                    "Example PPL",
                    is_active
                )
            )

            program_id = cursor.lastrowid

            create_example_ppl(
                db,
                program_id
            )

        db.commit()

    except Exception:
        db.rollback()
        raise


def create_example_ppl(db, program_id):
    """Create the example Push/Pull/Legs training plan."""

    workouts = {
        "Push": [
            (
                "Barbell Bench Press",
                "Barbell",
                3,
                8
            ),
            (
                "Dumbbell Shoulder Press",
                "Dumbbell",
                3,
                10
            ),
            (
                "Dumbbell Lateral Raise",
                "Dumbbell",
                3,
                12
            ),
            (
                "Cable Tricep Pushdown",
                "Cable",
                3,
                12
            )
        ],

        "Pull": [
            (
                "Lat Pulldown",
                "Machine",
                3,
                10
            ),
            (
                "Barbell Row",
                "Barbell",
                3,
                8
            ),
            (
                "Close Grip Row",
                "Machine",
                3,
                10
            ),
            (
                "Dumbbell Bicep Curl",
                "Dumbbell",
                3,
                10
            )
        ],

        "Legs": [
            (
                "Barbell Squat",
                "Barbell",
                3,
                8
            ),
            (
                "Romanian Deadlift",
                "Barbell",
                3,
                10
            ),
            (
                "Leg Press",
                "Machine",
                3,
                10
            ),
            (
                "Leg Curl",
                "Machine",
                3,
                12
            ),
            (
                "Calf Raise",
                "Machine",
                3,
                12
            )
        ]
    }

    for workout_order, (
        workout_name,
        exercises
    ) in enumerate(
        workouts.items(),
        start=1
    ):
        cursor = db.execute(
            """
            INSERT INTO workout (
                program_id,
                name,
                workout_order,
                created_date
            )
            VALUES (?, ?, ?, DATE('now'))
            """,
            (
                program_id,
                workout_name,
                workout_order
            )
        )

        workout_id = cursor.lastrowid

        for exercise_order, exercise_data in enumerate(
            exercises,
            start=1
        ):
            (
                exercise_name,
                equipment,
                target_sets,
                target_reps
            ) = exercise_data

            exercise = db.execute(
                """
                SELECT exercise_id
                FROM exercise
                WHERE name = ? COLLATE NOCASE
                  AND equipment = ? COLLATE NOCASE
                """,
                (
                    exercise_name,
                    equipment
                )
            ).fetchone()

            if exercise is None:
                raise ValueError(
                    "Seed exercise not found: "
                    f"{exercise_name} ({equipment})"
                )

            db.execute(
                """
                INSERT INTO workout_exercise (
                    workout_id,
                    exercise_id,
                    exercise_order,
                    target_sets,
                    target_reps
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    workout_id,
                    exercise["exercise_id"],
                    exercise_order,
                    target_sets,
                    target_reps
                )
            )


@click.command("seed-data")
@with_appcontext
def seed_data_command():
    """Add default exercises and the example plan."""

    seed_default_data()

    click.echo(
        "Default exercises and example plan added."
    )


@click.command("init-db")
@with_appcontext
def init_db_command():
    """Create the database tables."""

    init_db()

    click.echo(
        "Database initialised."
    )


def init_app(app):
    """Register database handling with Flask."""

    app.teardown_appcontext(
        close_db
    )

    app.cli.add_command(
        init_db_command
    )

    app.cli.add_command(
        seed_data_command
    )