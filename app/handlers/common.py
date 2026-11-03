"""Common handlers — /start, language selection, role selection."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.db.models import UserRole
from app.db.session import async_session
from app.keyboards.common import language_kb, role_kb, teacher_auth_kb
from app.keyboards.teacher import teacher_panel_kb
from app.services.auth import get_or_create_user, get_user_by_tg_id
from app.states import CommonSG, StudentSG, TeacherSG

router = Router(name="common")


# ── /start ──────────────────────────────────────────────────
@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()

    # Check if user already registered
    async with async_session() as session:
        user = await get_user_by_tg_id(session, message.from_user.id)
        if user:
            if user.role == UserRole.TEACHER:
                await message.answer(
                    "👨‍🏫 O'qituvchi paneli:",
                    reply_markup=teacher_panel_kb(),
                )
                return
            else:
                await state.set_state(StudentSG.enter_code)
                await message.answer("🔑 Test kodini kiriting:")
                return

    # New user — ask language
    await state.set_state(CommonSG.language)
    await message.answer(
        "🌐 Tilni tanlang / Выберите язык:",
        reply_markup=language_kb(),
    )


# ── Language selection ──────────────────────────────────────
@router.callback_query(CommonSG.language, F.data.startswith("lang_"))
async def cb_language(call: CallbackQuery, state: FSMContext):
    lang = call.data.split("_", 1)[1]
    await state.update_data(lang=lang)
    await state.set_state(CommonSG.role)
    await call.message.edit_text("👤 Rolingizni tanlang:", reply_markup=role_kb())
    await call.answer()


# ── Role selection ──────────────────────────────────────────
@router.callback_query(CommonSG.role, F.data.startswith("role_"))
async def cb_role(call: CallbackQuery, state: FSMContext):
    role_str = call.data.split("_", 1)[1]
    data = await state.get_data()
    lang = data.get("lang", "uz")
    role = UserRole.TEACHER if role_str == "teacher" else UserRole.STUDENT

    async with async_session() as session:
        user = await get_or_create_user(
            session,
            tg_user_id=call.from_user.id,
            full_name=call.from_user.full_name,
            role=role,
            lang_code=lang,
        )

    if role == UserRole.TEACHER:
        await state.set_state(TeacherSG.pin)
        await call.message.edit_text(
            "👨‍🏫 O'qituvchi sifatida kirish:",
            reply_markup=teacher_auth_kb(),
        )
    else:
        await state.set_state(StudentSG.enter_code)
        await call.message.edit_text("🔑 Test kodini kiriting:")

    await call.answer()


# ── /cancel ─────────────────────────────────────────────────
@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Amal bekor qilindi. /start — qayta boshlash.")


# ── /help ───────────────────────────────────────────────────
@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "📖 <b>EduQuiz Bot</b>\n\n"
        "/start — Boshlash\n"
        "/cancel — Bekor qilish\n"
        "/help — Yordam\n\n"
        "👨‍🏫 <b>O'qituvchi:</b> test yaratadi, boshqaradi, natijalarni ko'radi.\n"
        "👨‍🎓 <b>Talaba:</b> test kodini kiritib, savollarga javob beradi.",
        parse_mode="HTML",
    )
