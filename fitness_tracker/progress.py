from datetime import datetime

from flask import Blueprint, render_template, request

from database import get_db


progress_bp = Blueprint(
    "progress",
    __name__
)


def format_date(date_text):
    """Convert an ISO database date into a readable date."""

    try:
        parsed_date = datetime.strptime(
            date_text,
            "%Y-%m-%d"
        )

        return parsed_date.strftime(
            "%d %b %Y"
        ).lstrip("0")

    except ValueError:
        return date_text


def format_short_date(date_text):
    """Return a compact date for graph axis labels."""

    try:
        parsed_date = datetime.strptime(
            date_text,
            "%Y-%m-%d"
        )

        return parsed_date.strftime(
            "%d %b"
        ).lstrip("0")

    except ValueError:
        return date_text


def get_tracked_exercises():
    """Return exercises that have recorded workout history."""

    db = get_db()

    return db.execute(
        """
        SELECT
            exercise.exercise_id,
            exercise.name,
            exercise.primary_muscle,
            exercise.equipment,
            COUNT(
                DISTINCT workout_log.log_id
            ) AS session_count
        FROM exercise
        JOIN exercise_set
            ON exercise.exercise_id
            = exercise_set.exercise_id
        JOIN workout_log
            ON exercise_set.log_id
            = workout_log.log_id
        GROUP BY
            exercise.exercise_id,
            exercise.name,
            exercise.primary_muscle,
            exercise.equipment
        ORDER BY
            exercise.name COLLATE NOCASE,
            exercise.equipment COLLATE NOCASE
        """
    ).fetchall()


def get_exercise(exercise_id):
    """Return one exercise."""

    db = get_db()

    return db.execute(
        """
        SELECT *
        FROM exercise
        WHERE exercise_id = ?
        """,
        (exercise_id,)
    ).fetchone()


def get_exercise_history(exercise_id):
    """Return every recorded set for an exercise."""

    db = get_db()

    return db.execute(
        """
        SELECT
            workout_log.log_id,
            workout_log.log_date,
            workout_log.workout_name,
            exercise_set.set_number,
            exercise_set.weight,
            exercise_set.reps
        FROM exercise_set
        JOIN workout_log
            ON exercise_set.log_id
            = workout_log.log_id
        WHERE exercise_set.exercise_id = ?
        ORDER BY
            workout_log.log_date,
            workout_log.log_id,
            exercise_set.set_number
        """,
        (exercise_id,)
    ).fetchall()


def build_progress_sessions(exercise_id):
    """Group recorded sets into individual training sessions."""

    rows = get_exercise_history(
        exercise_id
    )

    grouped_sessions = {}

    for row in rows:
        log_id = row["log_id"]

        if log_id not in grouped_sessions:
            grouped_sessions[log_id] = {
                "log_id": log_id,
                "log_date": row["log_date"],
                "workout_name": row["workout_name"],
                "sets": []
            }

        grouped_sessions[log_id]["sets"].append(
            {
                "set_number": row["set_number"],
                "weight": row["weight"],
                "reps": row["reps"]
            }
        )

    sessions = []

    for session in grouped_sessions.values():
        sets = session["sets"]

        weighted_sets = [
            completed_set
            for completed_set in sets
            if completed_set["weight"] is not None
        ]

        best_reps = max(
            completed_set["reps"]
            for completed_set in sets
        )

        total_reps = sum(
            completed_set["reps"]
            for completed_set in sets
        )

        if weighted_sets:
            best_weight = max(
                completed_set["weight"]
                for completed_set in weighted_sets
            )

            volume = sum(
                completed_set["weight"]
                * completed_set["reps"]
                for completed_set in weighted_sets
            )

            best_set = max(
                weighted_sets,
                key=lambda completed_set: (
                    completed_set["weight"],
                    completed_set["reps"]
                )
            )

            best_set_weight = best_set["weight"]
            best_set_reps = best_set["reps"]

        else:
            best_weight = None
            volume = None

            best_set = max(
                sets,
                key=lambda completed_set:
                    completed_set["reps"]
            )

            best_set_weight = None
            best_set_reps = best_set["reps"]

        sessions.append(
            {
                "log_id": session["log_id"],
                "log_date": session["log_date"],
                "display_date": format_date(
                    session["log_date"]
                ),
                "short_date": format_short_date(
                    session["log_date"]
                ),
                "workout_name": session["workout_name"],
                "best_weight": best_weight,
                "best_reps": best_reps,
                "total_reps": total_reps,
                "volume": (
                    round(volume, 2)
                    if volume is not None
                    else None
                ),
                "best_set_weight": best_set_weight,
                "best_set_reps": best_set_reps
            }
        )

    return sessions


@progress_bp.route("/graphs")
def graphs():
    tracked_exercises = get_tracked_exercises()

    if not tracked_exercises:
        return render_template(
            "graphs.html",
            tracked_exercises=[],
            selected_exercise=None,
            sessions=[],
            graph_data=[],
            has_weight_data=False
        )

    selected_exercise_id = request.args.get(
        "exercise_id",
        type=int
    )

    valid_exercise_ids = {
        exercise["exercise_id"]
        for exercise in tracked_exercises
    }

    if selected_exercise_id not in valid_exercise_ids:
        selected_exercise_id = (
            tracked_exercises[0]["exercise_id"]
        )

    selected_exercise = get_exercise(
        selected_exercise_id
    )

    sessions = build_progress_sessions(
        selected_exercise_id
    )

    has_weight_data = any(
        session["best_weight"] is not None
        for session in sessions
    )

    graph_data = [
        {
            "date": session["short_date"],
            "full_date": session["display_date"],
            "best_weight": session["best_weight"],
            "best_reps": session["best_reps"],
            "volume": session["volume"]
        }
        for session in sessions
    ]

    return render_template(
        "graphs.html",
        tracked_exercises=tracked_exercises,
        selected_exercise=selected_exercise,
        sessions=sessions,
        graph_data=graph_data,
        has_weight_data=has_weight_data
    )