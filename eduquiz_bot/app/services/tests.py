"""Test CRUD service."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import Option, Question, Test, TestStatus
from app.utils.codes import generate_test_code


async def create_test(
    session: AsyncSession,
    teacher_id: int,
    title: str,
    subject: str | None = None,
) -> Test:
    """Create a new test in draft status with a unique code."""
    test = Test(
        code=await generate_test_code(session),
        teacher_id=teacher_id,
        title=title,
        subject=subject,
        status=TestStatus.DRAFT,
    )
    session.add(test)
    await session.flush()
    return test


async def add_question(
    session: AsyncSession,
    test_id: int,
    position: int,
    text: str,
    options: list[dict],
    image_file_id: str | None = None,
) -> Question:
    """Add a question with A/B/C/D options to a test."""
    q = Question(
        test_id=test_id,
        position=position,
        text=text,
        image_file_id=image_file_id,
    )
    session.add(q)
    await session.flush()

    for opt in options:
        session.add(
            Option(
                question_id=q.id,
                label=opt["label"],
                text=opt["text"],
                is_correct=opt.get("is_correct", False),
            )
        )
    await session.flush()
    return q


async def get_test_by_code(session: AsyncSession, code: str) -> Test | None:
    stmt = (
        select(Test)
        .where(Test.code == code)
        .options(selectinload(Test.questions).selectinload(Question.options))
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_test_full(session: AsyncSession, test_id: int) -> Test | None:
    stmt = (
        select(Test)
        .where(Test.id == test_id)
        .options(selectinload(Test.questions).selectinload(Question.options))
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def set_test_status(
    session: AsyncSession,
    test_id: int,
    status: TestStatus,
) -> Test | None:
    test = await get_test_full(session, test_id)
    if test is None:
        return None
    test.status = status
    now = datetime.now(timezone.utc)
    if status == TestStatus.OPEN:
        test.opened_at = now
    elif status == TestStatus.CLOSED:
        test.closed_at = now
    await session.flush()
    return test


async def list_teacher_tests(session: AsyncSession, teacher_id: int) -> list[Test]:
    stmt = (
        select(Test)
        .where(Test.teacher_id == teacher_id)
        .order_by(Test.created_at.desc())
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def update_test_settings(
    session: AsyncSession,
    test_id: int,
    *,
    time_limit_minutes: int | None = None,
    attempt_limit: int | None = None,
    shuffle_questions: bool | None = None,
    shuffle_options: bool | None = None,
) -> Test | None:
    test = await get_test_full(session, test_id)
    if test is None:
        return None
    if time_limit_minutes is not None:
        test.time_limit_minutes = time_limit_minutes
    if attempt_limit is not None:
        test.attempt_limit = attempt_limit
    if shuffle_questions is not None:
        test.shuffle_questions = shuffle_questions
    if shuffle_options is not None:
        test.shuffle_options = shuffle_options
    await session.flush()
    return test


async def set_correct_answer(
    session: AsyncSession,
    question_id: int,
    correct_label: str,
) -> None:
    """Mark the option with the given label as correct for a question."""
    stmt = select(Option).where(Option.question_id == question_id)
    result = await session.execute(stmt)
    options = result.scalars().all()
    for opt in options:
        opt.is_correct = (opt.label == correct_label)
    await session.flush()


async def set_question_image(
    session: AsyncSession,
    question_id: int,
    image_file_id: str,
) -> None:
    """Set the Telegram file_id for a question's image."""
    stmt = select(Question).where(Question.id == question_id)
    result = await session.execute(stmt)
    q = result.scalar_one_or_none()
    if q:
        q.image_file_id = image_file_id
        await session.flush()


async def get_question_with_options(
    session: AsyncSession,
    question_id: int,
) -> Question | None:
    """Fetch a single question with its options."""
    stmt = (
        select(Question)
        .where(Question.id == question_id)
        .options(selectinload(Question.options))
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()
