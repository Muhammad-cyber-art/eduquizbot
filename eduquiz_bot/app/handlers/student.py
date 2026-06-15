"""Student handlers — test code entry, quiz flow with question grid, results."""

from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from datetime import datetime, timezone
from sqlalchemy import select, func
from app.db.models import TestStatus, UserRole, User, Attempt, Test, Answer
from app.db.session import async_session
from app.keyboards.student import (
    finish_result_kb,
    question_grid_kb,
    quiz_option_kb,
    start_test_kb,
)
from app.services.attempts import (
    count_attempts,
    create_attempt,
    finish_attempt,
    get_attempt_by_id,
    get_attempt_result,
    save_answer,
)
from app.services.auth import get_or_create_user
from app.services.tests import get_question_with_options, get_test_by_code
from app.states import StudentSG
from app.utils.text import format_question, format_result, format_test_info, time_remaining

logger = logging.getLogger(__name__)
router = Router(name="student")


# ── Enter test code ─────────────────────────────────────────
@router.message(StudentSG.enter_code, F.text)
async def student_enter_code(message: Message, state: FSMContext):
    code = message.text.strip().upper()

    async with async_session() as session:
        test = await get_test_by_code(session, code)
        if not test:
            await message.answer("❌ Test kod noto'g'ri. Qayta kiriting:")
            return
        if test.status != TestStatus.OPEN:
            await message.answer("⚠️ Bu test hozir yopiq. Boshqa kod kiriting:")
            return

        # Get the test's teacher
        teacher = await session.get(User, test.teacher_id)
        if not teacher:
            await message.answer("⚠️ Ushbu test o'qituvchisi topilmadi. Testni topshira olmaysiz.")
            return

        # Check teacher status and validity limits
        if not teacher.is_active:
            await message.answer("⚠️ Ushbu test o'qituvchisi faol emas. Testni topshira olmaysiz.")
            return
        if teacher.expires_at and teacher.expires_at < datetime.now(timezone.utc):
            await message.answer("⚠️ Ushbu test o'qituvchisining obuna muddati tugagan. Testni topshira olmaysiz.")
            return

        # Ensure student user exists
        user = await get_or_create_user(
            session,
            tg_user_id=message.from_user.id,
            full_name=message.from_user.full_name,
            role=UserRole.STUDENT,
        )
        # Set WebApp menu button for student
        from app.utils.menu import set_user_menu_button
        await set_user_menu_button(message.bot, message.from_user.id, UserRole.STUDENT)

        # Enforce student enrollment limits for this teacher
        # Check if student has already attempted any test from this teacher
        stmt_has_attempt = (
            select(Attempt.id)
            .join(Test, Attempt.test_id == Test.id)
            .where(Test.teacher_id == teacher.id, Attempt.student_id == user.id)
            .limit(1)
        )
        has_attempt = (await session.execute(stmt_has_attempt)).scalar()
        
        if not has_attempt:
            # Count current unique students for this teacher
            stmt_count = (
                select(func.count(func.distinct(Attempt.student_id)))
                .join(Test, Attempt.test_id == Test.id)
                .where(Test.teacher_id == teacher.id)
            )
            current_students = (await session.execute(stmt_count)).scalar() or 0
            if current_students >= teacher.max_students:
                await message.answer(
                    f"⚠️ Ushbu o'qituvchining o'quvchilar soni limiti ({teacher.max_students}) to'lgan. Testni topshira olmaysiz."
                )
                return

        # Check attempt limit (skip if practice mode)
        attempt_count = await count_attempts(session, test.id, user.id)
        if getattr(test, "test_type", "standard") != "practice" and attempt_count >= test.attempt_limit:
            await message.answer(
                f"⚠️ Siz bu testni {attempt_count} marta topshirgansiz. "
                f"Limit: {test.attempt_limit}."
            )
            await state.clear()
            return

        # Extract all needed data INSIDE session
        test_id = test.id
        test_title = test.title
        test_code = test.code
        test_time_limit = test.time_limit_minutes
        q_count = len(test.questions)
        user_id = user.id

        await session.commit()

    await state.update_data(test_id=test_id, test_code=test_code, user_id=user_id)
    await state.set_state(StudentSG.confirm_start)

    info = format_test_info(test_title, test_code, q_count, test_time_limit)
    await message.answer(info, parse_mode="HTML", reply_markup=start_test_kb(test_id))


# ── Start test → show question grid ─────────────────────────
@router.callback_query(StudentSG.confirm_start, F.data.startswith("sstart_"))
async def cb_start_test(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    test_id = data["test_id"]
    user_id = data["user_id"]

    try:
        async with async_session() as session:
            attempt = await create_attempt(session, test_id, user_id)
            test = await get_test_by_code(session, data["test_code"])

            if not test or not test.questions:
                await call.message.edit_text("⚠️ Testda savollar yo'q.")
                await state.clear()
                await call.answer()
                return

            question_ids = [q.id for q in test.questions]
            attempt_id = attempt.id
            deadline = attempt.deadline_at

        await state.update_data(
            attempt_id=attempt_id,
            question_ids=question_ids,
            answered_ids=[],  # track answered question IDs
        )
        await state.set_state(StudentSG.in_quiz)

        # Show question grid
        remaining = time_remaining(deadline) if deadline else None
        time_text = ""
        if remaining is not None and remaining > 0:
            mm, ss = divmod(remaining, 60)
            time_text = f"\n⏱️ Qolgan vaqt: <b>{mm:02d}:{ss:02d}</b>"

        text = (
            f"📝 <b>Savollar ro'yxati</b>\n\n"
            f"Savolni tanlang va javob bering.{time_text}"
        )
        await call.message.edit_text(text, parse_mode="HTML")
        await call.message.answer(
            text,  # same text for the new message with keyboard
            parse_mode="HTML",
            reply_markup=question_grid_kb(attempt_id, question_ids, set()),
        )
    except Exception as e:
        logger.exception("Start test error: %s", e)
        await call.message.edit_text(f"⚠️ Xato yuz berdi: {e}")
        await state.clear()

    await call.answer()


# ── Select question from grid ───────────────────────────────
@router.callback_query(StudentSG.in_quiz, F.data.startswith("sq_"))
async def cb_select_question(call: CallbackQuery, state: FSMContext):
    """Student tapped a question number in the grid."""
    parts = call.data.split("_")
    attempt_id = int(parts[1])
    question_id = int(parts[2])

    data = await state.get_data()
    question_ids = data["question_ids"]

    # Find question index
    try:
        q_index = question_ids.index(question_id)
    except ValueError:
        await call.answer("Savol topilmadi", show_alert=True)
        return

    try:
        async with async_session() as session:
            q = await get_question_with_options(session, question_id)
            if not q:
                await call.answer("Savol topilmadi", show_alert=True)
                return

            # Extract data inside session
            q_data = {
                "id": q.id,
                "text": q.text,
                "image_file_id": q.image_file_id,
                "options": [{"label": o.label, "text": o.text} for o in q.options],
            }

            attempt = await get_attempt_by_id(session, attempt_id)
            deadline = attempt.deadline_at if attempt else None
            test = None
            if attempt:
                test = await session.get(Test, attempt.test_id)
            test_type = getattr(test, "test_type", "standard") if test else "standard"

        q_total = len(question_ids)
        remaining = time_remaining(deadline) if deadline else None

        text = format_question(
            q_index + 1, q_total, q_data["text"],
            q_data["options"], remaining,
        )

        if test_type == "written":
            text += "\n\n✍️ <b>Javobingizni xabar ko'rinishida yozib yuboring (variant harfini yoki qiymatini):</b>"
            kb = quiz_option_kb(q_data["id"], [], attempt_id)
            await state.set_state(StudentSG.waiting_written)
            await state.update_data(current_question_id=question_id, current_attempt_id=attempt_id)
        else:
            kb = quiz_option_kb(q_data["id"], q_data["options"], attempt_id)

        if q_data["image_file_id"]:
            # Send photo with question text as caption
            await call.message.answer_photo(
                photo=q_data["image_file_id"],
                caption=text,
                parse_mode="HTML",
                reply_markup=kb,
            )
            # Delete the old grid message to keep chat clean
            try:
                await call.message.delete()
            except Exception:
                pass
        else:
            await call.message.edit_text(
                text, parse_mode="HTML",
                reply_markup=kb,
            )
    except Exception as e:
        logger.exception("Select question error: %s", e)
        await call.answer(f"Xato: {e}", show_alert=True)
        return

    await call.answer()


# ── Back to grid ────────────────────────────────────────────
@router.callback_query(StudentSG.in_quiz, F.data.startswith("sgrid_"))
@router.callback_query(StudentSG.waiting_written, F.data.startswith("sgrid_"))
async def cb_back_to_grid(call: CallbackQuery, state: FSMContext):
    """Return to the question grid."""
    await state.set_state(StudentSG.in_quiz)
    data = await state.get_data()
    attempt_id = data["attempt_id"]
    question_ids = data["question_ids"]
    answered_ids = set(data.get("answered_ids", []))

    text = "📝 <b>Savollar ro'yxati</b>\n\nSavolni tanlang va javob bering."
    if call.message.photo:
        try:
            await call.message.delete()
        except Exception:
            pass
        await call.message.answer(
            text, parse_mode="HTML",
            reply_markup=question_grid_kb(attempt_id, question_ids, answered_ids),
        )
    else:
        await call.message.edit_text(
            text, parse_mode="HTML",
            reply_markup=question_grid_kb(attempt_id, question_ids, answered_ids),
        )
    await call.answer()


# ── Answer question → back to grid ──────────────────────────
@router.callback_query(StudentSG.in_quiz, F.data.startswith("ans_"))
async def cb_answer(call: CallbackQuery, state: FSMContext):
    """Student selected an answer — save it and return to grid/show feedback."""
    parts = call.data.split("_")
    question_id = int(parts[1])
    selected_label = parts[2]

    data = await state.get_data()
    attempt_id = data["attempt_id"]
    question_ids = data["question_ids"]
    answered_ids = set(data.get("answered_ids", []))

    try:
        async with async_session() as session:
            # Check if time expired
            attempt = await get_attempt_by_id(session, attempt_id)
            if attempt and attempt.deadline_at:
                remaining = time_remaining(attempt.deadline_at)
                if remaining is not None and remaining <= 0:
                    finished = await finish_attempt(session, attempt_id, expired=True)
                    await state.clear()
                    await call.message.edit_text(
                        "⏱️ <b>Vaqt tugadi!</b>\n\n" +
                        format_result(
                            finished.score or 0,
                            finished.max_score or 0,
                            float(finished.percent or 0),
                        ),
                        parse_mode="HTML",
                        reply_markup=finish_result_kb(attempt_id),
                    )
                    await call.answer("⏱️ Vaqt tugadi!")
                    return

            # Save answer
            await save_answer(session, attempt_id, question_id, selected_label)

            # Fetch test to check test_type
            test = await session.get(Test, attempt.test_id) if attempt else None
            test_type = getattr(test, "test_type", "standard") if test else "standard"
            
            q = await get_question_with_options(session, question_id)

        # Mark this question as answered
        answered_ids.add(question_id)
        await state.update_data(answered_ids=list(answered_ids))

        # Practice Mode: instant feedback and wait 3 seconds before moving to next question
        if test_type == "practice" and q:
            correct_opt = None
            selected_opt = None
            for opt in q.options:
                if opt.is_correct:
                    correct_opt = opt
                if opt.label == selected_label:
                    selected_opt = opt

            is_correct = (correct_opt and correct_opt.label == selected_label)
            selected_text = selected_opt.text if selected_opt else ""
            correct_label = correct_opt.label if correct_opt else ""
            correct_text = correct_opt.text if correct_opt else ""

            if is_correct:
                feedback = (
                    f"✅ <b>To'g'ri!</b>\n"
                    f"Sizning javobingiz: <b>{selected_label}) {selected_text}</b>"
                )
            else:
                feedback = (
                    f"❌ <b>Noto'g'ri!</b>\n"
                    f"Sizning javobingiz: <b>{selected_label}) {selected_text}</b>\n"
                    f"To'g'ri javob: <b>{correct_label}) {correct_text}</b>"
                )

            if q.explanation:
                feedback += f"\n\nℹ️ <b>Tushuntirish:</b>\n{q.explanation}"

            # Format original question layout
            q_index = question_ids.index(question_id)
            q_total = len(question_ids)
            remaining = time_remaining(attempt.deadline_at) if attempt and attempt.deadline_at else None
            q_display = format_question(q_index + 1, q_total, q.text, [], remaining)

            full_text = f"{feedback}\n\n{q_display}"

            # Edit message to show feedback and remove buttons to prevent double-clicks
            if call.message.photo:
                if len(full_text) > 1024:
                    full_text = full_text[:1020] + "..."
                await call.message.edit_caption(
                    caption=full_text,
                    parse_mode="HTML",
                    reply_markup=None,
                )
            else:
                await call.message.edit_text(
                    full_text,
                    parse_mode="HTML",
                    reply_markup=None,
                )

            await call.answer("To'g'ri!" if is_correct else "Noto'g'ri!")
            
            import asyncio
            await asyncio.sleep(3)
            
            # Transition to next question if exists, otherwise back to grid
            next_index = q_index + 1
            if next_index < q_total:
                next_q_id = question_ids[next_index]
                async with async_session() as session:
                    next_q = await get_question_with_options(session, next_q_id)
                    if next_q:
                        next_q_data = {
                            "id": next_q.id,
                            "text": next_q.text,
                            "image_file_id": next_q.image_file_id,
                            "options": [{"label": o.label, "text": o.text} for o in next_q.options],
                        }
                        
                        next_text = format_question(
                            next_index + 1, q_total, next_q_data["text"],
                            next_q_data["options"], remaining,
                        )
                        next_kb = quiz_option_kb(next_q_data["id"], next_q_data["options"], attempt_id)
                        
                        try:
                            await call.message.delete()
                        except Exception:
                            pass
                            
                        if next_q_data["image_file_id"]:
                            await call.message.answer_photo(
                                photo=next_q_data["image_file_id"],
                                caption=next_text,
                                parse_mode="HTML",
                                reply_markup=next_kb,
                            )
                        else:
                            await call.message.answer(
                                next_text, parse_mode="HTML",
                                reply_markup=next_kb,
                            )
            else:
                # Return to grid after the last question
                grid_text = "📝 <b>Savollar ro'yxati</b>\n\nSavolni tanlang va javob bering."
                try:
                    await call.message.delete()
                except Exception:
                    pass
                await call.message.answer(
                    grid_text, parse_mode="HTML",
                    reply_markup=question_grid_kb(attempt_id, question_ids, answered_ids),
                )
            return

        # Standard Mode: Return to grid
        text = (
            f"✅ <b>{selected_label})</b> javob saqlandi!\n\n"
            f"📝 <b>Savollar ro'yxati</b>\n\n"
            f"Savolni tanlang va javob bering."
        )
        if call.message.photo:
            try:
                await call.message.delete()
            except Exception:
                pass
            await call.message.answer(
                text, parse_mode="HTML",
                reply_markup=question_grid_kb(attempt_id, question_ids, answered_ids),
            )
        else:
            await call.message.edit_text(
                text, parse_mode="HTML",
                reply_markup=question_grid_kb(attempt_id, question_ids, answered_ids),
            )
    except Exception as e:
        logger.exception("Answer error: %s", e)
        await call.message.answer(f"⚠️ Xato: {e}. /start — qayta boshlash.")
        await state.clear()

    await call.answer()


# ── Finish test from grid ───────────────────────────────────
@router.callback_query(StudentSG.in_quiz, F.data.startswith("sfinish_"))
async def cb_finish_test(call: CallbackQuery, state: FSMContext):
    """Student wants to finish the test from the grid."""
    data = await state.get_data()
    attempt_id = data["attempt_id"]
    question_ids = data["question_ids"]
    answered_ids = set(data.get("answered_ids", []))

    unanswered = len(question_ids) - len(answered_ids)

    try:
        async with async_session() as session:
            finished = await finish_attempt(session, attempt_id)

        await state.clear()
        text = ""
        if unanswered > 0:
            text += f"⚠️ {unanswered} ta savol javobsiz qoldi.\n\n"
        text += format_result(
            finished.score or 0,
            finished.max_score or 0,
            float(finished.percent or 0),
        )
        await call.message.edit_text(
            text, parse_mode="HTML",
            reply_markup=finish_result_kb(attempt_id),
        )
    except Exception as e:
        logger.exception("Finish error: %s", e)
        await call.message.answer(f"⚠️ Xato: {e}. /start — qayta boshlash.")
        await state.clear()

    await call.answer("🏁 Test yakunlandi!")


# ── View result ─────────────────────────────────────────────
@router.callback_query(F.data.startswith("sresult_"))
async def cb_view_result(call: CallbackQuery):
    attempt_id = int(call.data.split("_", 1)[1])
    async with async_session() as session:
        att = await get_attempt_result(session, attempt_id)
    if not att:
        await call.answer("Natija topilmadi", show_alert=True)
        return
    await call.message.answer(
        format_result(
            att.score or 0,
            att.max_score or 0,
            float(att.percent or 0),
        ),
        parse_mode="HTML",
    )
    await call.answer()


# ── Home ────────────────────────────────────────────────────
@router.callback_query(F.data == "s_home")
async def cb_student_home(call: CallbackQuery, state: FSMContext):
    await state.set_state(StudentSG.enter_code)
    from app.keyboards.student import student_home_kb
    await call.message.edit_text("🔑 Yangi test kodini kiriting:", reply_markup=student_home_kb())
    await call.answer()



# ── Helpers ──────────────────────────────────────────────────
def _extract_question(q) -> dict:
    """Extract question data into plain dict (safe to use outside session)."""
    return {
        "id": q.id,
        "text": q.text,
        "options": [{"label": o.label, "text": o.text} for o in q.options],
    }


# ── Written Answer Handler ──────────────────────────────────
@router.message(StudentSG.waiting_written, F.text)
async def student_written_answer(message: Message, state: FSMContext):
    """Handle text answer in Written mode."""
    typed_answer = message.text.strip()
    
    data = await state.get_data()
    attempt_id = data["attempt_id"]
    question_ids = data["question_ids"]
    answered_ids = set(data.get("answered_ids", []))
    
    question_id = data.get("current_question_id")
    if not question_id:
        await message.answer("⚠️ Xatolik yuz berdi. Iltimos, /start buyrug'ini bosing.")
        await state.clear()
        return

    try:
        async with async_session() as session:
            # Check if time expired
            attempt = await get_attempt_by_id(session, attempt_id)
            if attempt and attempt.deadline_at:
                remaining = time_remaining(attempt.deadline_at)
                if remaining is not None and remaining <= 0:
                    finished = await finish_attempt(session, attempt_id, expired=True)
                    await state.clear()
                    await message.answer(
                        "⏱️ <b>Vaqt tugadi!</b>\n\n" +
                        format_result(
                            finished.score or 0,
                            finished.max_score or 0,
                            float(finished.percent or 0),
                        ),
                        parse_mode="HTML",
                        reply_markup=finish_result_kb(attempt_id),
                    )
                    return

            q = await get_question_with_options(session, question_id)
            if not q:
                await message.answer("Savol topilmadi.")
                return

            # Find the correct option and any wrong option
            correct_opt = None
            wrong_opt = None
            for opt in q.options:
                if opt.is_correct:
                    correct_opt = opt
                else:
                    wrong_opt = opt

            if not correct_opt:
                correct_label = "A"
                correct_text = ""
            else:
                correct_label = correct_opt.label
                correct_text = correct_opt.text.strip()

            # Compare typed answer case-insensitively with both label (e.g. A) and option text
            is_correct = (
                typed_answer.lower() == correct_label.lower() or
                typed_answer.lower() == correct_text.lower()
            )

            # Assign matching label
            if is_correct:
                selected_label = correct_label
            else:
                selected_label = "B" if correct_label == "A" else "A"
                if wrong_opt:
                    selected_label = wrong_opt.label

            # Save answer with selected_text set
            stmt = select(Answer).where(
                Answer.attempt_id == attempt_id,
                Answer.question_id == question_id,
            )
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()
            if existing:
                existing.selected_label = selected_label
                existing.selected_text = typed_answer
            else:
                answer = Answer(
                    attempt_id=attempt_id,
                    question_id=question_id,
                    selected_label=selected_label,
                    selected_text=typed_answer,
                )
                session.add(answer)
            await session.commit()

        # Mark question as answered
        answered_ids.add(question_id)
        await state.update_data(answered_ids=list(answered_ids))
        await state.set_state(StudentSG.in_quiz)

        # Show confirmation and return to grid
        text = (
            f"✅ Javobingiz saqlandi!\n\n"
            f"📝 <b>Savollar ro'yxati</b>\n\n"
            f"Savolni tanlang va javob bering."
        )
        await message.answer(
            text, parse_mode="HTML",
            reply_markup=question_grid_kb(attempt_id, question_ids, answered_ids),
        )

    except Exception as e:
        logger.exception("Written answer handler error: %s", e)
        await message.answer(f"⚠️ Xato: {e}. /start — qayta boshlash.")
        await state.clear()
