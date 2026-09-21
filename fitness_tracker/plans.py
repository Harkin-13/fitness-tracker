import sqlite3
from datetime import date

from flask import Blueprint, flash, redirect, render_template, request, url_for

from database import get_db


plans_bp = Blueprint(
    "plans",
    __name__
)


def rename_redirect(program_id):
    """Return to the page from which a plan was renamed."""

    if request.form.get("return_to") == "program":
        return redirect(
            url_for(
                "workouts.view_program",
                program_id=program_id
            )
        )

    return redirect(
        url_for("plans.index")
    )


@plans_bp.route("/plans")
def index():
    db = get_db()

    active_program = db.execute(
        """
        SELECT *
        FROM program
        WHERE is_active = 1
        LIMIT 1
        """
    ).fetchone()

    other_programs = db.execute(
        """
        SELECT *
        FROM program
        WHERE is_active = 0
        ORDER BY name COLLATE NOCASE
        """
    ).fetchall()

    return render_template(
        "index.html",
        active_program=active_program,
        other_programs=other_programs
    )


@plans_bp.route(
    "/program/add",
    methods=["POST"]
)
def add_program():
    name = request.form.get(
        "name",
        ""
    ).strip()

    if not name:
        flash(
            "Plan name is required.",
            "error"
        )

        return redirect(
            url_for("plans.index")
        )

    db = get_db()

    duplicate = db.execute(
        """
        SELECT program_id
        FROM program
        WHERE name = ? COLLATE NOCASE
        """,
        (name,)
    ).fetchone()

    if duplicate is not None:
        flash(
            "A plan with that name already exists.",
            "error"
        )

        return redirect(
            url_for("plans.index")
        )

    active_program = db.execute(
        """
        SELECT program_id
        FROM program
        WHERE is_active = 1
        LIMIT 1
        """
    ).fetchone()

    if active_program is None:
        is_active = 1
    else:
        is_active = 0

    try:
        db.execute(
            """
            INSERT INTO program (
                name,
                is_active,
                created_date
            )
            VALUES (?, ?, ?)
            """,
            (
                name,
                is_active,
                date.today().isoformat()
            )
        )

        db.commit()

    except sqlite3.IntegrityError:
        db.rollback()

        flash(
            "The plan could not be created.",
            "error"
        )

        return redirect(
            url_for("plans.index")
        )

    flash(
        "Plan created successfully.",
        "success"
    )

    return redirect(
        url_for("plans.index")
    )


@plans_bp.route(
    "/program/<int:program_id>/set-active",
    methods=["POST"]
)
def set_active_program(program_id):
    db = get_db()

    program = db.execute(
        """
        SELECT *
        FROM program
        WHERE program_id = ?
        """,
        (program_id,)
    ).fetchone()

    if program is None:
        return "Plan not found.", 404

    try:
        db.execute(
            """
            UPDATE program
            SET is_active = 0
            """
        )

        db.execute(
            """
            UPDATE program
            SET is_active = 1
            WHERE program_id = ?
            """,
            (program_id,)
        )

        db.commit()

    except sqlite3.Error:
        db.rollback()

        flash(
            "The active plan could not be changed.",
            "error"
        )

        return redirect(
            url_for("plans.index")
        )

    flash(
        f"{program['name']} is now the active plan.",
        "success"
    )

    return redirect(
        url_for("plans.index")
    )


@plans_bp.route(
    "/program/<int:program_id>/rename",
    methods=["POST"]
)
def rename_program(program_id):
    name = request.form.get(
        "name",
        ""
    ).strip()

    if not name:
        flash(
            "Plan name is required.",
            "error"
        )

        return rename_redirect(
            program_id
        )

    db = get_db()

    program = db.execute(
        """
        SELECT *
        FROM program
        WHERE program_id = ?
        """,
        (program_id,)
    ).fetchone()

    if program is None:
        return "Plan not found.", 404

    duplicate = db.execute(
        """
        SELECT program_id
        FROM program
        WHERE name = ? COLLATE NOCASE
          AND program_id != ?
        """,
        (
            name,
            program_id
        )
    ).fetchone()

    if duplicate is not None:
        flash(
            "A plan with that name already exists.",
            "error"
        )

        return rename_redirect(
            program_id
        )

    try:
        db.execute(
            """
            UPDATE program
            SET name = ?
            WHERE program_id = ?
            """,
            (
                name,
                program_id
            )
        )

        db.commit()

    except sqlite3.IntegrityError:
        db.rollback()

        flash(
            "The plan could not be renamed.",
            "error"
        )

        return rename_redirect(
            program_id
        )

    flash(
        "Plan renamed successfully.",
        "success"
    )

    return rename_redirect(
        program_id
    )


@plans_bp.route(
    "/program/<int:program_id>/delete",
    methods=["POST"]
)
def delete_program(program_id):
    db = get_db()

    program = db.execute(
        """
        SELECT *
        FROM program
        WHERE program_id = ?
        """,
        (program_id,)
    ).fetchone()

    if program is None:
        return "Plan not found.", 404

    was_active = (
        program["is_active"] == 1
    )

    try:
        db.execute(
            """
            DELETE FROM program
            WHERE program_id = ?
            """,
            (program_id,)
        )

        if was_active:
            next_program = db.execute(
                """
                SELECT program_id
                FROM program
                ORDER BY
                    created_date,
                    program_id
                LIMIT 1
                """
            ).fetchone()

            if next_program is not None:
                db.execute(
                    """
                    UPDATE program
                    SET is_active = 1
                    WHERE program_id = ?
                    """,
                    (
                        next_program[
                            "program_id"
                        ],
                    )
                )

        db.commit()

    except sqlite3.Error:
        db.rollback()

        flash(
            "The plan could not be deleted.",
            "error"
        )

        return redirect(
            url_for("plans.index")
        )

    flash(
        f"{program['name']} was deleted.",
        "success"
    )

    return redirect(
        url_for("plans.index")
    )