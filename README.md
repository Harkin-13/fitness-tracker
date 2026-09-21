# Fitness Tracker

A beginner-focused full-stack web application for creating training plans, recording completed workouts and reviewing exercise progress over time.

The application includes:

- a starter exercise library;
- an example Push/Pull/Legs training plan;
- no fabricated workout history.

Users can create their own plans, workouts and exercises in addition to the supplied examples.

## Main Features

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
- Responsive browser interface

## Technologies

- Python
- Flask
- SQLite
- pytest
- HTML
- Jinja
- CSS
- JavaScript
- SVG

## Requirements

- Python 3.10 or later
- Dependencies listed in `requirements.txt`

## Installation

From the project directory, install the required dependencies:

```bash
python -m pip install -r requirements.txt
```

## Database Setup

Create the database and add the starter content:

```bash
flask --app app init-db
flask --app app seed-data
```

This creates:

- the database tables;
- 14 starter exercises;
- an example Push/Pull/Legs plan;
- no artificial workout history.

The seed command is safe to run more than once and does not create duplicate starter data.

## Running the Application

Start the application with:

```bash
python app.py
```

Then open:

```text
http://127.0.0.1:5000
```

The application uses Flask's development server and is intended to be run locally.

## Automated Tests

Run the complete automated test suite with:

```bash
python -m pytest -q
```

The project includes 37 automated tests covering:

- plans;
- workouts;
- exercises;
- validation;
- progress calculations;
- workout and exercise ordering;
- starter data;
- database behaviour.

## Recreating the Database

To reset the application to its default state, delete the existing database and recreate it.

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

## Project Structure

```text
fitness_tracker/
├── static/
├── templates/
├── tests/
├── app.py
├── database.py
├── exercises.py
├── plans.py
├── progress.py
├── workouts.py
├── schema.sql
├── requirements.txt
├── README.md
├── .gitignore
└── LICENSE
```

## Project Background

This project was developed as the final software project for a BSc (Hons) Computing & IT degree with The Open University.

The application was designed around a deliberately small, beginner-focused scope, with emphasis placed on maintainability, relational database design, automated testing, usability and accessibility.

## Licence

This project is released under the MIT Licence.
