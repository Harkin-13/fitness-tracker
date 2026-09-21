import os
import secrets
from pathlib import Path

from flask import Flask, render_template

from database import init_app as init_database
from exercises import exercises_bp
from plans import plans_bp
from progress import progress_bp
from workouts import workouts_bp


BASE_DIR = Path(__file__).resolve().parent


def create_app(test_config=None):
    """Create and configure the Flask application."""

    app = Flask(__name__)

    app.config.from_mapping(
        SECRET_KEY=os.environ.get(
            "FITNESS_TRACKER_SECRET_KEY",
            secrets.token_hex(32)
        ),
        DATABASE=str(
            BASE_DIR / "fitness_tracker.db"
        )
    )

    if test_config is not None:
        app.config.update(
            test_config
        )

    init_database(app)

    app.register_blueprint(
        plans_bp
    )

    app.register_blueprint(
        exercises_bp
    )

    app.register_blueprint(
        workouts_bp
    )

    app.register_blueprint(
        progress_bp
    )

    @app.route("/")
    def home():
        return render_template(
            "home.html"
        )

    return app


app = create_app()


if __name__ == "__main__":
    app.run()