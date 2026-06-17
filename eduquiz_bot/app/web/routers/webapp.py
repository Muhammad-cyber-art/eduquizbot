"""Telegram WebApp APIs — teacher/student dashboards and AI quiz generator.

Key design decisions:
- get_tg_user_id() validates Telegram InitData cryptographically.
- AI generate endpoint uses explicit session management so no DB connection
  is held during the (potentially 30-second) Gemini API call.
- Teacher/student stats use SQL-level aggregation (GROUP BY, AVG, COUNT)
  instead of loading all rows into Python memory.
"""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import logging
import random
import string
from datetime import datetime, timedelta, timezone
from typing import Annotated
from urllib.parse import parse_qsl

import aiohttp
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.db.models import Attempt, Option, Question, Test, TestStatus, User, UserRole
from app.db.session import async_session, get_async_session
from app.utils.codes import generate_test_code

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Telegram InitData authentication ─────────────────────────

async def get_tg_user_id(
    x_tg_init_data: str = Header(..., alias="X-TG-Init-Data"),
) -> int:
    """Validate Telegram WebApp InitData and return the authenticated user ID.

    DEV bypass (DEV_<user_id>) is only allowed in development mode.
    """
    # DEV bypass — disabled in production
    if x_tg_init_data.startswith("DEV_"):
        if settings.is_production:
            raise HTTPException(status_code=401, detail="DEV mode disabled in production")
        try:
            return int(x_tg_init_data.replace("DEV_", "", 1))
        except ValueError:
            raise HTTPException(status_code=401, detail="Invalid DEV user id")

    try:
        parsed_data = dict(parse_qsl(x_tg_init_data, keep_blank_values=True))
        if "hash" not in parsed_data:
            raise ValueError("No hash field in init data")

        hash_value = parsed_data.pop("hash")
        data_check_string = "\n".join(
            f"{k}={v}" for k, v in sorted(parsed_data.items())
        )

        secret_key = hmac.new(
            b"WebAppData",
            settings.BOT_TOKEN.encode(),
            hashlib.sha256,
        ).digest()
        calculated_hash = hmac.new(
            secret_key,
            data_check_string.encode(),
            hashlib.sha256,
        ).hexdigest()

        # Constant-time comparison to prevent timing attacks
        if not hmac.compare_digest(calculated_hash, hash_value):
            raise ValueError("Hash mismatch")

        # Reject stale init data (older than 24 hours)
        if "auth_date" in parsed_data:
            auth_ts = int(parsed_data["auth_date"])
            age_seconds = int(datetime.now(timezone.utc).timestamp()) - auth_ts
            if age_seconds > 86400:
                raise ValueError(f"Init data expired ({age_seconds}s old)")

        if "user" in parsed_data:
            user_data = json.loads(parsed_data["user"])
            return int(user_data["id"])

        raise ValueError("No user field in init data")

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=401, detail=f"Unauthorized: {exc}") from exc


# ── Pydantic models ───────────────────────────────────────────

class AIGenerateRequest(BaseModel):
    topic: str
    num_questions: int
    difficulty: str
    option_count: int


class AIGenerateResponse(BaseModel):
    test_id: int
    title: str
    code: str
    questions_count: int
    difficulty: str


class UpdateTestStatusRequest(BaseModel):
    status: str


# ── User role endpoint ────────────────────────────────────────

@router.get("/user/role")
async def get_user_role(
    tg_user_id: int = Depends(get_tg_user_id),
    session: AsyncSession = Depends(get_async_session),
):
    stmt = select(User).where(User.tg_user_id == tg_user_id)
    user = (await session.execute(stmt)).scalar_one_or_none()
    if not user:
        return {"role": None}
    return {"role": user.role.value if hasattr(user.role, "value") else str(user.role)}


# ── Teacher Stats ─────────────────────────────────────────────

@router.get("/teacher/stats")
async def get_teacher_stats(
    tg_user_id: int = Depends(get_tg_user_id),
    session: AsyncSession = Depends(get_async_session),
):
    """Return aggregated teacher dashboard statistics.

    All aggregation is done at the database level (no Python-side filtering loops).
    """
    # 1. Resolve teacher
    teacher = (
        await session.execute(
            select(User).where(User.tg_user_id == tg_user_id, User.role == UserRole.TEACHER)
        )
    ).scalar_one_or_none()
    if not teacher:
        raise HTTPException(status_code=404, detail="O'qituvchi topilmadi.")

    finished_statuses = ["finished", "expired"]

    # 2. Aggregate attempt stats in a single DB query
    stats_row = (
        await session.execute(
            select(
                func.count(Attempt.id).label("total"),
                func.sum(
                    case((Attempt.percent >= 50, 1), else_=0)
                ).label("passed"),
            )
            .join(Test, Attempt.test_id == Test.id)
            .where(
                Test.teacher_id == teacher.id,
                Attempt.status.in_(finished_statuses),
            )
        )
    ).one()
    total_attempts_count = stats_row.total or 0
    passed_count = stats_row.passed or 0
    pass_rate = (
        round(passed_count / total_attempts_count * 100, 1)
        if total_attempts_count > 0
        else 0.0
    )

    # 3. Top 3 performers (DB-sorted, no Python sort)
    top_rows = (
        await session.execute(
            select(User.full_name, Test.title, Attempt.percent, Attempt.score, Attempt.max_score, Attempt.finished_at)
            .join(Test, Attempt.test_id == Test.id)
            .join(User, Attempt.student_id == User.id)
            .where(
                Test.teacher_id == teacher.id,
                Attempt.status.in_(finished_statuses),
            )
            .order_by(Attempt.percent.desc())
            .limit(3)
        )
    ).all()

    top_attempts = [
        {
            "student_name": row.full_name or "Noma'lum o'quvchi",
            "test_title": row.title,
            "percent": float(row.percent or 0),
            "score": row.score,
            "max_score": row.max_score,
            "finished_at": row.finished_at.strftime("%Y-%m-%d %H:%M") if row.finished_at else "",
        }
        for row in top_rows
    ]

    # 4. Bottom 3 performers (DB-sorted ascending)
    bottom_rows = (
        await session.execute(
            select(User.full_name, Test.title, Attempt.percent, Attempt.score, Attempt.max_score, Attempt.finished_at)
            .join(Test, Attempt.test_id == Test.id)
            .join(User, Attempt.student_id == User.id)
            .where(
                Test.teacher_id == teacher.id,
                Attempt.status.in_(finished_statuses),
            )
            .order_by(Attempt.percent.asc())
            .limit(3)
        )
    ).all()

    bottom_attempts = [
        {
            "student_name": row.full_name or "Noma'lum o'quvchi",
            "test_title": row.title,
            "percent": float(row.percent or 0),
            "score": row.score,
            "max_score": row.max_score,
            "finished_at": row.finished_at.strftime("%Y-%m-%d %H:%M") if row.finished_at else "",
        }
        for row in bottom_rows
    ]

    # 5. Tests with per-test aggregated stats (LEFT JOIN to include tests with 0 attempts)
    tests_rows = (
        await session.execute(
            select(
                Test.id,
                Test.title,
                Test.code,
                Test.difficulty,
                Test.status,
                Test.created_at,
                func.count(Attempt.id).label("attempts_count"),
                func.coalesce(func.avg(Attempt.percent), 0).label("average_score"),
            )
            .outerjoin(
                Attempt,
                (Attempt.test_id == Test.id) & (Attempt.status.in_(finished_statuses)),
            )
            .where(Test.teacher_id == teacher.id)
            .group_by(Test.id)
            .order_by(Test.created_at.desc())
        )
    ).all()

    tests_list = [
        {
            "id": row.id,
            "title": row.title,
            "code": row.code,
            "difficulty": row.difficulty,
            "status": row.status.value if hasattr(row.status, "value") else str(row.status),
            "attempts_count": row.attempts_count,
            "average_score": round(float(row.average_score or 0), 2),
            "created_at": row.created_at.strftime("%Y-%m-%d") if row.created_at else "",
        }
        for row in tests_rows
    ]

    # 6. Growth trends: students with >= 2 finished attempts (limited query)
    # Load only needed fields for top 20 students by attempt count
    growth_student_rows = (
        await session.execute(
            select(
                User.id,
                User.full_name,
                Attempt.percent,
                Attempt.finished_at,
                Test.title,
            )
            .join(Test, Attempt.test_id == Test.id)
            .join(User, Attempt.student_id == User.id)
            .where(
                Test.teacher_id == teacher.id,
                Attempt.status.in_(finished_statuses),
                Attempt.finished_at.isnot(None),
            )
            .order_by(User.id, Attempt.finished_at.asc())
        )
    ).all()

    student_map: dict = {}
    for row in growth_student_rows:
        if row.id not in student_map:
            student_map[row.id] = {
                "student_name": row.full_name or "Noma'lum o'quvchi",
                "attempts": [],
            }
        student_map[row.id]["attempts"].append({
            "test_title": row.title,
            "percent": float(row.percent or 0),
            "date": row.finished_at.strftime("%Y-%m-%d") if row.finished_at else "",
        })

    growth_trends = [
        s for s in student_map.values() if len(s["attempts"]) >= 2
    ][:10]

    return {
        "teacher_name": teacher.full_name,
        "ai_queries_limit": teacher.ai_queries_limit,
        "ai_queries_used": teacher.ai_queries_used,
        "total_tests": len(tests_list),
        "total_attempts": total_attempts_count,
        "pass_rate": pass_rate,
        "top_attempts": top_attempts,
        "bottom_attempts": bottom_attempts,
        "growth_trends": growth_trends,
        "tests": tests_list,
    }


# ── Teacher Test Details ──────────────────────────────────────

@router.get("/teacher/tests/{test_id}")
async def get_test_details(
    test_id: int,
    tg_user_id: int = Depends(get_tg_user_id),
    session: AsyncSession = Depends(get_async_session),
):
    stmt = select(Test).where(Test.id == test_id).options(
        selectinload(Test.teacher),
        selectinload(Test.attempts).selectinload(Attempt.student),
    )
    test = (await session.execute(stmt)).scalar_one_or_none()

    if not test or test.teacher.tg_user_id != tg_user_id:
        raise HTTPException(status_code=404, detail="Test topilmadi yoki ruxsat yo'q")

    participants = [
        {
            "student_name": a.student.full_name if a.student and a.student.full_name else "Noma'lum",
            "score": a.score,
            "max_score": a.max_score,
            "percent": float(a.percent or 0),
            "finished_at": a.finished_at.strftime("%Y-%m-%d %H:%M") if a.finished_at else "",
        }
        for a in test.attempts
        if a.status in ("finished", "expired")
    ]
    participants.sort(key=lambda x: x["percent"], reverse=True)

    return {
        "id": test.id,
        "title": test.title,
        "code": test.code,
        "difficulty": test.difficulty,
        "status": test.status.value if hasattr(test.status, "value") else str(test.status),
        "created_at": test.created_at.strftime("%Y-%m-%d %H:%M") if test.created_at else "",
        "participants": participants,
    }


# ── Teacher Test Status Update ────────────────────────────────

@router.put("/teacher/tests/{test_id}/status")
async def update_test_status(
    test_id: int,
    req: UpdateTestStatusRequest,
    tg_user_id: int = Depends(get_tg_user_id),
    session: AsyncSession = Depends(get_async_session),
):
    stmt = select(Test).where(Test.id == test_id).options(selectinload(Test.teacher))
    test = (await session.execute(stmt)).scalar_one_or_none()

    if not test or test.teacher.tg_user_id != tg_user_id:
        raise HTTPException(status_code=404, detail="Test topilmadi yoki ruxsat yo'q")

    try:
        new_status = req.status.upper()
        if hasattr(TestStatus, new_status):
            test.status = getattr(TestStatus, new_status)
        else:
            raise ValueError(f"Unknown status: {req.status}")
        await session.commit()
        return {"success": True, "status": req.status}
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=str(e)) from e


# ── Student Stats ─────────────────────────────────────────────

@router.get("/student/stats")
async def get_student_stats(
    tg_user_id: int = Depends(get_tg_user_id),
    session: AsyncSession = Depends(get_async_session),
):
    student = (
        await session.execute(
            select(User).where(User.tg_user_id == tg_user_id, User.role == UserRole.STUDENT)
        )
    ).scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="O'quvchi topilmadi.")

    finished_statuses = ["finished", "expired"]

    # Aggregate student-level stats in one query
    stats_row = (
        await session.execute(
            select(
                func.count(Attempt.id).label("attempts_count"),
                func.coalesce(func.sum(Attempt.xp_earned), 0).label("total_xp"),
                func.coalesce(func.avg(Attempt.percent), 0).label("average_score"),
            )
            .where(
                Attempt.student_id == student.id,
                Attempt.status.in_(finished_statuses),
            )
        )
    ).one()
    total_xp = stats_row.total_xp or 0
    attempts_count = stats_row.attempts_count or 0
    average_score = round(float(stats_row.average_score or 0), 1)

    # Weekly & Monthly cutoffs
    now = datetime.now(timezone.utc)
    monday = (now - timedelta(days=now.weekday())).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    first_day_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Weekly leaderboard
    weekly_rows = (
        await session.execute(
            select(
                User.id,
                User.full_name,
                func.sum(Attempt.xp_earned).label("weekly_xp"),
            )
            .join(Attempt, Attempt.student_id == User.id)
            .where(
                Attempt.status.in_(finished_statuses),
                Attempt.finished_at >= monday,
            )
            .group_by(User.id, User.full_name)
            .order_by(func.sum(Attempt.xp_earned).desc())
            .limit(10)
        )
    ).all()

    weekly_leaderboard = []
    student_weekly_rank = None
    for idx, row in enumerate(weekly_rows, 1):
        weekly_leaderboard.append({
            "rank": idx,
            "student_name": row.full_name or "Noma'lum o'quvchi",
            "xp": row.weekly_xp,
        })
        if row.id == student.id:
            student_weekly_rank = idx

    # Monthly leaderboard
    monthly_rows = (
        await session.execute(
            select(
                User.id,
                User.full_name,
                func.sum(Attempt.xp_earned).label("monthly_xp"),
            )
            .join(Attempt, Attempt.student_id == User.id)
            .where(
                Attempt.status.in_(finished_statuses),
                Attempt.finished_at >= first_day_of_month,
            )
            .group_by(User.id, User.full_name)
            .order_by(func.sum(Attempt.xp_earned).desc())
            .limit(10)
        )
    ).all()

    monthly_leaderboard = []
    student_monthly_rank = None
    for idx, row in enumerate(monthly_rows, 1):
        monthly_leaderboard.append({
            "rank": idx,
            "student_name": row.full_name or "Noma'lum o'quvchi",
            "xp": row.monthly_xp,
        })
        if row.id == student.id:
            student_monthly_rank = idx

    # Attempt history (most recent 50)
    history_rows = (
        await session.execute(
            select(
                Test.title,
                Test.code,
                Test.difficulty,
                Attempt.score,
                Attempt.max_score,
                Attempt.percent,
                Attempt.xp_earned,
                Attempt.status,
                Attempt.finished_at,
            )
            .join(Test, Attempt.test_id == Test.id)
            .where(
                Attempt.student_id == student.id,
                Attempt.status.in_(finished_statuses),
            )
            .order_by(Attempt.finished_at.desc())
            .limit(50)
        )
    ).all()

    attempts_history = [
        {
            "test_title": row.title,
            "test_code": row.code,
            "difficulty": row.difficulty,
            "score": row.score,
            "max_score": row.max_score,
            "percent": float(row.percent or 0),
            "xp_earned": row.xp_earned,
            "status": row.status,
            "date": row.finished_at.strftime("%Y-%m-%d %H:%M") if row.finished_at else "",
        }
        for row in history_rows
    ]

    # Progress trends (cumulative XP over time, oldest-first)
    cumulative_xp = 0
    progress_trends = []
    for row in reversed(history_rows):
        cumulative_xp += row.xp_earned
        progress_trends.append({
            "date": row.finished_at.strftime("%Y-%m-%d") if row.finished_at else "",
            "xp_gained": row.xp_earned,
            "cumulative_xp": cumulative_xp,
            "test_title": row.title,
        })

    return {
        "student_name": student.full_name,
        "total_xp": total_xp,
        "attempts_count": attempts_count,
        "average_score": average_score,
        "weekly_rank": student_weekly_rank,
        "monthly_rank": student_monthly_rank,
        "weekly_leaderboard": weekly_leaderboard,
        "monthly_leaderboard": monthly_leaderboard,
        "attempts": attempts_history,
        "progress_trends": progress_trends,
    }


# ── AI Quiz Generator ─────────────────────────────────────────

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1.5, min=2, max=10),
    retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError, ValueError)),
    reraise=True,
)
async def _call_gemini_api(req: AIGenerateRequest) -> dict | None:
    """Call the Gemini API to generate quiz questions with automatic retries.

    Returns parsed quiz dict. Raises an exception if all retries fail.
    No database connection is held during this call.
    """
    if not settings.GEMINI_API_KEY:
        logger.warning("No GEMINI_API_KEY set.")
        return None

    prompt = (
        f"Siz test yaratuvchi professional yordamchisiz. Quyidagi mavzu bo'yicha mukammal va to'g'ri test yaratib bering:\n"
        f"Mavzu: {req.topic}\n"
        f"Savollar soni: {req.num_questions}\n"
        f"Qiyinchilik darajasi: {req.difficulty} (easy, medium, hard)\n"
        f"Variantlar soni: {req.option_count} ta (A, B, C... va hokazo formatda)\n\n"
        f"Siz faqat va faqat quyidagi tuzilishdagi JSON formatida javob berishingiz shart. "
        f"Boshqa hech qanday izoh yoki tushuntirish yozmang:\n"
        f'{{"title": "Mavzuga mos sarlavha", "questions": [{{'
        f'"text": "Savol matni?", "options": ['
        f'{{"label": "A", "text": "Variant A", "is_correct": true}}, '
        f'{{"label": "B", "text": "Variant B", "is_correct": false}}'
        f"]}}]}}\n"
        f"Har bir savol uchun faqat bitta variant to'g'ri bo'lishini (is_correct: true) ta'minlang."
    )

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json"},
    }
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-2.0-flash:generateContent?key={settings.GEMINI_API_KEY}"
    )

    timeout = aiohttp.ClientTimeout(total=30.0)
    async with aiohttp.ClientSession(timeout=timeout) as client:
        async with client.post(url, json=payload) as resp:
            if resp.status == 200:
                data = await resp.json()
                raw_text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                return json.loads(raw_text)
            else:
                body = await resp.text()
                logger.warning("Gemini API %d: %s", resp.status, body[:300])
                raise ValueError(f"Gemini API Error: {resp.status}")


def _make_fallback_quiz(req: AIGenerateRequest) -> dict:
    """Generate a placeholder quiz when Gemini is unavailable."""
    questions = []
    for i in range(1, req.num_questions + 1):
        correct_idx = random.randint(0, req.option_count - 1)
        opts = [
            {
                "label": chr(ord("A") + o_idx),
                "text": f"{req.topic} haqidagi {i}-savol uchun {chr(ord('A') + o_idx)} variant",
                "is_correct": (o_idx == correct_idx),
            }
            for o_idx in range(req.option_count)
        ]
        questions.append({
            "text": f"{req.topic} mavzusiga oid {req.difficulty} darajadagi {i}-savol?",
            "options": opts,
        })
    return {
        "title": f"{req.topic} testi ({req.difficulty.capitalize()})",
        "questions": questions,
    }


@router.post("/ai/generate", response_model=AIGenerateResponse)
async def generate_ai_quiz(
    req: AIGenerateRequest,
    tg_user_id: int = Depends(get_tg_user_id),
):
    """Generate an AI-powered quiz.

    Uses explicit session management so NO database connection is held
    during the potentially long Gemini API call.

    Flow:
      1. Open short session → check & reserve AI quota → close session.
      2. Call Gemini API (no DB connection held).
      3. Open short session → save test to DB → close session.
      4. On DB error → open short session → refund quota → close session.
    """
    # ── Phase 1: Reserve AI quota ─────────────────────────────
    user_id: int
    async with async_session() as session:
        stmt = (
            select(User)
            .where(User.tg_user_id == tg_user_id, User.role == UserRole.TEACHER)
            .with_for_update()
        )
        user = (await session.execute(stmt)).scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="O'qituvchi topilmadi.")
        if user.ai_queries_used >= user.ai_queries_limit:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"AI limit tugadi. Sizning limitingiz: {user.ai_queries_limit} ta so'rov.",
            )
        user_id = user.id
        user.ai_queries_used += 1
        await session.commit()
    # DB connection released here ↑

    try:
        quiz_data = await _call_gemini_api(req)
    except Exception as gemini_err:
        logger.error("Gemini API exhausted all retries: %s", gemini_err)
        quiz_data = None

    if not quiz_data:
        logger.info("Using fallback quiz for topic: %s", req.topic)
        quiz_data = _make_fallback_quiz(req)

    # ── Phase 3: Persist quiz ─────────────────────────────────
    try:
        async with async_session() as session:
            test = Test(
                code=await generate_test_code(session),
                teacher_id=user_id,
                title=quiz_data.get("title", f"{req.topic} testi"),
                difficulty=req.difficulty,
                status=TestStatus.DRAFT,
            )
            session.add(test)
            await session.flush()

            for pos, q_item in enumerate(quiz_data.get("questions", []), 1):
                q = Question(
                    test_id=test.id,
                    position=pos,
                    text=q_item.get("text", f"{pos}-savol"),
                )
                session.add(q)
                await session.flush()

                for opt_item in q_item.get("options", []):
                    session.add(Option(
                        question_id=q.id,
                        label=opt_item.get("label", "A"),
                        text=opt_item.get("text", "—"),
                        is_correct=opt_item.get("is_correct", False),
                    ))

            await session.commit()

            return AIGenerateResponse(
                test_id=test.id,
                title=test.title,
                code=test.code,
                questions_count=len(quiz_data.get("questions", [])),
                difficulty=test.difficulty,
            )

    except Exception as exc:
        # ── Phase 4: Refund quota on DB failure ───────────────
        logger.exception("Failed to persist AI quiz: %s", exc)
        try:
            async with async_session() as session:
                stmt = select(User).where(User.id == user_id).with_for_update()
                locked_user = (await session.execute(stmt)).scalar_one()
                locked_user.ai_queries_used = max(0, locked_user.ai_queries_used - 1)
                await session.commit()
                logger.info("AI quota refunded for user %d", user_id)
        except Exception as refund_exc:
            logger.error(
                "CRITICAL: Failed to refund AI quota for user %d: %s",
                user_id, refund_exc,
            )
        raise HTTPException(
            status_code=500,
            detail=f"Testni saqlashda xatolik yuz berdi: {exc}",
        ) from exc
