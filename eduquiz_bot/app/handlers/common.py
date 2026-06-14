"""Common handlers — /start, language selection, role selection."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.db.models import UserRole
from app.db.session import async_session
from app.keyboards.common import language_kb, role_kb, teacher_auth_kb, contact_share_kb
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
                from app.keyboards.student import student_home_kb
                await message.answer("🔑 Test kodini kiriting:", reply_markup=student_home_kb())
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
    await state.set_state(CommonSG.full_name)
    
    prompts = {
        "uz": "✍️ Iltimos, ism va familiyangizni kiriting (Masalan: Ali Valiyev):",
        "ru": "✍️ Пожалуйста, введите ваше имя и фамилию (Например: Иван Иванов):",
        "en": "✍️ Please enter your first and last name (Example: John Doe):"
    }
    await call.message.edit_text(prompts.get(lang, prompts["uz"]))
    await call.answer()


# ── Name entry ──────────────────────────────────────────────
@router.message(CommonSG.full_name, F.text)
async def process_full_name(message: Message, state: FSMContext):
    full_name = message.text.strip()
    data = await state.get_data()
    lang = data.get("lang", "uz")

    if len(full_name) < 4 or " " not in full_name:
        err_msgs = {
            "uz": "⚠️ Iltimos, ism va familiyangizni to'liq kiriting (bo'shliq bilan ajratilgan):",
            "ru": "⚠️ Пожалуйста, введите имя и фамилию полностью (через пробел):",
            "en": "⚠️ Please enter both your first and last name (separated by space):"
        }
        await message.answer(err_msgs.get(lang, err_msgs["uz"]))
        return

    await state.update_data(full_name=full_name)
    await state.set_state(CommonSG.role)
    
    role_msgs = {
        "uz": "👤 Rolingizni tanlang:",
        "ru": "👤 Выберите вашу роль:",
        "en": "👤 Select your role:"
    }
    await message.answer(role_msgs.get(lang, role_msgs["uz"]), reply_markup=role_kb())


# ── Role selection ──────────────────────────────────────────
@router.callback_query(CommonSG.role, F.data.startswith("role_"))
async def cb_role(call: CallbackQuery, state: FSMContext):
    role_str = call.data.split("_", 1)[1]
    data = await state.get_data()
    lang = data.get("lang", "uz")
    full_name = data.get("full_name")
    role = UserRole.TEACHER if role_str == "teacher" else UserRole.STUDENT

    if role == UserRole.TEACHER:
        # Do not create user in DB yet! Save name in FSM state
        await state.update_data(lang=lang, full_name=full_name)
        await state.set_state(TeacherSG.pin)
        
        # Delete selection message to clean chat
        try:
            await call.message.delete()
        except Exception:
            pass
            
        await call.message.answer(
            "👨‍🏫 <b>O'qituvchi paneli</b>\n\n"
            "Tizimga kirish yoki ariza yuborish uchun pastdagi tugmani bosib <b>telefon raqamingizni ulashing</b>.\n\n"
            "<i>Agar sizda allaqachon tasdiqlangan parol yoki PIN-kod bo'lsa, uni to'g'ridan-to'g'ri yozib yuborishingiz ham mumkin.</i>",
            parse_mode="HTML",
            reply_markup=contact_share_kb(),
        )
    else:
        async with async_session() as session:
            await get_or_create_user(
                session,
                tg_user_id=call.from_user.id,
                full_name=full_name,
                role=UserRole.STUDENT,
                lang_code=lang,
            )
        await state.set_state(StudentSG.enter_code)
        from app.keyboards.student import student_home_kb
        await call.message.edit_text("🔑 Test kodini kiriting:", reply_markup=student_home_kb())


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
