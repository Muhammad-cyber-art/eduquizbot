"""Text formatting utilities for bot messages."""

from __future__ import annotations

from datetime import datetime, timezone


def format_question(
    index: int,
    total: int,
    question_text: str,
    options: list,
    remaining_seconds: int | None = None,
) -> str:
    """Format a quiz question message."""
    sep = "━" * 20
    parts = [sep, f"📝 Savol {index}/{total}"]

    if remaining_seconds is not None and remaining_seconds > 0:
        mm, ss = divmod(remaining_seconds, 60)
        parts.append(f"⏱️ Qolgan vaqt: {mm:02d}:{ss:02d}")

    parts.append(sep)
    parts.append(question_text)
    parts.append("")

    for opt in options:
        label = opt["label"] if isinstance(opt, dict) else opt.label
        text = opt["text"] if isinstance(opt, dict) else opt.text
        parts.append(f"{label}) {text}")

    return "\n".join(parts)


def format_result(score: int, max_score: int, percent: float) -> str:
    """Format test result summary."""
    return (
        f"🏁 <b>Test yakunlandi!</b>\n\n"
        f"✅ To'g'ri javoblar: <b>{score}/{max_score}</b>\n"
        f"📊 Foiz: <b>{percent:.1f}%</b>\n"
        f"{'🎉 Ajoyib natija!' if percent >= 80 else '📚 Yana harakat qiling!'}"
    )


def format_test_info(title: str, code: str, q_count: int, time_limit: int | None) -> str:
    """Format test information for student preview."""
    lines = [
        f"📋 <b>{title}</b>",
        f"🔑 Kod: <code>{code}</code>",
        f"❓ Savollar soni: <b>{q_count}</b>",
    ]
    if time_limit:
        lines.append(f"⏱️ Vaqt chegarasi: <b>{time_limit} daqiqa</b>")
    return "\n".join(lines)


def time_remaining(deadline: datetime | None) -> int | None:
    """Return seconds remaining until deadline, or None if no deadline."""
    if deadline is None:
        return None
    now = datetime.now(timezone.utc)
    # Handle naive datetimes from SQLite (no tzinfo)
    if deadline.tzinfo is None:
        deadline = deadline.replace(tzinfo=timezone.utc)
    delta = deadline - now
    return max(0, int(delta.total_seconds()))
