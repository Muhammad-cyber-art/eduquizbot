"""Student-specific keyboards."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def quiz_option_kb(question_id: int, options: list, attempt_id: int) -> InlineKeyboardMarkup:
    """A/B/C/D answer buttons + back-to-grid button."""
    rows = []
    for opt in options:
        label = opt["label"] if isinstance(opt, dict) else opt.label
        text = opt["text"] if isinstance(opt, dict) else opt.text
        rows.append([
            InlineKeyboardButton(
                text=f"{label}) {text}",
                callback_data=f"ans_{question_id}_{label}",
            )
        ])
    # Back to grid
    rows.append([
        InlineKeyboardButton(text="◀️ Savollar ro'yxati", callback_data=f"sgrid_{attempt_id}"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def question_grid_kb(
    attempt_id: int,
    question_ids: list[int],
    answered_ids: set[int],
) -> InlineKeyboardMarkup:
    """Grid of question number buttons (✅ = answered, ❓ = not yet)."""
    rows = []
    row = []
    for i, qid in enumerate(question_ids):
        marker = "✅" if qid in answered_ids else "❓"
        row.append(
            InlineKeyboardButton(
                text=f"{marker} {i + 1}",
                callback_data=f"sq_{attempt_id}_{qid}",
            )
        )
        if len(row) == 5:
            rows.append(row)
            row = []
    if row:
        rows.append(row)

    # Finish button
    total = len(question_ids)
    answered_count = sum(1 for qid in question_ids if qid in answered_ids)
    finish_text = f"🏁 Yakunlash ({answered_count}/{total})"
    rows.append([
        InlineKeyboardButton(text=finish_text, callback_data=f"sfinish_{attempt_id}"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def start_test_kb(test_id: int) -> InlineKeyboardMarkup:
    """Confirm start test button."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="▶️ Boshlash", callback_data=f"sstart_{test_id}")],
    ])


def finish_result_kb(attempt_id: int) -> InlineKeyboardMarkup:
    """After finishing, show result options."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Natijani ko'rish", callback_data=f"sresult_{attempt_id}")],
        [InlineKeyboardButton(text="🏠 Bosh sahifa", callback_data="s_home")],
    ])
