"""Export results to Excel (.xlsx)."""

from __future__ import annotations

import io

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import Attempt, Question, Test


async def export_test_results_xlsx(session: AsyncSession, test_id: int) -> io.BytesIO:
    """Generate an Excel file with attempt results for a test."""
    from openpyxl import Workbook

    test = await session.get(
        Test,
        test_id,
        options=[selectinload(Test.questions).selectinload(Question.options)],
    )

    stmt = (
        select(Attempt)
        .where(Attempt.test_id == test_id, Attempt.status.in_(["finished", "expired"]))
        .options(selectinload(Attempt.student), selectinload(Attempt.answers))
        .order_by(Attempt.finished_at)
    )
    result = await session.execute(stmt)
    attempts = result.scalars().all()

    wb = Workbook()
    ws = wb.active
    ws.title = "Results"

    # Header
    headers = ["#", "Student", "Score", "Max", "Percent", "Status", "Finished At"]
    ws.append(headers)

    for idx, att in enumerate(attempts, 1):
        ws.append([
            idx,
            att.student.full_name or str(att.student.tg_user_id),
            att.score,
            att.max_score,
            float(att.percent) if att.percent else 0,
            att.status,
            str(att.finished_at) if att.finished_at else "",
        ])

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf
