"""Attempt & answer service — manages student quiz sessions."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import Answer, Attempt, Option, Question, Test, User


async def create_attempt(
    session: AsyncSession,
    test_id: int,
    student_id: int,
) -> Attempt:
    """Create a new attempt for a student on a test."""
    test = await session.get(Test, test_id)
    deadline = None
    if test and test.time_limit_minutes:
        deadline = datetime.now(timezone.utc) + timedelta(minutes=test.time_limit_minutes)

    attempt = Attempt(
        test_id=test_id,
        student_id=student_id,
        deadline_at=deadline,
        status="in_progress",
    )
    session.add(attempt)
    await session.commit()
    await session.refresh(attempt)
    return attempt


async def get_active_attempt(
    session: AsyncSession,
    test_id: int,
    student_id: int,
) -> Attempt | None:
    stmt = (
        select(Attempt)
        .where(
            Attempt.test_id == test_id,
            Attempt.student_id == student_id,
            Attempt.status == "in_progress",
        )
        .order_by(Attempt.started_at.desc())
        .limit(1)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def count_attempts(
    session: AsyncSession,
    test_id: int,
    student_id: int,
) -> int:
    stmt = (
        select(func.count())
        .select_from(Attempt)
        .where(Attempt.test_id == test_id, Attempt.student_id == student_id)
    )
    result = await session.execute(stmt)
    return result.scalar_one()


async def save_answer(
    session: AsyncSession,
    attempt_id: int,
    question_id: int,
    selected_label: str,
) -> Answer:
    """Save or update a student's answer for a question."""
    stmt = select(Answer).where(
        Answer.attempt_id == attempt_id,
        Answer.question_id == question_id,
    )
    result = await session.execute(stmt)
    existing = result.scalar_one_or_none()
    if existing:
        existing.selected_label = selected_label
        await session.commit()
        return existing

    answer = Answer(
        attempt_id=attempt_id,
        question_id=question_id,
        selected_label=selected_label,
    )
    session.add(answer)
    await session.commit()
    return answer


async def finish_attempt(
    session: AsyncSession,
    attempt_id: int,
    *,
    expired: bool = False,
) -> Attempt:
    """Grade the attempt and mark it as finished/expired."""
    # Use session.execute(select()) instead of session.get() to bypass
    # identity map cache and force fresh load of relationships
    stmt = (
        select(Attempt)
        .where(Attempt.id == attempt_id)
        .options(selectinload(Attempt.answers))
    )
    result = await session.execute(stmt)
    attempt = result.scalar_one_or_none()
    if attempt is None:
        raise ValueError(f"Attempt {attempt_id} not found")

    # Load correct options using execute(select()) for fresh data
    test_stmt = (
        select(Test)
        .where(Test.id == attempt.test_id)
        .options(selectinload(Test.questions).selectinload(Question.options))
    )
    test_result = await session.execute(test_stmt)
    test = test_result.scalar_one_or_none()

    correct_map: dict[int, str] = {}
    for q in test.questions:
        for opt in q.options:
            if opt.is_correct:
                correct_map[q.id] = opt.label

    score = 0
    max_score = len(correct_map)
    for ans in attempt.answers:
        if correct_map.get(ans.question_id) == ans.selected_label:
            score += 1

    attempt.score = score
    attempt.max_score = max_score
    attempt.percent = round(score / max_score * 100, 2) if max_score else 0
    attempt.finished_at = datetime.now(timezone.utc)
    attempt.status = "expired" if expired else "finished"
    await session.commit()
    # No refresh needed — expire_on_commit=False, all attrs already set
    return attempt


async def get_attempt_by_id(
    session: AsyncSession,
    attempt_id: int,
) -> Attempt | None:
    """Quick fetch attempt by ID (no eager loading)."""
    return await session.get(Attempt, attempt_id)


async def get_attempt_result(
    session: AsyncSession,
    attempt_id: int,
) -> Attempt | None:
    stmt = (
        select(Attempt)
        .where(Attempt.id == attempt_id)
        .options(selectinload(Attempt.answers))
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_test_results(
    session: AsyncSession,
    test_id: int,
) -> list[Attempt]:
    """Get all attempts for a test with student info (ordered by newest first)."""
    stmt = (
        select(Attempt)
        .where(Attempt.test_id == test_id)
        .options(selectinload(Attempt.student))
        .order_by(Attempt.started_at.desc())
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())
