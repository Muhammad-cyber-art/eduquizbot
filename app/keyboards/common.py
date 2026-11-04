"""Common keyboards shared across flows."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton


def language_kb() -> InlineKeyboardMarkup:
    """Language selection keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="lang_uz"),
            InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru"),
        ],
    ])


def role_kb() -> InlineKeyboardMarkup:
    """Role selection keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👨‍🏫 O'qituvchi", callback_data="role_teacher"),
            InlineKeyboardButton(text="👨‍🎓 Talaba", callback_data="role_student"),
        ],
    ])


def teacher_auth_kb() -> InlineKeyboardMarkup:
    """Teacher authentication options."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔑 Kod kiritish", callback_data="tauth_pin")],
        [InlineKeyboardButton(text="📩 Ruxsat so'rash", callback_data="tauth_request")],
    ])


def back_kb(target: str = "menu") -> InlineKeyboardMarkup:
    """Generic back button."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Orqaga", callback_data=f"back_{target}")],
    ])
