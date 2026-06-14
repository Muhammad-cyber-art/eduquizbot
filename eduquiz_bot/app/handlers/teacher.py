"""Teacher handlers — test creation, management, and export flow."""

from __future__ import annotations

import html
import io
import logging
import os
import tempfile

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    BufferedInputFile,
    CallbackQuery,
    Message,
    ReplyKeyboardRemove,
)
from datetime import datetime, timezone
from sqlalchemy import func, select

from app.db.models import AccessRequest, Attempt, TestStatus, UserRole, User, Test
from app.db.session import async_session
from app.keyboards.teacher import (
    answers_file_prompt_kb,
    confirm_review_kb,
    mark_answer_kb,
    question_viewer_kb,
    teacher_panel_kb,
    test_list_kb,
    test_manage_kb,
    test_settings_kb,
    time_toggle_kb,
)
from app.services.attempts import get_test_results
from app.services.auth import (
    get_user_by_tg_id,
    validate_teacher_pin,
    validate_access_password,
    get_access_request_by_phone,
    create_access_request,
)
from app.services.exports import export_test_results_xlsx
from app.services.parsing import parse_file, parse_answer_key
from app.services.tests import (
    add_question,
    create_test,
    get_question_with_options,
    get_test_full,
    list_teacher_tests,
    set_correct_answer,
    set_question_image,
    set_test_status,
    update_test_settings,
)
from app.states import TeacherSG

logger = logging.getLogger(__name__)
router = Router(name="teacher")


# ── Guard: only teachers ────────────────────────────────────
async def _ensure_teacher(tg_user_id: int):
    """Return user if teacher, else None."""
    async with async_session() as session:
        user = await get_user_by_tg_id(session, tg_user_id)
        if user and user.role == UserRole.TEACHER:
            return user
    return None


# ── PIN input / Auth ────────────────────────────────────────
@router.message(TeacherSG.pin, F.text)
async def teacher_pin(message: Message, state: FSMContext):
    code = message.text.strip()
    if code == "❌ Bekor qilish" or code == "/cancel":
        await state.clear()
        from app.keyboards.common import role_kb
        await message.answer(
            "❌ Amal bekor qilindi.",
            reply_markup=ReplyKeyboardRemove(),
        )
        await message.answer("👤 Rolingizni tanlang:", reply_markup=role_kb())
        return

    data = await state.get_data()
    lang = data.get("lang", "uz")

    async with async_session() as session:
        # Check PIN code first
        invite = await validate_teacher_pin(session, code)
        if invite is not None:
            user = await get_user_by_tg_id(session, message.from_user.id)
            if user:
                user.role = UserRole.TEACHER
                user.max_tests = invite.max_tests
                user.max_students = invite.max_students
                user.expires_at = invite.expires_at
            else:
                user = User(
                    tg_user_id=message.from_user.id,
                    full_name=message.from_user.full_name,
                    role=UserRole.TEACHER,
                    lang_code=lang,
                    max_tests=invite.max_tests,
                    max_students=invite.max_students,
                    expires_at=invite.expires_at,
                )
                session.add(user)
            await session.commit()

            await state.clear()
            await message.answer(
                "✅ O'qituvchi paneliga xush kelibsiz!",
                reply_markup=ReplyKeyboardRemove(),
            )
            await message.answer(
                "👨‍🏫 O'qituvchi paneli:",
                reply_markup=teacher_panel_kb(),
            )
            return

        # Check access password
        access = await validate_access_password(session, code)
        if access and access.tg_user_id == message.from_user.id:
            access.status = "used"

            user = await get_user_by_tg_id(session, message.from_user.id)
            if user:
                user.role = UserRole.TEACHER
                user.max_tests = access.max_tests
                user.max_students = access.max_students
                user.expires_at = access.expires_at
            else:
                user = User(
                    tg_user_id=message.from_user.id,
                    full_name=access.full_name,
                    role=UserRole.TEACHER,
                    lang_code=lang,
                    max_tests=access.max_tests,
                    max_students=access.max_students,
                    expires_at=access.expires_at,
                )
                session.add(user)
            await session.commit()

            await state.clear()
            await message.answer(
                "✅ O'qituvchi paneliga xush kelibsiz!",
                reply_markup=ReplyKeyboardRemove(),
            )
            await message.answer(
                "👨‍🏫 O'qituvchi paneli:",
                reply_markup=teacher_panel_kb(),
            )
            return

        await message.answer("❌ Kod yoki parol noto'g'ri. Qayta kiriting:")


@router.message(TeacherSG.pin, F.contact)
async def teacher_contact_login(message: Message, state: FSMContext):
    contact = message.contact
    if contact.user_id != message.from_user.id:
        await message.answer("⚠️ Iltimos, faqat o'zingizning telefon raqamingizni ulashing.")
        return

    phone = contact.phone_number.replace("+", "").replace(" ", "").strip()
    data = await state.get_data()
    lang = data.get("lang", "uz")

    async with async_session() as session:
        req = await get_access_request_by_phone(session, phone)

        if req:
            if req.status == "approved":
                # Upgrade user
                user = await get_user_by_tg_id(session, message.from_user.id)
                if user:
                    user.role = UserRole.TEACHER
                    user.max_tests = req.max_tests
                    user.max_students = req.max_students
                    user.expires_at = req.expires_at
                else:
                    user = User(
                        tg_user_id=message.from_user.id,
                        full_name=req.full_name,
                        role=UserRole.TEACHER,
                        lang_code=lang,
                        max_tests=req.max_tests,
                        max_students=req.max_students,
                        expires_at=req.expires_at,
                    )
                    session.add(user)

                req.status = "used"
                req.tg_user_id = message.from_user.id
                await session.commit()

                await state.clear()
                await message.answer(
                    "✅ Telefon raqamingiz orqali profilingiz faollashtirildi!\n"
                    "O'qituvchi paneliga xush kelibsiz!",
                    reply_markup=ReplyKeyboardRemove(),
                )
                await message.answer(
                    "👨‍🏫 O'qituvchi paneli:",
                    reply_markup=teacher_panel_kb(),
                )
                return

            elif req.status == "pending":
                await message.answer(
                    "⏳ Sizning arizangiz kutilmoqda holatida.\n"
                    "Admin arizangizni tasdiqlaganidan so'ng, telefon raqamingizni qayta ulashib kirishingiz mumkin."
                )
                return

            elif req.status == "rejected":
                await message.answer(
                    "❌ Sizning arizangiz rad etilgan. Iltimos, administrator bilan bog'laning."
                )
                return

            elif req.status == "used":
                # Already approved and registered, let them log in directly
                user = await get_user_by_tg_id(session, message.from_user.id)
                if user:
                    user.role = UserRole.TEACHER
                    user.max_tests = req.max_tests
                    user.max_students = req.max_students
                    user.expires_at = req.expires_at
                else:
                    user = User(
                        tg_user_id=message.from_user.id,
                        full_name=req.full_name,
                        role=UserRole.TEACHER,
                        lang_code=lang,
                        max_tests=req.max_tests,
                        max_students=req.max_students,
                        expires_at=req.expires_at,
                    )
                    session.add(user)
                await session.commit()

                await state.clear()
                await message.answer(
                    "✅ O'qituvchi paneliga xush kelibsiz!",
                    reply_markup=ReplyKeyboardRemove(),
                )
                await message.answer(
                    "👨‍🏫 O'qituvchi paneli:",
                    reply_markup=teacher_panel_kb(),
                )
                return

        # If no request exists, create a new pending request
        db_phone = f"+{phone}" if not phone.startswith("+") else phone
        req_name = data.get("full_name") or message.from_user.full_name or "O'qituvchi"
        await create_access_request(
            session=session,
            tg_user_id=message.from_user.id,
            full_name=req_name,
            tg_username=message.from_user.username,
            phone_number=db_phone,
        )

        await message.answer(
            "📩 <b>Kirish arizangiz qabul qilindi!</b>\n\n"
            "Arizangiz ko'rib chiqilishi uchun administratorga yuborildi. "
            "Tasdiqlangandan so'ng, telefon raqamingizni qayta ulashib to'g'ridan-to'g'ri kirishingiz "
            "yoki sizga berilgan parol orqali kirishingiz mumkin bo'ladi.",
            parse_mode="HTML"
        )






# ── Panel shortcut ──────────────────────────────────────────
@router.callback_query(F.data == "t_panel")
async def cb_panel(call: CallbackQuery):
    await call.message.edit_text(
        "👨‍🏫 O'qituvchi paneli:", reply_markup=teacher_panel_kb()
    )
    await call.answer()


# ── New test: title ─────────────────────────────────────────
@router.callback_query(F.data == "t_new")
async def cb_new_test(call: CallbackQuery, state: FSMContext):
    async with async_session() as session:
        user = await get_user_by_tg_id(session, call.from_user.id)
        if not user or user.role != UserRole.TEACHER:
            await call.answer("❌ Siz o'qituvchi emassiz.", show_alert=True)
            return

        if not user.is_active:
            await call.message.edit_text("⚠️ Akkauntingiz faol emas. Iltimos, administrator bilan bog'laning.")
            await call.answer()
            return

        if user.expires_at and user.expires_at < datetime.now(timezone.utc):
            await call.message.edit_text("⚠️ Obuna muddatingiz tugagan. Iltimos, administrator bilan bog'laning.")
            await call.answer()
            return

        stmt = select(func.count(Test.id)).where(Test.teacher_id == user.id)
        res = await session.execute(stmt)
        total_tests = res.scalar() or 0
        if total_tests >= user.max_tests:
            await call.message.edit_text(
                f"⚠️ Test yaratish limiti tugadi. Limitingiz: {user.max_tests} ta test.\n"
                "Limitni oshirish uchun administrator bilan bog'laning."
            )
            await call.answer()
            return

    await state.set_state(TeacherSG.newtest_title)
    await call.message.edit_text("📝 Test nomini kiriting:")
    await call.answer()


@router.message(TeacherSG.newtest_title, F.text)
async def teacher_test_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text.strip())
    await state.set_state(TeacherSG.upload_file)
    await message.answer(
        "📎 Savollar faylini yuboring (.docx / .pdf / .txt):"
    )


# ── Upload & parse file ─────────────────────────────────────
@router.message(TeacherSG.upload_file, F.document)
async def teacher_upload(message: Message, state: FSMContext):
    doc = message.document
    ext = os.path.splitext(doc.file_name or "")[1].lower()
    if ext not in (".docx", ".pdf", ".txt"):
        await message.answer("⚠️ Faqat .docx, .pdf yoki .txt fayllar qabul qilinadi.")
        return

    # Download file to memory buffer (avoids Windows temp file locking)
    bot: Bot = message.bot
    file_obj = await bot.get_file(doc.file_id)
    buf = io.BytesIO()
    await bot.download_file(file_obj.file_path, buf)
    buf.seek(0)

    # Save to temp file for parsing
    tmp_path = os.path.join(tempfile.gettempdir(), f"eduquiz_{doc.file_id}{ext}")
    with open(tmp_path, "wb") as f:
        f.write(buf.read())

    # Parse
    try:
        parsed = parse_file(tmp_path)
    except Exception as e:
        logger.exception("Parse failed: %s", e)
        os.unlink(tmp_path)
        await message.answer(f"⚠️ Faylni o'qishda xato: {e}")
        return
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

    if not parsed:
        await message.answer("⚠️ Fayldan savollar topilmadi. Boshqa fayl yuboring.")
        return

    data = await state.get_data()
    title = data["title"]

    # Create test + add questions
    try:
        async with async_session() as session:
            db_user = await get_user_by_tg_id(session, message.from_user.id)
            if not db_user:
                await message.answer("Siz ro'yxatdan o'tmagansiz!")
                return
            test = await create_test(session, db_user.id, title)
            for i, pq in enumerate(parsed, 1):
                opts = []
                # Support up to 10 options (A-J)
                for po in pq.options[:10]:
                    opts.append({
                        "label": po.label,
                        "text": po.text,
                        "is_correct": po.label == pq.correct_label,
                    })
                # Determine max label among parsed options, defaulting to at least 'D'
                max_label = "D"
                for o in opts:
                    lbl = o["label"]
                    if len(lbl) == 1 and lbl.isupper() and lbl > max_label:
                        max_label = lbl

                # Fill missing options up to max_label with placeholders
                existing_labels = {o["label"] for o in opts}
                expected_labels = [chr(c) for c in range(ord("A"), ord(max_label) + 1)]
                for lbl in expected_labels:
                    if lbl not in existing_labels:
                        opts.append({"label": lbl, "text": "—", "is_correct": False})
                opts.sort(key=lambda x: x["label"])
                await add_question(session, test.id, i, pq.text, opts)

        # Upload question images to Telegram and save file_ids
        bot: Bot = message.bot
        async with async_session() as session:
            test_full = await get_test_full(session, test.id)
            for q, pq in zip(test_full.questions, parsed):
                if pq.image_bytes:
                    try:
                        from PIL import Image
                        from io import BytesIO
                        img = Image.open(BytesIO(pq.image_bytes))
                        logger.info(
                            "Question %d image: %dx%d, %d bytes",
                            q.id, img.width, img.height, len(pq.image_bytes),
                        )
                        img_msg = await bot.send_photo(
                            chat_id=message.chat.id,
                            photo=BufferedInputFile(pq.image_bytes, filename=f"q{q.id}.jpg"),
                        )
                        file_id = img_msg.photo[-1].file_id
                        # Delete the temporary photo message
                        await bot.delete_message(
                            chat_id=message.chat.id, message_id=img_msg.message_id
                        )
                        await set_question_image(session, q.id, file_id)
                        logger.info("Question %d image uploaded: file_id=%s", q.id, file_id)
                    except Exception as e:
                        logger.warning("Failed to upload question %d image: %s", q.id, e)
    except Exception as e:
        logger.exception("DB error creating test: %s", e)
        await message.answer(f"⚠️ Test yaratishda xato: {e}")
        return

    await state.update_data(test_id=test.id, q_count=len(parsed))

    # Check if any questions are missing correct answers
    needs_marking = any(pq.correct_label is None for pq in parsed)

    if needs_marking:
        # Ask if teacher has a separate answers file
        await state.set_state(TeacherSG.ask_answers_file)
        await message.answer(
            f"📋 <b>{html.escape(title)}</b> — {len(parsed)} ta savol yuklandi.\n\n"
            f"Savollarda to'g'ri javoblar belgilanmagan.\n"
            f"Javoblar yozilgan alohida faylingiz bormi?\n\n"
            f"Format: <code>1. A  2. B  3. C ...</code>",
            parse_mode="HTML",
            reply_markup=answers_file_prompt_kb(),
        )
        return

    # All answers already known from the file — go to review
    await _go_to_review(message, state, test.id, title, parsed)


@router.message(TeacherSG.upload_file, F.text)
async def teacher_upload_text_fallback(message: Message, state: FSMContext):
    """Remind user to send a file, not text."""
    await message.answer("📎 Iltimos, fayl yuboring (.docx / .pdf / .txt / .xlsx).")


# ── Answers file prompt handlers ─────────────────────────────
@router.callback_query(TeacherSG.ask_answers_file, F.data == "answers_yes")
async def cb_answers_yes(call: CallbackQuery, state: FSMContext):
    """Teacher has a separate answers file."""
    await state.set_state(TeacherSG.upload_answers)
    await call.message.edit_text(
        "📎 Javoblar faylini yuboring (.docx / .pdf / .txt / .xlsx):\n\n"
        "Format: <code>1. A  2. B  3. C ...</code>",
        parse_mode="HTML",
    )
    await call.answer()


@router.callback_query(TeacherSG.ask_answers_file, F.data == "answers_no")
async def cb_answers_no(call: CallbackQuery, state: FSMContext):
    """Teacher doesn't have a separate answers file — go to manual marking."""
    data = await state.get_data()
    test_id = data["test_id"]

    # Fetch questions for marking
    async with async_session() as session:
        test_full = await get_test_full(session, test_id)
    if not test_full or not test_full.questions:
        await call.message.edit_text("⚠️ Test topilmadi.")
        await state.clear()
        await call.answer()
        return

    question_ids = [q.id for q in test_full.questions]
    await state.update_data(mark_question_ids=question_ids, mark_index=0)
    await state.set_state(TeacherSG.mark_correct)

    # Send first question for marking
    first_q = test_full.questions[0]
    q_data = {
        "id": first_q.id,
        "text": first_q.text,
        "image_file_id": first_q.image_file_id,
        "options": [{"label": o.label, "text": o.text} for o in first_q.options],
    }
    q_total = len(test_full.questions)
    q_text = html.escape(q_data["text"])
    text = (
        f"📝 <b>Savol 1/{q_total}</b>\n\n"
        f"{q_text}\n\n"
        f"To'g'ri javobni tanlang:"
    )
    kb = mark_answer_kb(q_data["id"], q_data["options"])
    if q_data["image_file_id"]:
        await call.message.answer_photo(
            photo=q_data["image_file_id"], caption=text,
            parse_mode="HTML", reply_markup=kb,
        )
    else:
        await call.message.answer(text, parse_mode="HTML", reply_markup=kb)
    await call.answer()


# ── Answers file upload handler ──────────────────────────────
@router.message(TeacherSG.upload_answers, F.document)
async def teacher_upload_answers(message: Message, state: FSMContext):
    """Parse the answers file and match correct answers to questions."""
    doc = message.document
    ext = os.path.splitext(doc.file_name or "")[1].lower()
    if ext not in (".docx", ".pdf", ".txt", ".xlsx", ".xls"):
        await message.answer("⚠️ .docx, .pdf, .txt yoki .xlsx fayl yuboring.")
        return

    # Download file
    bot: Bot = message.bot
    file_obj = await bot.get_file(doc.file_id)
    buf = io.BytesIO()
    await bot.download_file(file_obj.file_path, buf)
    buf.seek(0)

    tmp_path = os.path.join(tempfile.gettempdir(), f"eduquiz_ans_{doc.file_id}{ext}")
    with open(tmp_path, "wb") as f:
        f.write(buf.read())

    # Parse answer key
    try:
        answer_key = parse_answer_key(tmp_path)
    except Exception as e:
        logger.exception("Answer parse failed: %s", e)
        os.unlink(tmp_path)
        await message.answer(f"⚠️ Javoblar faylini o'qishda xato: {e}")
        return
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

    if not answer_key:
        await message.answer(
            "⚠️ Javoblar topilmadi. Format: <code>1. A  2. B  3. C ...</code>\n"
            "Qayta urinib ko'ring yoki qo'lda belgilang.",
            parse_mode="HTML",
            reply_markup=answers_file_prompt_kb(),
        )
        await state.set_state(TeacherSG.ask_answers_file)
        return

    data = await state.get_data()
    test_id = data["test_id"]

    # Match answers to questions by position number
    async with async_session() as session:
        test_full = await get_test_full(session, test_id)
    if not test_full:
        await message.answer("⚠️ Test topilmadi.")
        await state.clear()
        return

    matched = 0
    for i, q in enumerate(test_full.questions, 1):
        if i in answer_key:
            async with async_session() as session:
                await set_correct_answer(session, q.id, answer_key[i])
            matched += 1

    await message.answer(
        f"✅ {matched}/{len(test_full.questions)} ta savolga javob moslandi!"
    )

    # Check if any are still unmarked
    if matched < len(test_full.questions):
        # Some questions still need manual marking
        unanswered_ids = [
            q.id for i, q in enumerate(test_full.questions, 1)
            if i not in answer_key
        ]
        await state.update_data(mark_question_ids=unanswered_ids, mark_index=0)
        await state.set_state(TeacherSG.mark_correct)

        # Load first unanswered question
        async with async_session() as session:
            first_q = await get_question_with_options(session, unanswered_ids[0])
        if first_q:
            q_data = {
                "id": first_q.id,
                "text": first_q.text,
                "options": [{"label": o.label, "text": o.text} for o in first_q.options],
            }
            q_total = len(unanswered_ids)
            text = (
                f"📝 <b>Qolgan savol 1/{q_total}</b>\n\n"
                f"{html.escape(q_data['text'])}\n\n"
                f"To'g'ri javobni tanlang:"
            )
            await message.answer(
                text, parse_mode="HTML",
                reply_markup=mark_answer_kb(q_data["id"], q_data["options"]),
            )
        return

    # All matched — go to review
    async with async_session() as session:
        test = await get_test_full(session, test_id)
    await _send_review_message(message, state, test)


@router.message(TeacherSG.upload_answers, F.text)
async def teacher_answers_text_fallback(message: Message, state: FSMContext):
    """Remind to send a file."""
    await message.answer("📎 Javoblar faylini yuboring (.docx / .pdf / .txt / .xlsx).")


# ── Helpers ──────────────────────────────────────────────────
async def _go_to_review(message: Message, state: FSMContext, test_id: int, title: str, parsed):
    """Transition to the review state with preview."""
    await state.set_state(TeacherSG.review_questions)

    safe_title = html.escape(title)
    preview = f"📋 <b>{safe_title}</b>\n❓ Savollar soni: <b>{len(parsed)}</b>\n\n"
    for i, q in enumerate(parsed[:3], 1):
        preview += f"<b>{i}. {html.escape(q.text[:80])}</b>\n"
        for po in q.options[:4]:
            marker = "✅" if po.label == q.correct_label else "  "
            preview += f"  {marker} <b>{po.label})</b> {html.escape(po.text)}\n"
        preview += "\n"
    if len(parsed) > 3:
        preview += f"  ... va yana {len(parsed) - 3} ta savol\n\n"
    preview += "Savollarni tasdiqlaysizmi?"

    await message.answer(preview, parse_mode="HTML", reply_markup=confirm_review_kb(test_id))


async def _send_review_message(message: Message, state: FSMContext, test):
    """Send review message using DB-loaded test data."""
    await state.set_state(TeacherSG.review_questions)

    safe_title = html.escape(test.title)
    q_count = len(test.questions)
    preview = f"📋 <b>{safe_title}</b>\n❓ Savollar soni: <b>{q_count}</b>\n\n"
    for i, q in enumerate(test.questions[:3], 1):
        preview += f"<b>{i}. {html.escape(q.text[:80])}</b>\n"
        for opt in q.options:
            marker = "✅" if opt.is_correct else "  "
            preview += f"  {marker} <b>{opt.label})</b> {html.escape(opt.text)}\n"
        preview += "\n"
    if q_count > 3:
        preview += f"  ... va yana {q_count - 3} ta savol\n\n"
    preview += "Savollarni tasdiqlaysizmi?"

    await message.answer(preview, parse_mode="HTML", reply_markup=confirm_review_kb(test.id))


# ── Review confirmation → settings ──────────────────────────
@router.callback_query(TeacherSG.review_questions, F.data.startswith("qconfirm_"))
async def cb_confirm_questions(call: CallbackQuery, state: FSMContext):
    test_id = int(call.data.split("_", 1)[1])
    await state.update_data(test_id=test_id)
    await state.set_state(TeacherSG.settings_time)
    await call.message.edit_text(
        "⏱️ Bu test uchun vaqt chegarasi belgilansinmi?",
        reply_markup=time_toggle_kb(test_id),
    )
    await call.answer()


@router.callback_query(TeacherSG.review_questions, F.data.startswith("qreupload_"))
async def cb_reupload(call: CallbackQuery, state: FSMContext):
    await state.set_state(TeacherSG.upload_file)
    await call.message.edit_text("📎 Yangi fayl yuboring (.docx / .pdf / .txt):")
    await call.answer()


# ── Mark correct answers ────────────────────────────────────
@router.callback_query(TeacherSG.mark_correct, F.data.startswith("mark_"))
async def cb_mark_answer(call: CallbackQuery, state: FSMContext):
    """Teacher picked the correct answer for a question."""
    # Parse: mark_{question_id}_{label}
    parts = call.data.split("_")
    question_id = int(parts[1])
    selected_label = parts[2]

    data = await state.get_data()
    question_ids = data["mark_question_ids"]
    mark_index = data["mark_index"]
    test_id = data["test_id"]

    # Save the correct answer
    async with async_session() as session:
        await set_correct_answer(session, question_id, selected_label)

    # Move to next question
    mark_index += 1

    if mark_index >= len(question_ids):
        # All questions marked — go to review
        await state.set_state(TeacherSG.review_questions)

        async with async_session() as session:
            test = await get_test_full(session, test_id)
            # Extract data inside session with correct answers
            safe_title = html.escape(test.title)
            q_count = len(test.questions)
            q_preview = []
            for i, q in enumerate(test.questions[:3], 1):
                q_preview.append(f"<b>{i}. {html.escape(q.text[:80])}</b>")
                for opt in q.options:
                    marker = "✅" if opt.is_correct else "  "
                    q_preview.append(f"  {marker} <b>{opt.label})</b> {html.escape(opt.text)}")
                q_preview.append("")

        preview = f"✅ Barcha javoblar belgilandi!\n\n"
        preview += f"📋 <b>{safe_title}</b>\n❓ Savollar soni: <b>{q_count}</b>\n\n"
        preview += "\n".join(q_preview) + "\n"
        if q_count > 3:
            preview += f"  ... va yana {q_count - 3} ta savol\n\n"
        preview += "Savollarni tasdiqlaysizmi?"

        # Handle transition from photo message to text review
        if call.message.photo:
            try:
                await call.message.delete()
            except Exception:
                pass
            await call.message.answer(
                preview, parse_mode="HTML", reply_markup=confirm_review_kb(test_id)
            )
        else:
            await call.message.edit_text(
                preview, parse_mode="HTML", reply_markup=confirm_review_kb(test_id)
            )
        await call.answer()
        return

    await state.update_data(mark_index=mark_index)

    # Load next question for marking inside session
    async with async_session() as session:
        test = await get_test_full(session, test_id)
        q = test.questions[mark_index]
        q_data = {
            "id": q.id,
            "text": q.text,
            "image_file_id": q.image_file_id,
            "options": [{"label": o.label, "text": o.text} for o in q.options],
        }
        q_total = len(test.questions)

    # Replace current message directly with next question (like a story)
    q_text = html.escape(q_data["text"])
    text = (
        f"📝 <b>Savol {mark_index + 1}/{q_total}</b>\n\n"
        f"{q_text}\n\n"
        f"To'g'ri javobni tanlang:"
    )
    kb = mark_answer_kb(q_data["id"], q_data["options"])

    # If current message is a photo, we must delete it and send a new one
    # (Telegram doesn't allow edit_text on photo messages)
    if call.message.photo:
        try:
            await call.message.delete()
        except Exception:
            pass
        if q_data["image_file_id"]:
            await call.message.answer_photo(
                photo=q_data["image_file_id"],
                caption=text,
                parse_mode="HTML",
                reply_markup=kb,
            )
        else:
            await call.message.answer(
                text, parse_mode="HTML",
                reply_markup=kb,
            )
    else:
        # Current message is text — try to edit, or delete+resend if it fails
        if q_data["image_file_id"]:
            try:
                await call.message.delete()
            except Exception:
                pass
            await call.message.answer_photo(
                photo=q_data["image_file_id"],
                caption=text,
                parse_mode="HTML",
                reply_markup=kb,
            )
        else:
            await call.message.edit_text(
                text, parse_mode="HTML",
                reply_markup=kb,
            )
    await call.answer(f"✅ {selected_label}) belgilandi")


async def _send_mark_question(message, test, index: int):
    """Send a question for the teacher to mark the correct answer.
    NOTE: test must be loaded inside a session before calling this."""
    q = test.questions[index]
    total = len(test.questions)
    q_text = html.escape(q.text)

    # Build option list for display (extract inside session-safe way)
    options = [{"label": o.label, "text": o.text} for o in q.options]

    text = (
        f"📝 <b>Savol {index + 1}/{total}</b>\n\n"
        f"{q_text}\n\n"
        f"To'g'ri javobni tanlang:"
    )
    kb = mark_answer_kb(q.id, options)

    if q.image_file_id:
        await message.answer_photo(
            photo=q.image_file_id,
            caption=text,
            parse_mode="HTML",
            reply_markup=kb,
        )
    else:
        await message.answer(
            text,
            parse_mode="HTML",
            reply_markup=kb,
        )


# ── Time settings ───────────────────────────────────────────
@router.callback_query(TeacherSG.settings_time, F.data.startswith("time_yes_"))
async def cb_time_yes(call: CallbackQuery, state: FSMContext):
    test_id = int(call.data.rsplit("_", 1)[1])
    await state.update_data(test_id=test_id, set_time=True)
    await call.message.edit_text("Necha daqiqa? (masalan: 50)")
    await call.answer()


@router.callback_query(TeacherSG.settings_time, F.data.startswith("time_no_"))
async def cb_time_no(call: CallbackQuery, state: FSMContext):
    test_id = int(call.data.rsplit("_", 1)[1])
    async with async_session() as session:
        await update_test_settings(session, test_id, time_limit_minutes=None)
        test = await get_test_full(session, test_id)
    await state.clear()
    await call.message.edit_text(
        f"✅ Test tayyor! (draft)\n🔑 Kod: <code>{test.code}</code>",
        parse_mode="HTML",
        reply_markup=test_manage_kb(test),
    )
    await call.answer()


@router.message(TeacherSG.settings_time, F.text.regexp(r"^\d+$"))
async def teacher_time_input(message: Message, state: FSMContext):
    minutes = int(message.text.strip())
    if minutes <= 0 or minutes > 600:
        await message.answer("⚠️ Vaqt 1-600 daqiqa orasida bo'lishi kerak.")
        return

    data = await state.get_data()
    test_id = data["test_id"]

    async with async_session() as session:
        await update_test_settings(session, test_id, time_limit_minutes=minutes)
        test = await get_test_full(session, test_id)

    await state.clear()
    await message.answer(
        f"✅ Test tayyor! (draft)\n⏱️ Vaqt: {minutes} daqiqa",
        parse_mode="HTML",
        reply_markup=test_manage_kb(test),
    )


# ── Test list ───────────────────────────────────────────────
@router.callback_query(F.data == "t_list")
async def cb_test_list(call: CallbackQuery):
    async with async_session() as session:
        user = await get_user_by_tg_id(session, call.from_user.id)
        if not user:
            await call.answer("Foydalanuvchi topilmadi", show_alert=True)
            return
        tests = await list_teacher_tests(session, user.id)
    if not tests:
        await call.message.edit_text(
            "📋 Hozircha test yo'q.", reply_markup=teacher_panel_kb()
        )
    else:
        await call.message.edit_text(
            "📋 Testlaringiz:", reply_markup=test_list_kb(tests)
        )
    await call.answer()


# ── Test manage ─────────────────────────────────────────────
@router.callback_query(F.data.startswith("tmanage_"))
async def cb_test_manage(call: CallbackQuery):
    test_id = int(call.data.split("_", 1)[1])
    async with async_session() as session:
        test = await get_test_full(session, test_id)
    if not test:
        await call.answer("Test topilmadi", show_alert=True)
        return
    time_info = f"⏱️ Vaqt: {test.time_limit_minutes} daq" if test.time_limit_minutes else "⏱️ Vaqt: cheksiz"
    await call.message.edit_text(
        f"📋 <b>{html.escape(test.title)}</b>\n"
        f"🔑 Kod: <code>{test.code}</code>\n"
        f"📊 Status: <b>{test.status.value}</b>\n"
        f"❓ Savollar: {len(test.questions)}\n"
        f"{time_info}",
        parse_mode="HTML",
        reply_markup=test_manage_kb(test),
    )
    await call.answer()


# ── View questions with correct answers ─────────────────────
QUESTIONS_PER_PAGE = 3


@router.callback_query(F.data.startswith("tview_"))
async def cb_view_questions(call: CallbackQuery):
    """Show test questions with options and correct answers (paginated)."""
    parts = call.data.split("_")
    test_id = int(parts[1])
    page = int(parts[2])

    async with async_session() as session:
        test = await get_test_full(session, test_id)
    if not test or not test.questions:
        await call.answer("Savollar topilmadi", show_alert=True)
        return

    questions = test.questions
    total = len(questions)
    total_pages = (total + QUESTIONS_PER_PAGE - 1) // QUESTIONS_PER_PAGE
    page = min(page, total_pages - 1)

    start = page * QUESTIONS_PER_PAGE
    end = min(start + QUESTIONS_PER_PAGE, total)

    text = f"📋 <b>{html.escape(test.title)}</b> — savollar\n\n"
    for idx in range(start, end):
        q = questions[idx]
        img_tag = " 🖼️" if q.image_file_id else ""
        text += f"<b>{idx + 1}. {html.escape(q.text)}</b>{img_tag}\n"
        for opt in q.options:
            marker = "✅" if opt.is_correct else "  "
            text += f"  {marker} <b>{opt.label})</b> {html.escape(opt.text)}\n"
        text += "\n"

    text += f"📄 Sahifa {page + 1}/{total_pages}"

    await call.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=question_viewer_kb(test_id, page, total_pages),
    )
    await call.answer()


@router.callback_query(F.data == "noop")
async def cb_noop(call: CallbackQuery):
    """Do nothing — used for non-interactive buttons."""
    await call.answer()


# ── Open / Close test ───────────────────────────────────────
@router.callback_query(F.data.startswith("topen_"))
async def cb_open_test(call: CallbackQuery):
    test_id = int(call.data.split("_", 1)[1])
    async with async_session() as session:
        test = await set_test_status(session, test_id, TestStatus.OPEN)
    if not test:
        await call.answer("Test topilmadi", show_alert=True)
        return
    await call.message.edit_text(
        f"🟢 Test ochildi!\n🔑 Kod: <code>{test.code}</code>\n\n"
        f"Talabalar endi bu kodni kirita oladi.",
        parse_mode="HTML",
        reply_markup=test_manage_kb(test),
    )
    await call.answer("Test ochildi")


@router.callback_query(F.data.startswith("tclose_"))
async def cb_close_test(call: CallbackQuery):
    test_id = int(call.data.split("_", 1)[1])
    async with async_session() as session:
        test = await set_test_status(session, test_id, TestStatus.CLOSED)
    if not test:
        await call.answer("Test topilmadi", show_alert=True)
        return
    await call.message.edit_text(
        "🔴 Test yopildi!",
        reply_markup=test_manage_kb(test),
    )
    await call.answer("Test yopildi")


# ── Export results ──────────────────────────────────────────
@router.callback_query(F.data.startswith("texp_"))
async def cb_export(call: CallbackQuery):
    test_id = int(call.data.split("_", 1)[1])
    try:
        async with async_session() as session:
            buf = await export_test_results_xlsx(session, test_id)
        await call.message.answer_document(
            BufferedInputFile(buf.read(), filename=f"results_{test_id}.xlsx"),
            caption="📥 Natijalar (Excel)",
        )
    except Exception as e:
        logger.exception("Export failed: %s", e)
        await call.answer(f"Export xatosi: {e}", show_alert=True)
        return
    await call.answer()


# ── Results viewer ──────────────────────────────────────────
@router.callback_query(F.data.startswith("tresults_"))
async def cb_results(call: CallbackQuery):
    """Show student results for a test in the bot."""
    test_id = int(call.data.split("_", 1)[1])

    async with async_session() as session:
        test = await get_test_full(session, test_id)
        attempts = await get_test_results(session, test_id)

    if not test:
        await call.answer("Test topilmadi", show_alert=True)
        return

    # Extract data inside session
    test_title = html.escape(test.title)
    results_data = []
    for att in attempts:
        student_name = html.escape(att.student.full_name) if att.student else "Noma'lum"
        results_data.append({
            "name": student_name,
            "score": att.score or 0,
            "max_score": att.max_score or 0,
            "percent": float(att.percent or 0),
            "status": att.status,
        })

    if not results_data:
        await call.message.edit_text(
            f"📊 <b>{test_title}</b>\n\nHali hech kim test topshirmagan.",
            parse_mode="HTML",
            reply_markup=test_manage_kb(test),
        )
        await call.answer()
        return

    # Build results text
    text = f"📊 <b>{test_title}</b> — Natijalar\n\n"
    finished = [r for r in results_data if r["status"] in ("finished", "expired")]
    in_progress = [r for r in results_data if r["status"] == "in_progress"]

    if finished:
        # Sort by score descending
        finished.sort(key=lambda x: x["score"], reverse=True)
        for i, r in enumerate(finished, 1):
            status_icon = "🏆" if i == 1 else "📝"
            emoji = "🟢" if r["percent"] >= 70 else ("🟡" if r["percent"] >= 50 else "🔴")
            text += (
                f"{status_icon} <b>{i}.</b> {r['name']}\n"
                f"    {emoji} {r['score']}/{r['max_score']} ({r['percent']:.0f}%)\n"
            )
    if in_progress:
        text += f"\n⏳ Jarayonda: {len(in_progress)} ta o'quvchi\n"

    text += f"\n👥 Jami: {len(results_data)} ta urinish"

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    back_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Orqaga", callback_data=f"tmanage_{test_id}")],
    ])

    await call.message.edit_text(text, parse_mode="HTML", reply_markup=back_kb)
    await call.answer()


# ── Settings ────────────────────────────────────────────────
@router.callback_query(F.data.startswith("tset_"))
async def cb_settings(call: CallbackQuery, state: FSMContext):
    """Show or handle test settings."""
    parts = call.data.split("_", 2)  # tset_{action}_{id} or tset_{id}
    if len(parts) == 2:
        # tset_{test_id} — show settings menu
        test_id = int(parts[1])
        async with async_session() as session:
            test = await get_test_full(session, test_id)
            if not test:
                await call.answer("Test topilmadi", show_alert=True)
                return
        await call.message.edit_text(
            f"⚙️ <b>Sozlamalar</b> — {html.escape(test.title)}",
            parse_mode="HTML",
            reply_markup=test_settings_kb(test),
        )
        await call.answer()
        return

    action = parts[1]  # time, attempts, shuffleq, shuffleo
    test_id = int(parts[2])

    if action == "time":
        await state.set_state(TeacherSG.settings_input)
        await state.update_data(settings_test_id=test_id, settings_field="time")
        await call.message.edit_text(
            "⏱️ Vaqt limitini daqiqalarda kiriting (yoki '0' deb yozing — vaqt yo'q):"
        )
        await call.answer()
        return

    if action == "attempts":
        await state.set_state(TeacherSG.settings_input)
        await state.update_data(settings_test_id=test_id, settings_field="attempts")
        await call.message.edit_text(
            "🔢 Urinishlar sonini kiriting (1-10):"
        )
        await call.answer()
        return

    if action == "shuffleq":
        async with async_session() as session:
            test = await get_test_full(session, test_id)
            if test:
                new_val = not test.shuffle_questions
                await update_test_settings(session, test_id, shuffle_questions=new_val)
                test = await get_test_full(session, test_id)
        if test:
            await call.message.edit_reply_markup(reply_markup=test_settings_kb(test))
        await call.answer("✅ O'zgartirildi")
        return

    if action == "shuffleo":
        async with async_session() as session:
            test = await get_test_full(session, test_id)
            if test:
                new_val = not test.shuffle_options
                await update_test_settings(session, test_id, shuffle_options=new_val)
                test = await get_test_full(session, test_id)
        if test:
            await call.message.edit_reply_markup(reply_markup=test_settings_kb(test))
        await call.answer("✅ O'zgartirildi")
        return

    await call.answer()


@router.message(TeacherSG.settings_input, F.text)
async def cb_settings_input(message: Message, state: FSMContext):
    """Handle text input for settings (time limit or attempt limit)."""
    data = await state.get_data()
    test_id = data["settings_test_id"]
    field = data["settings_field"]
    text = message.text.strip()

    async with async_session() as session:
        if field == "time":
            if text in ("0", "yo'q", "yoq", "no"):
                await update_test_settings(session, test_id, time_limit_minutes=None)
                await message.answer("✅ Vaqt limiti olib tashlandi.")
            else:
                try:
                    minutes = int(text)
                    if minutes < 1:
                        raise ValueError
                    await update_test_settings(session, test_id, time_limit_minutes=minutes)
                    await message.answer(f"✅ Vaqt limiti: {minutes} daqiqa.")
                except ValueError:
                    await message.answer("⚠️ Noto'g'ri qiymat. Raqam kiriting.")
                    return

        elif field == "attempts":
            try:
                limit = int(text)
                if limit < 1 or limit > 10:
                    raise ValueError
                await update_test_settings(session, test_id, attempt_limit=limit)
                await message.answer(f"✅ Urinishlar soni: {limit}.")
            except ValueError:
                await message.answer("⚠️ 1 dan 10 gacha raqam kiriting.")
                return

    await state.clear()
    # Show settings menu again
    async with async_session() as session:
        test = await get_test_full(session, test_id)
    if test:
        await message.answer(
            f"⚙️ <b>Sozlamalar</b> — {html.escape(test.title)}",
            parse_mode="HTML",
            reply_markup=test_settings_kb(test),
        )


# ── Stats ───────────────────────────────────────────────────
@router.callback_query(F.data == "t_stats")
async def cb_stats(call: CallbackQuery):
    """Show overall statistics for the teacher."""
    async with async_session() as session:
        user = await get_user_by_tg_id(session, call.from_user.id)
        if not user:
            await call.answer("Foydalanuvchi topilmadi", show_alert=True)
            return

        # Count tests by status
        stmt = (
            select(Attempt.status, func.count())
            .join(Attempt.test)
            .where(Attempt.test.has(teacher_id=user.id))
            .group_by(Attempt.status)
        )
        from app.db.models import Test as TestModel
        stmt = (
            select(func.count())
            .select_from(TestModel)
            .where(TestModel.teacher_id == user.id)
        )
        total_tests = (await session.execute(stmt)).scalar_one()

        # Total attempts across all teacher's tests
        from sqlalchemy import and_
        stmt2 = (
            select(func.count())
            .select_from(Attempt)
            .join(TestModel, Attempt.test_id == TestModel.id)
            .where(TestModel.teacher_id == user.id)
        )
        total_attempts = (await session.execute(stmt2)).scalar_one()

        # Finished attempts
        stmt3 = (
            select(func.count())
            .select_from(Attempt)
            .join(TestModel, Attempt.test_id == TestModel.id)
            .where(TestModel.teacher_id == user.id, Attempt.status.in_(["finished", "expired"]))
        )
        finished_attempts = (await session.execute(stmt3)).scalar_one()

    from app.keyboards.common import back_kb
    await call.message.edit_text(
        f"📊 <b>Statistika</b>\n\n"
        f"📋 Jami testlar: <b>{total_tests}</b>\n"
        f"👥 Jami urinishlar: <b>{total_attempts}</b>\n"
        f"✅ Yakunlangan: <b>{finished_attempts}</b>",
        parse_mode="HTML",
        reply_markup=teacher_panel_kb(),
    )
    await call.answer()


# ── /newtest command shortcut ───────────────────────────────
@router.message(Command("newtest"))
async def cmd_newtest(message: Message, state: FSMContext):
    """Shortcut command to start creating a new test."""
    user = await _ensure_teacher(message.from_user.id)
    if not user:
        await message.answer("⚠️ Bu buyruq faqat o'qituvchilar uchun.")
        return
    await state.set_state(TeacherSG.newtest_title)
    await message.answer("📝 Test nomini kiriting:")
