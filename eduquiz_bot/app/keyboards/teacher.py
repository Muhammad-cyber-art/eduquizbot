"""Teacher-specific keyboards."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

from app.db.models import Test, TestStatus
from app.config import settings


def teacher_panel_kb() -> InlineKeyboardMarkup:
    """Main teacher panel menu."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Yangi test", callback_data="t_new")],
        [InlineKeyboardButton(text="📋 Testlarim", callback_data="t_list")],
        [InlineKeyboardButton(text="📊 Statistika", callback_data="t_stats")],
        [InlineKeyboardButton(text="👤 Profilim", callback_data="t_profile")],
        [InlineKeyboardButton(text="📱 Mini App (Statistika & AI)", web_app=WebAppInfo(url=f"{settings.WEB_URL}/webapp/teacher"))],
    ])



def test_manage_kb(test: Test) -> InlineKeyboardMarkup:
    """Management buttons for a specific test."""
    rows: list[list[InlineKeyboardButton]] = [
        [InlineKeyboardButton(text="📋 Savollarni ko'rish", callback_data=f"tview_{test.id}_0")],
        [InlineKeyboardButton(text="⚙️ Sozlamalar", callback_data=f"tset_{test.id}")],
    ]

    if test.status == TestStatus.DRAFT:
        rows.append([InlineKeyboardButton(text="🟢 Ochish", callback_data=f"topen_{test.id}")])
    elif test.status == TestStatus.OPEN:
        rows.append([InlineKeyboardButton(text="🔴 Yopish", callback_data=f"tclose_{test.id}")])

    rows.append([
        InlineKeyboardButton(text="📊 Natijalar", callback_data=f"tresults_{test.id}"),
        InlineKeyboardButton(text="📥 Excel", callback_data=f"texp_{test.id}"),
    ])
    rows.append([InlineKeyboardButton(text="◀️ Orqaga", callback_data="t_list")])

    return InlineKeyboardMarkup(inline_keyboard=rows)


def test_settings_kb(test: Test) -> InlineKeyboardMarkup:
    """Settings buttons for a specific test."""
    time_text = f"⏱️ Vaqt: {test.time_limit_minutes} min" if test.time_limit_minutes else "⏱️ Vaqt: yo'q"
    shuf_q = f"🔀 Savollar: {'✅' if test.shuffle_questions else '❌'}"
    shuf_o = f"🔀 Variantlar: {'✅' if test.shuffle_options else '❌'}"
    
    # Map test type values to friendly text
    type_map = {"standard": "Imtihon (Standard)", "practice": "Mashq (Instant)", "written": "Yozma (Open)"}
    type_label = type_map.get(getattr(test, "test_type", "standard"), "Imtihon")
    type_text = f"🏷️ Turi: {type_label}"

    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=time_text, callback_data=f"tset_time_{test.id}")],
        [InlineKeyboardButton(text=f"🔢 Urinishlar: {test.attempt_limit}", callback_data=f"tset_attempts_{test.id}")],
        [InlineKeyboardButton(text=type_text, callback_data=f"tset_type_{test.id}")],
        [InlineKeyboardButton(text=shuf_q, callback_data=f"tset_shuffleq_{test.id}")],
        [InlineKeyboardButton(text=shuf_o, callback_data=f"tset_shuffleo_{test.id}")],
        [InlineKeyboardButton(text="◀️ Orqaga", callback_data=f"tmanage_{test.id}")],
    ])


def test_type_kb(test_id: int) -> InlineKeyboardMarkup:
    """Select quiz test type keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Imtihon (Standard)", callback_data=f"tset_settype_{test_id}_standard")],
        [InlineKeyboardButton(text="🚀 Mashq (Instant)", callback_data=f"tset_settype_{test_id}_practice")],
        [InlineKeyboardButton(text="✍️ Yozma (Open-ended)", callback_data=f"tset_settype_{test_id}_written")],
        [InlineKeyboardButton(text="◀️ Orqaga", callback_data=f"tset_{test_id}")],
    ])


def time_toggle_kb(test_id: int) -> InlineKeyboardMarkup:
    """Ask whether to set time limit."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Ha", callback_data=f"time_yes_{test_id}"),
            InlineKeyboardButton(text="❌ Yo'q", callback_data=f"time_no_{test_id}"),
        ],
    ])


def confirm_review_kb(test_id: int) -> InlineKeyboardMarkup:
    """Confirm parsed questions."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"qconfirm_{test_id}"),
            InlineKeyboardButton(text="🔄 Qayta yuklash", callback_data=f"qreupload_{test_id}"),
        ],
    ])


def mark_answer_kb(question_id: int, options: list) -> InlineKeyboardMarkup:
    """Let teacher pick the correct answer for a question."""
    rows = []
    for opt in options:
        label = opt["label"] if isinstance(opt, dict) else opt.label
        text = opt["text"] if isinstance(opt, dict) else opt.text
        rows.append([
            InlineKeyboardButton(
                text=f"{label}) {text}",
                callback_data=f"mark_{question_id}_{label}",
            )
        ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def test_list_kb(tests: list[Test]) -> InlineKeyboardMarkup:
    """List of teacher's tests as inline buttons."""
    rows = []
    for t in tests:
        status_icon = {"draft": "📝", "open": "🟢", "closed": "🔴"}.get(t.status.value, "❓")
        rows.append([
            InlineKeyboardButton(
                text=f"{status_icon} {t.title} [{t.code}]",
                callback_data=f"tmanage_{t.id}",
            )
        ])
    rows.append([InlineKeyboardButton(text="◀️ Panel", callback_data="t_panel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def question_viewer_kb(test_id: int, page: int, total_pages: int) -> InlineKeyboardMarkup:
    """Pagination buttons for viewing questions."""
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="◀️ Oldingi", callback_data=f"tview_{test_id}_{page - 1}"))
    nav.append(InlineKeyboardButton(text=f"{page + 1}/{total_pages}", callback_data="noop"))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton(text="Keyingi ▶️", callback_data=f"tview_{test_id}_{page + 1}"))
    return InlineKeyboardMarkup(inline_keyboard=[
        nav,
        [InlineKeyboardButton(text="◀️ Orqaga", callback_data=f"tmanage_{test_id}")],
    ])


def answers_file_prompt_kb() -> InlineKeyboardMarkup:
    """Ask if teacher has a separate answers file."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Ha, bor", callback_data="answers_yes"),
            InlineKeyboardButton(text="❌ Yo'q", callback_data="answers_no"),
        ],
    ])
