# Beginner Fitness Tracker

A beginner-focused web application for creating training plans,
recording completed workouts and reviewing exercise progress over time.

The submitted database contains:

- a starter exercise library;
- an example Push/Pull/Legs training plan;
- no fabricated workout history.

Users can create their own plans, workouts and exercises in addition to
the supplied examples.

## Requirements

- Python 3.10 or later
- Dependencies listed in `requirements.txt`

## Installation

From the project directory:

```bash
python -m pip install -r requirements.txt
```

## Running the application

```bash
python app.py
```

Then open:

```text
http://127.0.0.1:5000
```

The application uses Flask's development server and is intended to be
run locally for demonstration and assessment.

## Automated tests

Run the complete automated test suite with:

```bash
python -m pytest -q
```

## Recreating the supplied database

The application database can be recreated from `schema.sql` and the
included seed command.

### Windows PowerShell

```powershell
Remove-Item .\fitness_tracker.db -ErrorAction SilentlyContinue
flask --app app init-db
flask --app app seed-data
```

### macOS / Linux

```bash
rm -f fitness_tracker.db
flask --app app init-db
flask --app app seed-data
```

This creates the database tables, the starter exercise library and the
example Push/Pull/Legs plan. It does not create artificial workout
history.

## Main features

- Create, rename, activate and delete training plans
- Create and reorder workouts
- Build workouts from a starter or custom exercise library
- Reorder exercises within workouts
- Configure target sets and repetitions
- Record completed sets, repetitions and optional weight
- View previous exercise performance while training
- Preserve exercise history when plans or workouts are deleted
- View progress using weight, volume and repetition graphs
- Review recorded sessions in a supporting data table
- Keyboard-accessible workout navigation and ordering controls