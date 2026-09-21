CREATE TABLE IF NOT EXISTS program (
    program_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL COLLATE NOCASE,
    is_active INTEGER NOT NULL DEFAULT 0,
    created_date TEXT NOT NULL,

    CHECK (is_active IN (0, 1)),

    UNIQUE (name)
);


CREATE TABLE IF NOT EXISTS workout (
    workout_id INTEGER PRIMARY KEY AUTOINCREMENT,
    program_id INTEGER NOT NULL,
    name TEXT NOT NULL COLLATE NOCASE,
    workout_order INTEGER NOT NULL DEFAULT 1,
    created_date TEXT NOT NULL,

    FOREIGN KEY (program_id)
        REFERENCES program(program_id)
        ON DELETE CASCADE,

    UNIQUE (program_id, name),

    CHECK (workout_order > 0)
);


CREATE TABLE IF NOT EXISTS exercise (
    exercise_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL COLLATE NOCASE,
    primary_muscle TEXT NOT NULL,
    equipment TEXT NOT NULL COLLATE NOCASE,
    is_custom INTEGER NOT NULL DEFAULT 0,

    CHECK (is_custom IN (0, 1)),

    UNIQUE (name, equipment)
);


CREATE TABLE IF NOT EXISTS workout_exercise (
    workout_exercise_id INTEGER PRIMARY KEY AUTOINCREMENT,
    workout_id INTEGER NOT NULL,
    exercise_id INTEGER NOT NULL,
    exercise_order INTEGER NOT NULL DEFAULT 1,
    target_sets INTEGER NOT NULL DEFAULT 3,
    target_reps INTEGER NOT NULL DEFAULT 10,

    FOREIGN KEY (workout_id)
        REFERENCES workout(workout_id)
        ON DELETE CASCADE,

    FOREIGN KEY (exercise_id)
        REFERENCES exercise(exercise_id)
        ON DELETE CASCADE,

    UNIQUE (
        workout_id,
        exercise_id
    ),

    CHECK (
        exercise_order > 0
    ),

    CHECK (
        target_sets BETWEEN 1 AND 20
    ),

    CHECK (
        target_reps BETWEEN 1 AND 100
    )
);


CREATE TABLE IF NOT EXISTS workout_log (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    workout_id INTEGER,
    workout_name TEXT NOT NULL,
    log_date TEXT NOT NULL,

    FOREIGN KEY (workout_id)
        REFERENCES workout(workout_id)
        ON DELETE SET NULL
);


CREATE TABLE IF NOT EXISTS exercise_set (
    set_id INTEGER PRIMARY KEY AUTOINCREMENT,
    log_id INTEGER NOT NULL,
    exercise_id INTEGER NOT NULL,
    set_number INTEGER NOT NULL,
    weight REAL,
    reps INTEGER NOT NULL,

    FOREIGN KEY (log_id)
        REFERENCES workout_log(log_id)
        ON DELETE CASCADE,

    FOREIGN KEY (exercise_id)
        REFERENCES exercise(exercise_id)
        ON DELETE CASCADE,

    UNIQUE (
        log_id,
        exercise_id,
        set_number
    ),

    CHECK (
        set_number > 0
    ),

    CHECK (
        weight IS NULL
        OR weight BETWEEN 0 AND 1000
    ),

    CHECK (
        reps BETWEEN 1 AND 100
    )
);


CREATE UNIQUE INDEX IF NOT EXISTS one_active_program
ON program(is_active)
WHERE is_active = 1;


CREATE INDEX IF NOT EXISTS workout_program_index
ON workout(
    program_id,
    workout_order
);


CREATE INDEX IF NOT EXISTS workout_exercise_workout_index
ON workout_exercise(
    workout_id,
    exercise_order
);


CREATE INDEX IF NOT EXISTS exercise_set_exercise_index
ON exercise_set(
    exercise_id,
    log_id
);


CREATE INDEX IF NOT EXISTS workout_log_date_index
ON workout_log(
    log_date
);