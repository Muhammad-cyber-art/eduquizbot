"""FSM state groups for Teacher, Student, and Common flows."""

from aiogram.fsm.state import State, StatesGroup


# ── Common (language + role selection) ──────────────────────
class CommonSG(StatesGroup):
    language = State()
    role = State()


# ── Teacher flow ────────────────────────────────────────────
class TeacherSG(StatesGroup):
    pin = State()
    # Access request flow
    request_name = State()
    request_phone = State()
    # Test creation
    newtest_title = State()
    upload_file = State()
    ask_answers_file = State()  # Ask if teacher has separate answers file
    upload_answers = State()    # Waiting for answers file upload
    review_questions = State()
    edit_question = State()
    mark_correct = State()    # Teacher picks correct answer for each question
    settings_time = State()
    settings_attempt_limit = State()
    settings_input = State()  # Generic settings input (time/attempts)
    manage = State()


# ── Student flow ────────────────────────────────────────────
class StudentSG(StatesGroup):
    enter_code = State()
    confirm_start = State()
    in_quiz = State()
