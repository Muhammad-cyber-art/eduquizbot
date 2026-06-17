"""Initial PostgreSQL schema — creates the complete EduQuiz database.

Revision ID: 0001
Revises: (none — initial migration)
Create Date: 2026-06-17

This migration:
  1. Creates PostgreSQL native ENUM types: user_role, test_status
  2. Creates all tables in FK-dependency order
  3. Creates all indexes (explicit + implicit from column definitions)
  4. Creates all constraints (PK, FK, UNIQUE, CHECK)

To apply:
    cd eduquiz_bot
    DATABASE_URL=postgresql+asyncpg://... alembic upgrade head

To roll back:
    DATABASE_URL=postgresql+asyncpg://... alembic downgrade base
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ENUM
from alembic import op

# revision identifiers
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# ── PostgreSQL native ENUM types ──────────────────────────────────────────────
# Defined as module-level objects so they can be referenced in both upgrade/downgrade.

user_role_enum = ENUM(
    "teacher", "student", "admin",
    name="user_role",
    create_type=False,
)

test_status_enum = ENUM(
    "draft", "open", "closed",
    name="test_status",
    create_type=False,
)


def upgrade() -> None:
    # ── Step 1: Create PostgreSQL ENUM types ────────────────────────────────
    op.execute("CREATE TYPE user_role AS ENUM ('teacher', 'student', 'admin')")
    op.execute("CREATE TYPE test_status AS ENUM ('draft', 'open', 'closed')")

    # ── Step 2: users ────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), nullable=False, autoincrement=True),
        sa.Column("tg_user_id", sa.BigInteger(), nullable=False),
        sa.Column("full_name", sa.Text(), nullable=True),
        sa.Column(
            "role",
            ENUM("teacher", "student", "admin", name="user_role", create_type=False),
            nullable=False,
        ),
        sa.Column("lang_code", sa.String(5), nullable=False, server_default="uz"),
        sa.Column("max_tests", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("max_students", sa.Integer(), nullable=False, server_default="50"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ai_queries_limit", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("ai_queries_used", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    # Unique constraint + index on tg_user_id (the primary lookup key for bot handlers)
    op.create_index("ix_users_tg_user_id", "users", ["tg_user_id"], unique=True)

    # ── Step 3: teacher_invite_codes ─────────────────────────────────────────
    op.create_table(
        "teacher_invite_codes",
        sa.Column("id", sa.BigInteger(), nullable=False, autoincrement=True),
        sa.Column("code", sa.String(32), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("max_tests", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("max_students", sa.Integer(), nullable=False, server_default="50"),
        sa.Column("ai_queries_limit", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )

    # ── Step 4: access_requests ──────────────────────────────────────────────
    op.create_table(
        "access_requests",
        sa.Column("id", sa.BigInteger(), nullable=False, autoincrement=True),
        sa.Column("tg_user_id", sa.BigInteger(), nullable=False),
        sa.Column("full_name", sa.Text(), nullable=False),
        sa.Column("tg_username", sa.String(64), nullable=True),
        sa.Column("phone_number", sa.String(32), nullable=True),
        sa.Column("max_tests", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("max_students", sa.Integer(), nullable=False, server_default="50"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ai_queries_limit", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("status", sa.String(16), nullable=False, server_default="pending"),
        sa.Column("password", sa.String(128), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_access_requests_tg_user_id", "access_requests", ["tg_user_id"])
    op.create_index("ix_access_requests_phone_number", "access_requests", ["phone_number"])
    op.create_index("ix_access_requests_status", "access_requests", ["status"])

    # ── Step 5: tests ────────────────────────────────────────────────────────
    op.create_table(
        "tests",
        sa.Column("id", sa.BigInteger(), nullable=False, autoincrement=True),
        sa.Column("code", sa.String(16), nullable=False),
        sa.Column("teacher_id", sa.BigInteger(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("difficulty", sa.String(16), nullable=False, server_default="medium"),
        sa.Column("subject", sa.Text(), nullable=True),
        sa.Column(
            "status",
            ENUM("draft", "open", "closed", name="test_status", create_type=False),
            nullable=False,
            server_default="draft",
        ),
        sa.Column("time_limit_minutes", sa.Integer(), nullable=True),
        sa.Column("attempt_limit", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("test_type", sa.String(16), nullable=False, server_default="standard"),
        sa.Column("shuffle_questions", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("shuffle_options", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["teacher_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_index("ix_tests_code", "tests", ["code"])
    op.create_index("ix_tests_teacher_id", "tests", ["teacher_id"])

    # ── Step 6: questions ────────────────────────────────────────────────────
    op.create_table(
        "questions",
        sa.Column("id", sa.BigInteger(), nullable=False, autoincrement=True),
        sa.Column("test_id", sa.BigInteger(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("image_file_id", sa.Text(), nullable=True),
        sa.Column("explanation", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["test_id"], ["tests.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("test_id", "position"),
    )
    op.create_index("ix_questions_test_id", "questions", ["test_id"])

    # ── Step 7: options ──────────────────────────────────────────────────────
    op.create_table(
        "options",
        sa.Column("id", sa.BigInteger(), nullable=False, autoincrement=True),
        sa.Column("question_id", sa.BigInteger(), nullable=False),
        sa.Column("label", sa.String(1), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("is_correct", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.CheckConstraint(
            "label IN ('A','B','C','D','E','F','G','H','I','J')",
            name="ck_option_label",
        ),
        sa.ForeignKeyConstraint(["question_id"], ["questions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("question_id", "label"),
    )
    op.create_index("ix_options_question_id", "options", ["question_id"])

    # ── Step 8: attempts ─────────────────────────────────────────────────────
    op.create_table(
        "attempts",
        sa.Column("id", sa.BigInteger(), nullable=False, autoincrement=True),
        sa.Column("test_id", sa.BigInteger(), nullable=False),
        sa.Column("student_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("deadline_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("score", sa.Integer(), nullable=True),
        sa.Column("max_score", sa.Integer(), nullable=True),
        sa.Column("percent", sa.Numeric(5, 2), nullable=True),
        sa.Column("status", sa.String(16), nullable=False, server_default="in_progress"),
        sa.Column("xp_earned", sa.Integer(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["test_id"], ["tests.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["student_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("test_id", "student_id", "started_at"),
    )
    op.create_index("ix_attempts_test_id", "attempts", ["test_id"])
    op.create_index("ix_attempts_student_id", "attempts", ["student_id"])
    op.create_index("ix_attempts_deadline_at", "attempts", ["deadline_at"])
    op.create_index("ix_attempts_status", "attempts", ["status"])

    # ── Step 9: answers ──────────────────────────────────────────────────────
    op.create_table(
        "answers",
        sa.Column("id", sa.BigInteger(), nullable=False, autoincrement=True),
        sa.Column("attempt_id", sa.BigInteger(), nullable=False),
        sa.Column("question_id", sa.BigInteger(), nullable=False),
        sa.Column("selected_label", sa.String(1), nullable=False),
        sa.Column("selected_text", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "selected_label IN ('A','B','C','D','E','F','G','H','I','J')",
            name="ck_answer_label",
        ),
        sa.ForeignKeyConstraint(["attempt_id"], ["attempts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["question_id"], ["questions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("attempt_id", "question_id"),
    )
    op.create_index("ix_answers_attempt_id", "answers", ["attempt_id"])
    op.create_index("ix_answers_question_id", "answers", ["question_id"])


def downgrade() -> None:
    # Drop tables in reverse FK-dependency order
    op.drop_table("answers")
    op.drop_table("attempts")
    op.drop_table("options")
    op.drop_table("questions")
    op.drop_table("tests")
    op.drop_table("access_requests")
    op.drop_table("teacher_invite_codes")
    op.drop_table("users")

    # Drop PostgreSQL ENUM types last (tables that reference them must be gone first)
    op.execute("DROP TYPE IF EXISTS test_status")
    op.execute("DROP TYPE IF EXISTS user_role")
