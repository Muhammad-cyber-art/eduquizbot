"""Telegram WebApp APIs — dashboards and AI generator."""

import json
import logging
import random
import string
import aiohttp
from datetime import datetime, timedelta, timezone

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.db.models import Attempt, Option, Question, Test, TestStatus, User, UserRole
from app.db.session import get_async_session
from app.utils.codes import generate_test_code

logger = logging.getLogger(__name__)
router = APIRouter()

import hashlib
import hmac
from urllib.parse import parse_qsl
from fastapi import Header

async def get_tg_user_id(x_tg_init_data: str = Header(..., alias="X-TG-Init-Data")) -> int:
    # DEV bypass — only allowed in development mode
    if x_tg_init_data.startswith("DEV_"):
        if settings.is_production:
            raise HTTPException(status_code=401, detail="DEV mode disabled in production")
        try:
            return int(x_tg_init_data.replace("DEV_", ""))
        except ValueError:
            raise HTTPException(status_code=401, detail="Invalid DEV user id")

    try:
        parsed_data = dict(parse_qsl(x_tg_init_data))
        if "hash" not in parsed_data:
            raise ValueError("No hash in init data")

        hash_value = parsed_data.pop("hash")
        data_check_string = "\n".join(
            f"{k}={v}" for k, v in sorted(parsed_data.items())
        )

        secret_key = hmac.new(b"WebAppData", settings.BOT_TOKEN.encode(), hashlib.sha256).digest()
        calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

        if calculated_hash != hash_value:
            raise ValueError("Invalid hash")

        # Reject stale init data (older than 24 hours)
        if "auth_date" in parsed_data:
            auth_ts = int(parsed_data["auth_date"])
            age_seconds = int(datetime.now(timezone.utc).timestamp()) - auth_ts
            if age_seconds > 86400:
                raise ValueError(f"Init data expired ({age_seconds}s old)")

        if "user" in parsed_data:
            user_data = json.loads(parsed_data["user"])
            return int(user_data["id"])

        raise ValueError("No user id in init data")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Unauthorized: {e}")



# ── Pydantic Request/Response Models ────────────────────────
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


@router.get("/user/role")
async def get_user_role(
    tg_user_id: int = Depends(get_tg_user_id),
    session: AsyncSession = Depends(get_async_session),
):
    stmt = select(User).where(User.tg_user_id == tg_user_id)
    res = await session.execute(stmt)
    user = res.scalar_one_or_none()
    if not user:
        return {"role": None}
    return {"role": user.role.value if hasattr(user.role, "value") else str(user.role)}


# ── Teacher Stats Endpoint ──────────────────────────────────
@router.get("/teacher/stats")
async def get_teacher_stats(
    tg_user_id: int = Depends(get_tg_user_id),
    session: AsyncSession = Depends(get_async_session),
):
    # Find teacher
    stmt = select(User).where(User.tg_user_id == tg_user_id, User.role == UserRole.TEACHER)
    res = await session.execute(stmt)
    teacher = res.scalar_one_or_none()
    if not teacher:
         raise HTTPException(status_code=404, detail="O'qituvchi topilmadi.")

    # Fetch teacher's tests
    stmt_tests = (
        select(Test)
        .where(Test.teacher_id == teacher.id)
        .options(selectinload(Test.attempts))
        .order_by(Test.created_at.desc())
    )
    res_tests = await session.execute(stmt_tests)
    tests = res_tests.scalars().all()

    # Fetch all attempts for these tests to calculate overall metrics
    stmt_attempts = (
        select(Attempt)
        .join(Test)
        .where(Test.teacher_id == teacher.id)
        .options(selectinload(Attempt.student), selectinload(Attempt.test))
    )
    res_attempts = await session.execute(stmt_attempts)
    attempts = res_attempts.scalars().all()

    total_tests = len(tests)
    finished_attempts = [a for a in attempts if a.status in ("finished", "expired")]
    total_attempts_count = len(finished_attempts)

    # Pass rate (percent >= 50%)
    passed_attempts = [a for a in finished_attempts if (a.percent or 0) >= 50.0]
    pass_rate = round((len(passed_attempts) / total_attempts_count * 100), 1) if total_attempts_count else 0.0

    # Extreme scores (Eng past baholar va eng baland ballar)
    sorted_attempts = sorted(finished_attempts, key=lambda a: (a.percent or 0), reverse=True)
    
    top_attempts = []
    for a in sorted_attempts[:3]:
        top_attempts.append({
            "student_name": a.student.full_name if a.student and a.student.full_name else "Noma'lum o'quvchi",
            "test_title": a.test.title,
            "percent": float(a.percent or 0),
            "score": a.score,
            "max_score": a.max_score,
            "finished_at": a.finished_at.strftime("%Y-%m-%d %H:%M") if a.finished_at else ""
        })

    bottom_attempts = []
    for a in reversed(sorted_attempts[-3:]):
        if len(bottom_attempts) >= 3:
            break
        # Avoid duplicate rendering if total attempts < 3
        if a in sorted_attempts[:3] and len(sorted_attempts) < 3:
            continue
        bottom_attempts.append({
            "student_name": a.student.full_name if a.student and a.student.full_name else "Noma'lum o'quvchi",
            "test_title": a.test.title,
            "percent": float(a.percent or 0),
            "score": a.score,
            "max_score": a.max_score,
            "finished_at": a.finished_at.strftime("%Y-%m-%d %H:%M") if a.finished_at else ""
        })

    # Growth Trends (student progress over their last attempts)
    # Group attempts by student
    student_attempts_map = {}
    for a in finished_attempts:
        s_id = a.student_id
        if s_id not in student_attempts_map:
            student_attempts_map[s_id] = {
                "student_name": a.student.full_name if a.student and a.student.full_name else "Noma'lum o'quvchi",
                "attempts": []
            }
        student_attempts_map[s_id]["attempts"].append({
            "test_title": a.test.title,
            "percent": float(a.percent or 0),
            "date": a.finished_at.strftime("%Y-%m-%d") if a.finished_at else ""
        })

    # Filter students with at least 2 attempts to show actual trend
    growth_trends = []
    for s_data in student_attempts_map.values():
        if len(s_data["attempts"]) >= 2:
            # Sort chronologically by date
            s_data["attempts"].sort(key=lambda x: x["date"])
            growth_trends.append(s_data)

    # Detailed test list for table
    tests_list = []
    for t in tests:
        t_attempts = [a for a in finished_attempts if a.test_id == t.id]
        t_cnt = len(t_attempts)
        t_avg = sum(a.percent for a in t_attempts) / t_cnt if t_cnt else 0
        tests_list.append({
            "id": t.id,
            "title": t.title,
            "code": t.code,
            "difficulty": t.difficulty,
            "status": t.status.value if hasattr(t.status, "value") else str(t.status),
            "attempts_count": t_cnt,
            "average_score": round(t_avg, 2),
            "created_at": t.created_at.strftime("%Y-%m-%d") if t.created_at else ""
        })

    return {
        "teacher_name": teacher.full_name,
        "ai_queries_limit": teacher.ai_queries_limit,
        "ai_queries_used": teacher.ai_queries_used,
        "total_tests": total_tests,
        "total_attempts": total_attempts_count,
        "pass_rate": pass_rate,
        "top_attempts": top_attempts,
        "bottom_attempts": bottom_attempts,
        "growth_trends": growth_trends[:10],  # limit to top 10 trends for UI
        "tests": tests_list,
    }


# ── Teacher Test Details Endpoint ───────────────────────────
@router.get("/teacher/tests/{test_id}")
async def get_test_details(
    test_id: int,
    tg_user_id: int = Depends(get_tg_user_id),
    session: AsyncSession = Depends(get_async_session),
):
    stmt = select(Test).where(Test.id == test_id).options(
        selectinload(Test.teacher),
        selectinload(Test.attempts).selectinload(Attempt.student)
    )
    res = await session.execute(stmt)
    test = res.scalar_one_or_none()
    
    if not test or test.teacher.tg_user_id != tg_user_id:
        raise HTTPException(status_code=404, detail="Test topilmadi yoki ruxsat yo'q")

    participants = []
    for a in test.attempts:
        if a.status in ("finished", "expired"):
            participants.append({
                "student_name": a.student.full_name if a.student and a.student.full_name else "Noma'lum",
                "score": a.score,
                "max_score": a.max_score,
                "percent": float(a.percent or 0),
                "finished_at": a.finished_at.strftime("%Y-%m-%d %H:%M") if a.finished_at else ""
            })
            
    # Sort participants by score descending
    participants.sort(key=lambda x: x["percent"], reverse=True)

    return {
        "id": test.id,
        "title": test.title,
        "code": test.code,
        "difficulty": test.difficulty,
        "status": test.status.value if hasattr(test.status, "value") else str(test.status),
        "created_at": test.created_at.strftime("%Y-%m-%d %H:%M") if test.created_at else "",
        "participants": participants
    }


class UpdateTestStatusRequest(BaseModel):
    status: str

@router.put("/teacher/tests/{test_id}/status")
async def update_test_status(
    test_id: int,
    req: UpdateTestStatusRequest,
    tg_user_id: int = Depends(get_tg_user_id),
    session: AsyncSession = Depends(get_async_session),
):
    stmt = select(Test).where(Test.id == test_id).options(selectinload(Test.teacher))
    res = await session.execute(stmt)
    test = res.scalar_one_or_none()
    
    if not test or test.teacher.tg_user_id != tg_user_id:
        raise HTTPException(status_code=404, detail="Test topilmadi yoki ruxsat yo'q")

    try:
        # Validate status enum if possible
        if hasattr(TestStatus, req.status.upper()):
            test.status = getattr(TestStatus, req.status.upper())
        else:
            test.status = req.status # Fallback
        await session.commit()
        return {"success": True, "status": req.status}
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=str(e))



# ── Student Stats Endpoint ──────────────────────────────────
@router.get("/student/stats")
async def get_student_stats(
    tg_user_id: int = Depends(get_tg_user_id),
    session: AsyncSession = Depends(get_async_session),
):
    # Find student
    stmt = select(User).where(User.tg_user_id == tg_user_id, User.role == UserRole.STUDENT)
    res = await session.execute(stmt)
    student = res.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="O'quvchi topilmadi.")

    # Fetch attempts by this student
    stmt_attempts = (
        select(Attempt)
        .where(Attempt.student_id == student.id)
        .options(selectinload(Attempt.test))
        .order_by(Attempt.finished_at.desc())
    )
    res_attempts = await session.execute(stmt_attempts)
    attempts = res_attempts.scalars().all()

    finished_attempts = [a for a in attempts if a.status in ("finished", "expired")]

    # Calculate overall XP and stats
    total_xp = sum(a.xp_earned for a in finished_attempts)
    attempts_count = len(finished_attempts)
    average_score = sum(a.percent for a in finished_attempts) / attempts_count if attempts_count else 0.0

    # Weekly & Monthly Leaderboard
    now = datetime.now(timezone.utc)
    monday = now - timedelta(days=now.weekday())
    monday = monday.replace(hour=0, minute=0, second=0, microsecond=0)
    first_day = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Weekly Leaderboard
    stmt_weekly = (
        select(
            User.id,
            User.full_name,
            func.sum(Attempt.xp_earned).label("weekly_xp")
        )
        .join(Attempt, Attempt.student_id == User.id)
        .where(Attempt.status.in_(["finished", "expired"]), Attempt.finished_at >= monday)
        .group_by(User.id, User.full_name)
        .order_by(func.sum(Attempt.xp_earned).desc())
    )
    res_weekly = await session.execute(stmt_weekly)
    weekly_rows = res_weekly.all()

    weekly_leaderboard = []
    student_weekly_rank = None
    for idx, row in enumerate(weekly_rows, 1):
        weekly_leaderboard.append({
            "rank": idx,
            "student_name": row.full_name or "Noma'lum o'quvchi",
            "xp": row.weekly_xp
        })
        if row.id == student.id:
            student_weekly_rank = idx

    # Monthly Leaderboard
    stmt_monthly = (
        select(
            User.id,
            User.full_name,
            func.sum(Attempt.xp_earned).label("monthly_xp")
        )
        .join(Attempt, Attempt.student_id == User.id)
        .where(Attempt.status.in_(["finished", "expired"]), Attempt.finished_at >= first_day)
        .group_by(User.id, User.full_name)
        .order_by(func.sum(Attempt.xp_earned).desc())
    )
    res_monthly = await session.execute(stmt_monthly)
    monthly_rows = res_monthly.all()

    monthly_leaderboard = []
    student_monthly_rank = None
    for idx, row in enumerate(monthly_rows, 1):
        monthly_leaderboard.append({
            "rank": idx,
            "student_name": row.full_name or "Noma'lum o'quvchi",
            "xp": row.monthly_xp
        })
        if row.id == student.id:
            student_monthly_rank = idx

    # History
    attempts_history = []
    for a in finished_attempts:
        attempts_history.append({
            "test_title": a.test.title,
            "test_code": a.test.code,
            "difficulty": a.test.difficulty,
            "score": a.score,
            "max_score": a.max_score,
            "percent": float(a.percent or 0),
            "xp_earned": a.xp_earned,
            "status": a.status,
            "date": a.finished_at.strftime("%Y-%m-%d %H:%M") if a.finished_at else ""
        })

    # Progress trends (XP over time)
    progress_trends = []
    cumulative_xp = 0
    # Process from oldest to newest to show cumulative growth
    for a in reversed(finished_attempts):
        cumulative_xp += a.xp_earned
        progress_trends.append({
            "date": a.finished_at.strftime("%Y-%m-%d") if a.finished_at else "",
            "xp_gained": a.xp_earned,
            "cumulative_xp": cumulative_xp,
            "test_title": a.test.title
        })

    return {
        "student_name": student.full_name,
        "total_xp": total_xp,
        "attempts_count": attempts_count,
        "average_score": round(average_score, 1),
        "weekly_rank": student_weekly_rank,
        "monthly_rank": student_monthly_rank,
        "weekly_leaderboard": weekly_leaderboard[:10],
        "monthly_leaderboard": monthly_leaderboard[:10],
        "attempts": attempts_history,
        "progress_trends": progress_trends,
    }


# ── AI Quiz Generator Endpoint ──────────────────────────────
@router.post("/ai/generate", response_model=AIGenerateResponse)
async def generate_ai_quiz(
    req: AIGenerateRequest,
    tg_user_id: int = Depends(get_tg_user_id),
    session: AsyncSession = Depends(get_async_session),
):
    # Find teacher and lock row to prevent race conditions
    stmt = select(User).where(User.tg_user_id == tg_user_id, User.role == UserRole.TEACHER).with_for_update()
    res = await session.execute(stmt)
    user = res.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="O'qituvchi topilmadi.")

    # Check limits
    if user.ai_queries_used >= user.ai_queries_limit:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"AI limit tugadi. Sizning limitingiz: {user.ai_queries_limit} ta so'rov.",
        )

    # Increment quota immediately to release lock and prevent race conditions
    user.ai_queries_used += 1
    await session.commit()

    # Try calling Gemini API
    quiz_data = None
    if settings.GEMINI_API_KEY:
        try:
            prompt = (
                f"Siz test yaratuvchi professional yordamchisiz. Quyidagi mavzu bo'yicha mukammal va to'g'ri test yaratib bering:\n"
                f"Mavzu: {req.topic}\n"
                f"Savollar soni: {req.num_questions}\n"
                f"Qiyinchilik darajasi: {req.difficulty} (easy, medium, hard)\n"
                f"Variantlar soni: {req.option_count} ta (A, B, C... va hokazo formatda)\n\n"
                f"Siz faqat va faqat quyidagi tuzilishdagi JSON formatida javob berishingiz shart. Boshqa hech qanday izoh yoki tushuntirish yozmang:\n"
                f"{{\n"
                f"  \"title\": \"Mavzuga mos sarlavha\",\n"
                f"  \"questions\": [\n"
                f"    {{\n"
                f"      \"text\": \"Savol matni?\",\n"
                f"      \"options\": [\n"
                f"        {{\"label\": \"A\", \"text\": \"Variant A matni\", \"is_correct\": true}},\n"
                f"        {{\"label\": \"B\", \"text\": \"Variant B matni\", \"is_correct\": false}},\n"
                f"        ...\n"
                f"      ]\n"
                f"    }}\n"
                f"  ]\n"
                f"}}\n"
                f"Har bir savol uchun faqat bitta variant to'g'ri bo'lishini (is_correct: true) va qolganlari noto'g'ri bo'lishini ta'minlang."
            )

            headers = {"Content-Type": "application/json"}
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "responseMimeType": "application/json"
                }
            }
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={settings.GEMINI_API_KEY}"

            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30.0)) as client:
                async with client.post(url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        resp_json = await response.json()
                        text_out = resp_json["candidates"][0]["content"]["parts"][0]["text"].strip()
                        # Parse JSON
                        quiz_data = json.loads(text_out)
                    else:
                        resp_text = await response.text()
                        logger.warning("Gemini API returned status %d: %s", response.status, resp_text)

        except Exception as e:
            logger.exception("Failed to generate quiz using Gemini: %s", e)

    # Fallback if Gemini failed or key not configured
    if not quiz_data:
        logger.info("Using fallback mock quiz generation for topic: %s", req.topic)
        fallback_title = f"{req.topic} testi ({req.difficulty.capitalize()})"
        fallback_questions = []
        for i in range(1, req.num_questions + 1):
            opts = []
            for o_idx in range(req.option_count):
                label = chr(ord("A") + o_idx)
                opts.append({
                    "label": label,
                    "text": f"{req.topic} haqidagi {i}-savol uchun {label} variant",
                    "is_correct": o_idx == 0
                })
            # Shuffling the options correct index
            correct_idx = random.randint(0, req.option_count - 1)
            for o_idx, opt in enumerate(opts):
                opt["is_correct"] = (o_idx == correct_idx)

            fallback_questions.append({
                "text": f"{req.topic} mavzusiga oid {req.difficulty} darajadagi {i}-savol?",
                "options": opts
            })
        quiz_data = {"title": fallback_title, "questions": fallback_questions}

    # Save Draft Test and Questions
    try:
        test = Test(
            code=await generate_test_code(session),
            teacher_id=user.id,
            title=quiz_data.get("title", f"{req.topic} testi"),
            difficulty=req.difficulty,
            status=TestStatus.DRAFT,
        )
        session.add(test)
        await session.flush()

        import tempfile
        import os
        from docx import Document
        from aiogram import Bot
        from aiogram.types import BufferedInputFile
        from app.services.parsing import parse_file

        # Generate DOCX from AI output
        doc = Document()
        doc.add_heading(quiz_data.get("title", f"{req.topic} testi"), 0)

        for pos, q_item in enumerate(quiz_data.get("questions", []), 1):
            doc.add_paragraph(f"{pos}. {q_item.get('text', '')}")
            for opt_item in q_item.get("options", []):
                doc.add_paragraph(f"{opt_item.get('label', 'A')}) {opt_item.get('text', '')}")
            doc.add_paragraph()  # Empty line separator

        fd, tmp_path = tempfile.mkstemp(suffix=".docx")
        os.close(fd)
        
        bot = Bot(token=settings.BOT_TOKEN)
        
        try:
            doc.save(tmp_path)
            # Parse it to get cropped images
            parsed_questions = parse_file(tmp_path)
            
            # Map images to questions
            for pos, q_item in enumerate(quiz_data.get("questions", []), 1):
                file_id = None
                # Try to find corresponding parsed question (0-indexed)
                pq_idx = pos - 1
                if pq_idx < len(parsed_questions):
                    pq = parsed_questions[pq_idx]
                    if pq.image_bytes:
                        try:
                            # Send photo to teacher silently and delete immediately to just get file_id
                            msg = await bot.send_photo(
                                chat_id=tg_user_id,
                                photo=BufferedInputFile(pq.image_bytes, filename=f"q{pos}.jpg"),
                                disable_notification=True
                            )
                            file_id = msg.photo[-1].file_id
                            try:
                                await bot.delete_message(chat_id=tg_user_id, message_id=msg.message_id)
                            except Exception:
                                pass
                        except Exception as e:
                            logger.warning(f"Failed to upload image for question {pos}: {e}")

                q = Question(
                    test_id=test.id,
                    position=pos,
                    text=q_item.get("text", f"{pos}-savol"),
                    image_file_id=file_id
                )
                session.add(q)
                await session.flush()

                for opt_item in q_item.get("options", []):
                    opt = Option(
                        question_id=q.id,
                        label=opt_item.get("label", "A"),
                        text=opt_item.get("text", "—"),
                        is_correct=opt_item.get("is_correct", False),
                    )
                    session.add(opt)
                    
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            await bot.session.close()

        # Successfully created test, commit the test details
        await session.commit()

        return AIGenerateResponse(
            test_id=test.id,
            title=test.title,
            code=test.code,
            questions_count=len(quiz_data.get("questions", [])),
            difficulty=test.difficulty
        )

    except Exception as e:
        await session.rollback()
        # Refund the quota since creation failed
        try:
            stmt = select(User).where(User.id == user.id).with_for_update()
            u_res = await session.execute(stmt)
            locked_user = u_res.scalar_one()
            locked_user.ai_queries_used = max(0, locked_user.ai_queries_used - 1)
            await session.commit()
        except Exception:
            pass # Ignore refund errors to return the main error
            
        logger.exception("Failed to write AI test to DB: %s", e)
        raise HTTPException(
            status_code=500,
            detail=f"Testni ma'lumotlar bazasiga yozishda xatolik: {e}"
        )
