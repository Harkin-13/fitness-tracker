import sqlite3

from flask import Blueprint, flash, redirect, render_template, request, url_for

from database import get_db


exercises_bp = Blueprint(
    "exercises",
    __name__
)


PRIMARY_MUSCLES = [
    "Traps",
    "Front Delts",
    "Side Delts",
    "Rear Delts",
    "Chest",
    "Upper Back",
    "Lats",
    "Abs",
    "Biceps",
    "Triceps",
    "Forearms",
    "Lower Back",
    "Abductors",
    "Adductors",
    "Glutes",
    "Quads",
    "Hamstrings",
    "Calves",
    "Other",
]


EQUIPMENT_OPTIONS = [
    "Machine",
    "Cable",
    "Smith machine",
    "Dumbbell",
    "Barbell",
    "Bodyweight",
    "Other",
]


@exercises_bp.route("/exercises")
def exercise_library():
    db = get_db()

    exercises = db.execute(
        """
        SELECT *
        FROM exercise
        ORDER BY
            name COLLATE NOCASE,
            equipment COLLATE NOCASE
        """
    ).fetchall()

    return render_template(
        "exercises.html",
        exercises=exercises,
        primary_muscles=PRIMARY_MUSCLES,
        equipment_options=EQUIPMENT_OPTIONS
    )


@exercises_bp.route(
    "/exercise/add",
    methods=["POST"]
)
def add_exercise():
    name = request.form.get(
        "name",
        ""
    ).strip()

    primary_muscle = request.form.get(
        "primary_muscle",
        ""
    ).strip()

    equipment = request.form.get(
        "equipment",
        ""
    ).strip()

    if not name:
        flash(
            "Exercise name is required.",
            "error"
        )

        return redirect(
            url_for("exercises.exercise_library")
        )

    if primary_muscle not in PRIMARY_MUSCLES:
        flash(
            "Select a valid primary muscle.",
            "error"
        )

        return redirect(
            url_for("exercises.exercise_library")
        )

    if equipment not in EQUIPMENT_OPTIONS:
        flash(
            "Select valid equipment.",
            "error"
        )

        return redirect(
            url_for("exercises.exercise_library")
        )

    db = get_db()

    duplicate = db.execute(
        """
        SELECT exercise_id
        FROM exercise
        WHERE name = ? COLLATE NOCASE
          AND equipment = ? COLLATE NOCASE
        """,
        (
            name,
            equipment
        )
    ).fetchone()

    if duplicate is not None:
        flash(
            "That exercise and equipment combination "
            "already exists.",
            "error"
        )

        return redirect(
            url_for("exercises.exercise_library")
        )

    try:
        db.execute(
            """
            INSERT INTO exercise (
                name,
                primary_muscle,
                equipment,
                is_custom
            )
            VALUES (?, ?, ?, 1)
            """,
            (
                name,
                primary_muscle,
                equipment
            )
        )

        db.commit()

    except sqlite3.IntegrityError:
        db.rollback()

        flash(
            "The exercise could not be added.",
            "error"
        )

        return redirect(
            url_for("exercises.exercise_library")
        )

    flash(
        "Exercise added successfully.",
        "success"
    )

    return redirect(
        url_for("exercises.exercise_library")
    )


@exercises_bp.route(
    "/exercise/<int:exercise_id>/edit",
    methods=["GET", "POST"]
)
def edit_exercise(exercise_id):
    db = get_db()

    exercise = db.execute(
        """
        SELECT *
        FROM exercise
        WHERE exercise_id = ?
        """,
        (exercise_id,)
    ).fetchone()

    if exercise is None:
        return "Exercise not found.", 404

    if request.method == "POST":
        name = request.form.get(
            "name",
            ""
        ).strip()

        primary_muscle = request.form.get(
            "primary_muscle",
            ""
        ).strip()

        equipment = request.form.get(
            "equipment",
            ""
        ).strip()

        if not name:
            flash(
                "Exercise name is required.",
                "error"
            )

            return redirect(
                url_for(
                    "exercises.edit_exercise",
                    exercise_id=exercise_id
                )
            )

        if primary_muscle not in PRIMARY_MUSCLES:
            flash(
                "Select a valid primary muscle.",
                "error"
            )

            return redirect(
                url_for(
                    "exercises.edit_exercise",
                    exercise_id=exercise_id
                )
            )

        if equipment not in EQUIPMENT_OPTIONS:
            flash(
                "Select valid equipment.",
                "error"
            )

            return redirect(
                url_for(
                    "exercises.edit_exercise",
                    exercise_id=exercise_id
                )
            )

        duplicate = db.execute(
            """
            SELECT exercise_id
            FROM exercise
            WHERE name = ? COLLATE NOCASE
              AND equipment = ? COLLATE NOCASE
              AND exercise_id != ?
            """,
            (
                name,
                equipment,
                exercise_id
            )
        ).fetchone()

        if duplicate is not None:
            flash(
                "That exercise and equipment combination "
                "already exists.",
                "error"
            )

            return redirect(
                url_for(
                    "exercises.edit_exercise",
                    exercise_id=exercise_id
                )
            )

        try:
            db.execute(
                """
                UPDATE exercise
                SET name = ?,
                    primary_muscle = ?,
                    equipment = ?
                WHERE exercise_id = ?
                """,
                (
                    name,
                    primary_muscle,
                    equipment,
                    exercise_id
                )
            )

            db.commit()

        except sqlite3.IntegrityError:
            db.rollback()

            flash(
                "The exercise could not be updated.",
                "error"
            )

            return redirect(
                url_for(
                    "exercises.edit_exercise",
                    exercise_id=exercise_id
                )
            )

        flash(
            "Exercise updated successfully.",
            "success"
        )

        return redirect(
            url_for("exercises.exercise_library")
        )

    return render_template(
        "edit_exercise.html",
        exercise=exercise,
        primary_muscles=PRIMARY_MUSCLES,
        equipment_options=EQUIPMENT_OPTIONS
    )


@exercises_bp.route(
    "/exercise/<int:exercise_id>/delete",
    methods=["POST"]
)
def delete_exercise(exercise_id):
    db = get_db()

    exercise = db.execute(
        """
        SELECT *
        FROM exercise
        WHERE exercise_id = ?
        """,
        (exercise_id,)
    ).fetchone()

    if exercise is None:
        return "Exercise not found.", 404

    try:
        db.execute(
            """
            DELETE FROM exercise
            WHERE exercise_id = ?
            """,
            (exercise_id,)
        )

        db.commit()

    except sqlite3.Error:
        db.rollback()

        flash(
            "The exercise could not be deleted.",
            "error"
        )

        return redirect(
            url_for(
                "exercises.exercise_library"
            )
        )

    flash(
        f"{exercise['name']} and its history were deleted.",
        "success"
    )

    return redirect(
        url_for(
            "exercises.exercise_library"
        )
    )