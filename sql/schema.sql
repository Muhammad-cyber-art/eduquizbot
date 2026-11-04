-- ============================================================
-- EduQuiz Bot — PostgreSQL DDL (minimal production-ready)
-- ============================================================

-- ENUMs
CREATE TYPE user_role   AS ENUM ('teacher', 'student');
CREATE TYPE test_status AS ENUM ('draft', 'open', 'closed');

-- USERS
CREATE TABLE users (
    id          BIGSERIAL PRIMARY KEY,
    tg_user_id  BIGINT      NOT NULL UNIQUE,
    full_name   TEXT,
    role        user_role   NOT NULL,
    lang_code   VARCHAR(5)  NOT NULL DEFAULT 'uz',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- TEACHER INVITE / PIN CODES
CREATE TABLE teacher_invite_codes (
    id          BIGSERIAL PRIMARY KEY,
    code        VARCHAR(32) NOT NULL UNIQUE,
    is_active   BOOLEAN     NOT NULL DEFAULT TRUE,
    expires_at  TIMESTAMPTZ,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- TESTS
CREATE TABLE tests (
    id                BIGSERIAL PRIMARY KEY,
    code              VARCHAR(16)  NOT NULL UNIQUE,
    teacher_id        BIGINT       NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    title             TEXT         NOT NULL,
    subject           TEXT,
    status            test_status  NOT NULL DEFAULT 'draft',
    time_limit_minutes INT,
    attempt_limit     INT          NOT NULL DEFAULT 1,
    shuffle_questions BOOLEAN      NOT NULL DEFAULT FALSE,
    shuffle_options   BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at        TIMESTAMPTZ  NOT NULL DEFAULT now(),
    opened_at         TIMESTAMPTZ,
    closed_at         TIMESTAMPTZ
);

-- QUESTIONS
CREATE TABLE questions (
    id             BIGSERIAL PRIMARY KEY,
    test_id        BIGINT       NOT NULL REFERENCES tests(id) ON DELETE CASCADE,
    position       INT          NOT NULL,
    text           TEXT         NOT NULL,
    image_file_id  TEXT,
    explanation    TEXT,
    created_at     TIMESTAMPTZ  NOT NULL DEFAULT now(),
    UNIQUE (test_id, position)
);

-- OPTIONS (A/B/C/D/E/F/G/H/I/J/K/L/M/N/O/P/Q/R/S/T/U/V/W/X/Y/Z)
CREATE TABLE options (
    id           BIGSERIAL PRIMARY KEY,
    question_id  BIGINT      NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    label        CHAR(1)     NOT NULL CHECK (label IN ('A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z')),
    text         TEXT        NOT NULL,
    is_correct   BOOLEAN     NOT NULL DEFAULT FALSE,
    UNIQUE (question_id, label)
);

-- ATTEMPTS
CREATE TABLE attempts (
    id           BIGSERIAL PRIMARY KEY,
    test_id      BIGINT       NOT NULL REFERENCES tests(id)   ON DELETE CASCADE,
    student_id   BIGINT       NOT NULL REFERENCES users(id)   ON DELETE CASCADE,
    started_at   TIMESTAMPTZ  NOT NULL DEFAULT now(),
    deadline_at  TIMESTAMPTZ,
    finished_at  TIMESTAMPTZ,
    score        INT,
    max_score    INT,
    percent      NUMERIC(5,2),
    status       VARCHAR(16)  NOT NULL DEFAULT 'in_progress',
    -- status values: in_progress | finished | expired
    UNIQUE (test_id, student_id, started_at)
);

-- ANSWERS
CREATE TABLE answers (
    id              BIGSERIAL PRIMARY KEY,
    attempt_id      BIGINT      NOT NULL REFERENCES attempts(id)  ON DELETE CASCADE,
    question_id     BIGINT      NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    selected_label  CHAR(1)     NOT NULL CHECK (selected_label IN ('A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z')),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (attempt_id, question_id)
);

-- ============================================================
-- INDEXES (fast lookups & reporting)
-- ============================================================
CREATE INDEX idx_tests_teacher          ON tests(teacher_id);
CREATE INDEX idx_tests_status           ON tests(status);
CREATE INDEX idx_questions_test         ON questions(test_id);
CREATE INDEX idx_attempts_test_student  ON attempts(test_id, student_id);
CREATE INDEX idx_attempts_test_finished ON attempts(test_id, finished_at);
CREATE INDEX idx_answers_attempt        ON answers(attempt_id);

-- ============================================================
-- CONSISTENCY RULES (DB-level)
-- ============================================================

-- Ensure only one correct option per question
CREATE UNIQUE INDEX idx_options_correct
    ON options(question_id)
    WHERE is_correct = TRUE;

-- Prevent answers to questions not belonging to the attempt's test
-- (application-level check recommended; trigger below is optional)
-- CREATE OR REPLACE FUNCTION check_answer_question_belongs_to_test()
-- RETURNS TRIGGER AS $$
-- BEGIN
--     IF NOT EXISTS (
--         SELECT 1 FROM questions q
--         JOIN attempts a ON a.test_id = q.test_id
--         WHERE q.id = NEW.question_id AND a.id = NEW.attempt_id
--     ) THEN
--         RAISE EXCEPTION 'Question does not belong to the attempt test';
--     END IF;
--     RETURN NEW;
-- END;
-- $$ LANGUAGE plpgsql;
-- CREATE TRIGGER trg_check_answer_question
--     BEFORE INSERT ON answers
--     FOR EACH ROW EXECUTE FUNCTION check_answer_question_belongs_to_test();
