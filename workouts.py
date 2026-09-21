import sqlite3
from datetime import date, datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for

from database import get_db


workouts_bp = Blueprint(
    "workouts",
    __name__
)


def program_redirect(program_id, workout_id=None):
    """Return to a plan, optionally keeping a workout selected."""

    if workout_id is None:
        return redirect(
            url_for(
                "workouts.view_program",
                program_id=program_id
            )
        )

    return redirect(
        url_for(
            "workouts.view_program",
            program_id=program_id,
            selected=workout_id
        )
    )


def get_program(program_id):
    """Retrieve one training plan."""

    db = get_db()

    return db.execute(
        """
        SELECT *
        FROM program
        WHERE program_id = ?
        """,
        (program_id,)
    ).fetchone()


def get_workout(program_id, workout_id):
    """Retrieve a workout belonging to a specific plan."""

    db = get_db()

    return db.execute(
        """
        SELECT *
        FROM workout
        WHERE workout_id = ?
          AND program_id = ?
        """,
        (
            workout_id,
            program_id
        )
    ).fetchone()


def get_workout_exercises(workout_id):
    """Retrieve the exercises assigned to a workout."""

    db = get_db()

    return db.execute(
        """
        SELECT
            exercise.exercise_id,
            exercise.name,
            exercise.primary_muscle,
            exercise.equipment,
            workout_exercise.workout_exercise_id,
            workout_exercise.exercise_order,
            workout_exercise.target_sets,
            workout_exercise.target_reps
        FROM workout_exercise
        JOIN exercise
            ON workout_exercise.exercise_id
            = exercise.exercise_id
        WHERE workout_exercise.workout_id = ?
        ORDER BY
            workout_exercise.exercise_order,
            workout_exercise.workout_exercise_id
        """,
        (workout_id,)
    ).fetchall()


def get_available_exercises(workout_id):
    """Retrieve exercises not already assigned to a workout."""

    db = get_db()

    return db.execute(
        """
        SELECT *
        FROM exercise
        WHERE exercise_id NOT IN (
            SELECT exercise_id
            FROM workout_exercise
            WHERE workout_id = ?
        )
        ORDER BY
            name COLLATE NOCASE,
            equipment COLLATE NOCASE
        """,
        (workout_id,)
    ).fetchall()

def get_previous_performance(exercise_id):
    """Return the most recent recorded performance for an exercise."""

    db = get_db()

    previous_log = db.execute(
        """
        SELECT
            workout_log.log_id,
            workout_log.log_date,
            workout_log.workout_name
        FROM workout_log
        WHERE EXISTS (
            SELECT 1
            FROM exercise_set
            WHERE exercise_set.log_id
                = workout_log.log_id
            AND exercise_set.exercise_id = ?
        )
        ORDER BY
            workout_log.log_date DESC,
            workout_log.log_id DESC
        LIMIT 1
        """,
        (exercise_id,)
    ).fetchone()

    if previous_log is None:
        return {
            "log": None,
            "sets": []
        }

    previous_sets = db.execute(
        """
        SELECT
            set_number,
            weight,
            reps
        FROM exercise_set
        WHERE log_id = ?
          AND exercise_id = ?
        ORDER BY set_number
        """,
        (
            previous_log["log_id"],
            exercise_id
        )
    ).fetchall()

    return {
        "log": previous_log,
        "sets": previous_sets
    }


def build_active_workout_data(workout_id):
    """Build the exercise data needed by the active workout page."""

    exercises = get_workout_exercises(
        workout_id
    )

    exercise_data = []

    for exercise in exercises:
        previous = get_previous_performance(
            exercise["exercise_id"]
        )

        exercise_data.append(
            {
                "exercise": exercise,
                "previous_log": previous["log"],
                "previous_sets": previous["sets"]
            }
        )

    return exercise_data


def validate_workout_date(date_text):
    """Validate a submitted workout date."""

    if not date_text:
        return None, "Workout date is required."

    try:
        workout_date = datetime.strptime(
            date_text,
            "%Y-%m-%d"
        ).date()

    except ValueError:
        return None, "Enter a valid workout date."

    if workout_date > date.today():
        return None, "Workout date cannot be in the future."

    return workout_date.isoformat(), None


def validate_completed_sets(exercises, form):
    """Validate submitted workout values before saving anything."""

    completed_sets = []

    for exercise in exercises:
        exercise_id = exercise["exercise_id"]

        for set_number in range(
            1,
            exercise["target_sets"] + 1
        ):
            weight_key = (
                f"weight_{exercise_id}_{set_number}"
            )

            reps_key = (
                f"reps_{exercise_id}_{set_number}"
            )

            weight_text = form.get(
                weight_key,
                ""
            ).strip()

            reps_text = form.get(
                reps_key,
                ""
            ).strip()

            if not reps_text:
                return (
                    None,
                    (
                        "Enter the repetitions completed for "
                        f"{exercise['name']}, set {set_number}."
                    )
                )

            try:
                reps = int(
                    reps_text
                )

            except ValueError:
                return (
                    None,
                    "Repetitions must be a whole number."
                )

            if reps < 1 or reps > 100:
                return (
                    None,
                    "Repetitions must be between 1 and 100."
                )

            if weight_text:
                try:
                    weight = float(
                        weight_text
                    )

                except ValueError:
                    return (
                        None,
                        "Weight must be a valid number."
                    )

                if weight < 0 or weight > 1000:
                    return (
                        None,
                        (
                            "Weight must be between 0 and "
                            "1000 kilograms."
                        )
                    )

            else:
                weight = None

            completed_sets.append(
                (
                    exercise_id,
                    set_number,
                    weight,
                    reps
                )
            )

    return completed_sets, None


def save_completed_workout(
    workout_id,
    workout_name,
    completed_sets,
    workout_date
):
    """Save a workout log and completed sets as one transaction."""

    db = get_db()

    try:
        cursor = db.execute(
            """
            INSERT INTO workout_log (
                workout_id,
                workout_name,
                log_date
            )
            VALUES (?, ?, ?)
            """,
            (
                workout_id,
                workout_name,
                workout_date
            )
        )

        log_id = cursor.lastrowid

        for completed_set in completed_sets:
            db.execute(
                """
                INSERT INTO exercise_set (
                    log_id,
                    exercise_id,
                    set_number,
                    weight,
                    reps
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    log_id,
                    completed_set[0],
                    completed_set[1],
                    completed_set[2],
                    completed_set[3]
                )
            )

        db.commit()

        return True

    except sqlite3.Error:
        db.rollback()

        return False

@workouts_bp.route(
    "/program/<int:program_id>"
)
def view_program(program_id):
    db = get_db()

    program = get_program(
        program_id
    )

    if program is None:
        return "Plan not found.", 404

    workouts = db.execute(
        """
        SELECT *
        FROM workout
        WHERE program_id = ?
        ORDER BY
            workout_order,
            workout_id
        """,
        (program_id,)
    ).fetchall()

    selected_workout_id = request.args.get(
        "selected",
        type=int
    )

    workout_ids = [
        workout["workout_id"]
        for workout in workouts
    ]

    if selected_workout_id not in workout_ids:
        if workout_ids:
            selected_workout_id = workout_ids[0]
        else:
            selected_workout_id = None

    workout_data = []

    selected_workout_index = None

    if selected_workout_id is not None:
        selected_workout_index = workout_ids.index(
            selected_workout_id
        )

    can_move_workout_left = (
        selected_workout_index is not None
        and selected_workout_index > 0
    )

    can_move_workout_right = (
        selected_workout_index is not None
        and selected_workout_index < len(workout_ids) - 1
    )

    for workout in workouts:
        workout_id = workout["workout_id"]

        workout_data.append(
            {
                "workout": workout,
                "exercises": get_workout_exercises(
                    workout_id
                ),
                "available_exercises": get_available_exercises(
                    workout_id
                )
            }
        )

    return render_template(
        "program.html",
        program=program,
        workout_data=workout_data,
        selected_workout_id=selected_workout_id,
        can_move_workout_left=can_move_workout_left,
        can_move_workout_right=can_move_workout_right
    )


@workouts_bp.route(
    "/program/<int:program_id>/workout/add",
    methods=["POST"]
)
def add_workout(program_id):
    name = request.form.get(
        "name",
        ""
    ).strip()

    if not name:
        flash(
            "Workout name is required.",
            "error"
        )

        return program_redirect(
            program_id
        )

    db = get_db()

    program = get_program(
        program_id
    )

    if program is None:
        return "Plan not found.", 404

    duplicate = db.execute(
        """
        SELECT workout_id
        FROM workout
        WHERE program_id = ?
          AND name = ? COLLATE NOCASE
        """,
        (
            program_id,
            name
        )
    ).fetchone()

    if duplicate is not None:
        flash(
            "A workout with that name already exists "
            "in this plan.",
            "error"
        )

        return program_redirect(
            program_id
        )

    highest_order = db.execute(
        """
        SELECT MAX(workout_order)
        FROM workout
        WHERE program_id = ?
        """,
        (program_id,)
    ).fetchone()[0]

    if highest_order is None:
        new_order = 1
    else:
        new_order = highest_order + 1

    try:
        cursor = db.execute(
            """
            INSERT INTO workout (
                program_id,
                name,
                workout_order,
                created_date
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                program_id,
                name,
                new_order,
                date.today().isoformat()
            )
        )

        workout_id = cursor.lastrowid

        db.commit()

    except sqlite3.IntegrityError:
        db.rollback()

        flash(
            "The workout could not be created.",
            "error"
        )

        return program_redirect(
            program_id
        )

    flash(
        f"{name} was added to {program['name']}.",
        "success"
    )

    return program_redirect(
        program_id,
        workout_id
    )


@workouts_bp.route(
    "/program/<int:program_id>/workout/"
    "<int:workout_id>/rename",
    methods=["POST"]
)
def rename_workout(program_id, workout_id):
    name = request.form.get(
        "name",
        ""
    ).strip()

    if not name:
        flash(
            "Workout name is required.",
            "error"
        )

        return program_redirect(
            program_id,
            workout_id
        )

    db = get_db()

    workout = get_workout(
        program_id,
        workout_id
    )

    if workout is None:
        return "Workout not found.", 404

    duplicate = db.execute(
        """
        SELECT workout_id
        FROM workout
        WHERE program_id = ?
          AND name = ? COLLATE NOCASE
          AND workout_id != ?
        """,
        (
            program_id,
            name,
            workout_id
        )
    ).fetchone()

    if duplicate is not None:
        flash(
            "A workout with that name already exists "
            "in this plan.",
            "error"
        )

        return program_redirect(
            program_id,
            workout_id
        )

    try:
        db.execute(
            """
            UPDATE workout
            SET name = ?
            WHERE workout_id = ?
            """,
            (
                name,
                workout_id
            )
        )

        db.commit()

    except sqlite3.IntegrityError:
        db.rollback()

        flash(
            "The workout could not be renamed.",
            "error"
        )

        return program_redirect(
            program_id,
            workout_id
        )

    flash(
        "Workout renamed successfully.",
        "success"
    )

    return program_redirect(
        program_id,
        workout_id
    )


@workouts_bp.route(
    "/program/<int:program_id>/workout/"
    "<int:workout_id>/delete",
    methods=["POST"]
)
def delete_workout(program_id, workout_id):
    db = get_db()

    workout = get_workout(
        program_id,
        workout_id
    )

    if workout is None:
        return "Workout not found.", 404

    try:
        db.execute(
            """
            DELETE FROM workout
            WHERE workout_id = ?
            """,
            (workout_id,)
        )

        db.commit()

    except sqlite3.Error:
        db.rollback()

        flash(
            "The workout could not be deleted.",
            "error"
        )

        return program_redirect(
            program_id,
            workout_id
        )

    flash(
        f"{workout['name']} was deleted.",
        "success"
    )

    return program_redirect(
        program_id
    )


@workouts_bp.route(
    "/program/<int:program_id>/workout/"
    "<int:workout_id>/exercise/add",
    methods=["POST"]
)
def add_workout_exercise(program_id, workout_id):
    exercise_id = request.form.get(
        "exercise_id",
        type=int
    )

    if exercise_id is None:
        flash(
            "Select an exercise.",
            "error"
        )

        return program_redirect(
            program_id,
            workout_id
        )

    db = get_db()

    workout = get_workout(
        program_id,
        workout_id
    )

    if workout is None:
        return "Workout not found.", 404

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

    duplicate = db.execute(
        """
        SELECT workout_exercise_id
        FROM workout_exercise
        WHERE workout_id = ?
          AND exercise_id = ?
        """,
        (
            workout_id,
            exercise_id
        )
    ).fetchone()

    if duplicate is not None:
        flash(
            "That exercise is already in this workout.",
            "error"
        )

        return program_redirect(
            program_id,
            workout_id
        )

    highest_order = db.execute(
        """
        SELECT MAX(exercise_order)
        FROM workout_exercise
        WHERE workout_id = ?
        """,
        (workout_id,)
    ).fetchone()[0]

    if highest_order is None:
        new_order = 1
    else:
        new_order = highest_order + 1

    try:
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
                exercise_id,
                new_order,
                3,
                10
            )
        )

        db.commit()

    except sqlite3.IntegrityError:
        db.rollback()

        flash(
            "The exercise could not be added "
            "to this workout.",
            "error"
        )

        return program_redirect(
            program_id,
            workout_id
        )

    flash(
        f"{exercise['name']} was added to "
        f"{workout['name']}.",
        "success"
    )

    return program_redirect(
        program_id,
        workout_id
    )


@workouts_bp.route(
    "/program/<int:program_id>/workout/"
    "<int:workout_id>/exercise/"
    "<int:workout_exercise_id>/update",
    methods=["POST"]
)
def update_workout_exercise(
    program_id,
    workout_id,
    workout_exercise_id
):
    target_sets = request.form.get(
        "target_sets",
        type=int
    )

    target_reps = request.form.get(
        "target_reps",
        type=int
    )

    if (
        target_sets is None
        or target_sets < 1
        or target_sets > 20
    ):
        flash(
            "Target sets must be between 1 and 20.",
            "error"
        )

        return program_redirect(
            program_id,
            workout_id
        )

    if (
        target_reps is None
        or target_reps < 1
        or target_reps > 100
    ):
        flash(
            "Target reps must be between 1 and 100.",
            "error"
        )

        return program_redirect(
            program_id,
            workout_id
        )

    db = get_db()

    workout = get_workout(
        program_id,
        workout_id
    )

    workout_exercise = db.execute(
        """
        SELECT workout_exercise_id
        FROM workout_exercise
        WHERE workout_exercise_id = ?
          AND workout_id = ?
        """,
        (
            workout_exercise_id,
            workout_id
        )
    ).fetchone()

    if (
        workout is None
        or workout_exercise is None
    ):
        return "Workout exercise not found.", 404

    try:
        db.execute(
            """
            UPDATE workout_exercise
            SET target_sets = ?,
                target_reps = ?
            WHERE workout_exercise_id = ?
            """,
            (
                target_sets,
                target_reps,
                workout_exercise_id
            )
        )

        db.commit()

    except sqlite3.IntegrityError:
        db.rollback()

        flash(
            "The exercise targets could not be updated.",
            "error"
        )

        return program_redirect(
            program_id,
            workout_id
        )

    flash(
        "Exercise targets updated.",
        "success"
    )

    return program_redirect(
        program_id,
        workout_id
    )


@workouts_bp.route(
    "/program/<int:program_id>/workout/"
    "<int:workout_id>/exercise/"
    "<int:workout_exercise_id>/remove",
    methods=["POST"]
)
def remove_workout_exercise(
    program_id,
    workout_id,
    workout_exercise_id
):
    db = get_db()

    workout = get_workout(
        program_id,
        workout_id
    )

    workout_exercise = db.execute(
        """
        SELECT
            workout_exercise.workout_exercise_id,
            exercise.name
        FROM workout_exercise
        JOIN exercise
            ON workout_exercise.exercise_id
            = exercise.exercise_id
        WHERE workout_exercise.workout_exercise_id = ?
          AND workout_exercise.workout_id = ?
        """,
        (
            workout_exercise_id,
            workout_id
        )
    ).fetchone()

    if (
        workout is None
        or workout_exercise is None
    ):
        return "Workout exercise not found.", 404

    try:
        db.execute(
            """
            DELETE FROM workout_exercise
            WHERE workout_exercise_id = ?
            """,
            (workout_exercise_id,)
        )

        db.commit()

    except sqlite3.Error:
        db.rollback()

        flash(
            "The exercise could not be removed.",
            "error"
        )

        return program_redirect(
            program_id,
            workout_id
        )

    flash(
        f"{workout_exercise['name']} was removed "
        "from the workout.",
        "success"
    )

    return program_redirect(
        program_id,
        workout_id
    )

@workouts_bp.route(
    "/program/<int:program_id>/workout/"
    "<int:workout_id>/start"
)
def start_workout(program_id, workout_id):
    program = get_program(
        program_id
    )

    workout = get_workout(
        program_id,
        workout_id
    )

    if (
        program is None
        or workout is None
    ):
        return "Workout not found.", 404

    exercise_data = build_active_workout_data(
        workout_id
    )

    if not exercise_data:
        flash(
            "Add at least one exercise before "
            "starting this workout.",
            "error"
        )

        return program_redirect(
            program_id,
            workout_id
        )

    return render_template(
        "active_workout.html",
        program=program,
        workout=workout,
        exercise_data=exercise_data,
        form_data={},
        today=date.today().isoformat()
    )


@workouts_bp.route(
    "/program/<int:program_id>/workout/"
    "<int:workout_id>/finish",
    methods=["POST"]
)
def finish_workout(program_id, workout_id):
    program = get_program(
        program_id
    )

    workout = get_workout(
        program_id,
        workout_id
    )

    if (
        program is None
        or workout is None
    ):
        return "Workout not found.", 404

    exercises = get_workout_exercises(
        workout_id
    )

    if not exercises:
        flash(
            "This workout does not contain any exercises.",
            "error"
        )

        return program_redirect(
            program_id,
            workout_id
        )

    workout_date, date_error = validate_workout_date(
        request.form.get(
            "workout_date",
            ""
        )
    )

    if date_error is not None:
        flash(
            date_error,
            "error"
        )

        exercise_data = build_active_workout_data(
            workout_id
        )

        return render_template(
            "active_workout.html",
            program=program,
            workout=workout,
            exercise_data=exercise_data,
            form_data=request.form,
            today=date.today().isoformat()
        )

    completed_sets, error = validate_completed_sets(
        exercises,
        request.form
    )

    if error is not None:
        flash(
            error,
            "error"
        )

        exercise_data = build_active_workout_data(
            workout_id
        )

        return render_template(
            "active_workout.html",
            program=program,
            workout=workout,
            exercise_data=exercise_data,
            form_data=request.form,
            today=date.today().isoformat()
        )

    saved = save_completed_workout(
        workout_id,
        workout["name"],
        completed_sets,
        workout_date
    )

    if not saved:
        flash(
            "The workout could not be saved.",
            "error"
        )

        exercise_data = build_active_workout_data(
            workout_id
        )

        return render_template(
            "active_workout.html",
            program=program,
            workout=workout,
            exercise_data=exercise_data,
            form_data=request.form,
            today=date.today().isoformat()
        )

    flash(
        f"{workout['name']} was completed and saved.",
        "success"
    )

    return program_redirect(
        program_id,
        workout_id
    )

@workouts_bp.route(
    "/program/<int:program_id>/workout/<int:workout_id>/move-left",
    methods=["POST"]
)
def move_workout_left(program_id, workout_id):
    return move_workout(program_id, workout_id, "left")


@workouts_bp.route(
    "/program/<int:program_id>/workout/<int:workout_id>/move-right",
    methods=["POST"]
)
def move_workout_right(program_id, workout_id):
    return move_workout(program_id, workout_id, "right")

def move_workout(program_id, workout_id, direction):
    """Move a workout one position left or right."""

    db = get_db()

    current = db.execute(
        """
        SELECT *
        FROM workout
        WHERE workout_id = ?
          AND program_id = ?
        """,
        (
            workout_id,
            program_id
        )
    ).fetchone()

    if current is None:
        return "Workout not found.", 404

    if direction == "left":
        neighbour = db.execute(
            """
            SELECT *
            FROM workout
            WHERE program_id = ?
              AND workout_order < ?
            ORDER BY workout_order DESC
            LIMIT 1
            """,
            (
                program_id,
                current["workout_order"]
            )
        ).fetchone()

    else:
        neighbour = db.execute(
            """
            SELECT *
            FROM workout
            WHERE program_id = ?
              AND workout_order > ?
            ORDER BY workout_order ASC
            LIMIT 1
            """,
            (
                program_id,
                current["workout_order"]
            )
        ).fetchone()

    if neighbour is None:
        return program_redirect(
            program_id,
            workout_id
        )

    try:
        db.execute(
            """
            UPDATE workout
            SET workout_order =
                CASE
                    WHEN workout_id = ?
                        THEN ?
                    WHEN workout_id = ?
                        THEN ?
                END
            WHERE workout_id IN (?, ?)
              AND program_id = ?
            """,
            (
                current["workout_id"],
                neighbour["workout_order"],

                neighbour["workout_id"],
                current["workout_order"],

                current["workout_id"],
                neighbour["workout_id"],

                program_id
            )
        )

        db.commit()

    except sqlite3.Error:
        db.rollback()

        flash(
            "The workout order could not be updated.",
            "error"
        )

    return program_redirect(
        program_id,
        workout_id
    )

@workouts_bp.route(
    "/program/<int:program_id>/workout/<int:workout_id>/exercise/<int:workout_exercise_id>/move-up",
    methods=["POST"]
)
def move_workout_exercise_up(
    program_id,
    workout_id,
    workout_exercise_id
):
    return move_workout_exercise(
        program_id,
        workout_id,
        workout_exercise_id,
        "up"
    )


@workouts_bp.route(
    "/program/<int:program_id>/workout/<int:workout_id>/exercise/<int:workout_exercise_id>/move-down",
    methods=["POST"]
)
def move_workout_exercise_down(
    program_id,
    workout_id,
    workout_exercise_id
):
    return move_workout_exercise(
        program_id,
        workout_id,
        workout_exercise_id,
        "down"
    )

def move_workout_exercise(
    program_id,
    workout_id,
    workout_exercise_id,
    direction
):
    """Move an exercise one position up or down."""

    db = get_db()

    workout = get_workout(
        program_id,
        workout_id
    )

    if workout is None:
        return "Workout not found.", 404

    current = db.execute(
        """
        SELECT *
        FROM workout_exercise
        WHERE workout_exercise_id = ?
          AND workout_id = ?
        """,
        (
            workout_exercise_id,
            workout_id
        )
    ).fetchone()

    if current is None:
        return "Workout exercise not found.", 404

    if direction == "up":
        neighbour = db.execute(
            """
            SELECT *
            FROM workout_exercise
            WHERE workout_id = ?
              AND exercise_order < ?
            ORDER BY exercise_order DESC
            LIMIT 1
            """,
            (
                workout_id,
                current["exercise_order"]
            )
        ).fetchone()

    else:
        neighbour = db.execute(
            """
            SELECT *
            FROM workout_exercise
            WHERE workout_id = ?
              AND exercise_order > ?
            ORDER BY exercise_order ASC
            LIMIT 1
            """,
            (
                workout_id,
                current["exercise_order"]
            )
        ).fetchone()

    if neighbour is None:
        return program_redirect(
            program_id,
            workout_id
        )

    try:
        db.execute(
            """
            UPDATE workout_exercise
            SET exercise_order =
                CASE
                    WHEN workout_exercise_id = ?
                        THEN ?
                    WHEN workout_exercise_id = ?
                        THEN ?
                END
            WHERE workout_exercise_id IN (?, ?)
              AND workout_id = ?
            """,
            (
                current["workout_exercise_id"],
                neighbour["exercise_order"],

                neighbour["workout_exercise_id"],
                current["exercise_order"],

                current["workout_exercise_id"],
                neighbour["workout_exercise_id"],

                workout_id
            )
        )

        db.commit()

    except sqlite3.Error:
        db.rollback()

        flash(
            "The exercise order could not be updated.",
            "error"
        )

    return program_redirect(
        program_id,
        workout_id
    )