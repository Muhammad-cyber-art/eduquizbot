"""SQLAlchemy ORM models for EduQuiz Bot — PostgreSQL only.

Design decisions:
- All PKs use BIGSERIAL (BigInteger + autoincrement) for future scalability.
- Enums use native_enum=True → stored as PostgreSQL ENUM types (faster, indexed).
- All timestamps use DateTime(timezone=True) → stored as TIMESTAMPTZ in PostgreSQL.
- CASCADE deletes are used where the child record has no meaning without the parent.
- RESTRICT is used on teacher→test to prevent accidental teacher deletion.
- Composite unique constraints are defined at __table_args__ level for clarity.
"""

from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


# ── Python enums ─────────────────────────────────────────────
class UserRole(str, enum.Enum):
    TEACHER = "teacher"
    STUDENT = "student"
    ADMIN = "admin"


class TestStatus(str, enum.Enum):
    DRAFT = "draft"
    OPEN = "open"
    CLOSED = "closed"


class SubscriptionPlan(str, enum.Enum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


# ── Users ─────────────────────────────────────────────────────
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tg_user_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True, nullable=False)
    full_name: Mapped[str | None] = mapped_column(Text)
    role: Mapped[UserRole] = mapped_column(
        # native_enum=True → PostgreSQL stores as pg ENUM type (not VARCHAR)
        Enum(UserRole, name="user_role", native_enum=True, create_type=True, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    lang_code: Mapped[str] = mapped_column(String(5), nullable=False, default="uz")
    max_tests: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    max_students: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ai_queries_limit: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    ai_queries_used: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    tests: Mapped[list[Test]] = relationship(back_populates="teacher")
    attempts: Mapped[list[Attempt]] = relationship(back_populates="student")


# ── Teacher Invite Codes ──────────────────────────────────────
class TeacherInviteCode(Base):
    __tablename__ = "teacher_invite_codes"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    max_tests: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    max_students: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
    ai_queries_limit: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


# ── Access Requests ───────────────────────────────────────────
class AccessRequest(Base):
    """Teacher access request — submitted via bot, reviewed on admin panel."""
    __tablename__ = "access_requests"
    __table_args__ = (
        Index("ix_access_requests_phone_number", "phone_number"),
        Index("ix_access_requests_status", "status"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tg_user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(Text, nullable=False)
    tg_username: Mapped[str | None] = mapped_column(String(64))
    phone_number: Mapped[str | None] = mapped_column(String(32))
    max_tests: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    max_students: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ai_queries_limit: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="pending"
    )  # pending | approved | rejected | used
    # bcrypt-hashed password — set when admin approves; never stored as plaintext
    password: Mapped[str | None] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


# ── Tests ─────────────────────────────────────────────────────
class Test(Base):
    __tablename__ = "tests"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(16), unique=True, index=True, nullable=False)
    teacher_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    difficulty: Mapped[str] = mapped_column(String(16), nullable=False, default="medium")
    subject: Mapped[str | None] = mapped_column(Text)
    status: Mapped[TestStatus] = mapped_column(
        Enum(TestStatus, name="test_status", native_enum=True, create_type=True, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=TestStatus.DRAFT,
    )
    time_limit_minutes: Mapped[int | None] = mapped_column(Integer)
    attempt_limit: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    test_type: Mapped[str] = mapped_column(String(16), nullable=False, default="standard")
    shuffle_questions: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    shuffle_options: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    opened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Relationships
    teacher: Mapped[User] = relationship(back_populates="tests")
    questions: Mapped[list[Question]] = relationship(
        back_populates="test", order_by="Question.position"
    )
    attempts: Mapped[list[Attempt]] = relationship(back_populates="test")


# ── Questions ─────────────────────────────────────────────────
class Question(Base):
    __tablename__ = "questions"
    __table_args__ = (UniqueConstraint("test_id", "position"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    test_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("tests.id", ondelete="CASCADE"), index=True, nullable=False
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    image_file_id: Mapped[str | None] = mapped_column(Text)
    explanation: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    test: Mapped[Test] = relationship(back_populates="questions")
    options: Mapped[list[Option]] = relationship(
        back_populates="question", order_by="Option.label"
    )


# ── Options (A/B/C/D/…) ───────────────────────────────────────
class Option(Base):
    __tablename__ = "options"
    __table_args__ = (
        UniqueConstraint("question_id", "label"),
        CheckConstraint(
            "label IN ('A','B','C','D','E','F','G','H','I','J')",
            name="ck_option_label",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    question_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("questions.id", ondelete="CASCADE"), index=True, nullable=False
    )
    label: Mapped[str] = mapped_column(String(1), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Relationships
    question: Mapped[Question] = relationship(back_populates="options")


# ── Attempts ──────────────────────────────────────────────────
class Attempt(Base):
    __tablename__ = "attempts"
    __table_args__ = (UniqueConstraint("test_id", "student_id", "started_at"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    test_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("tests.id", ondelete="CASCADE"), index=True, nullable=False
    )
    student_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    deadline_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    score: Mapped[int | None] = mapped_column(Integer)
    max_score: Mapped[int | None] = mapped_column(Integer)
    percent: Mapped[float | None] = mapped_column(Numeric(5, 2))
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="in_progress", index=True
    )
    xp_earned: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Relationships
    test: Mapped[Test] = relationship(back_populates="attempts")
    student: Mapped[User] = relationship(back_populates="attempts")
    answers: Mapped[list[Answer]] = relationship(back_populates="attempt")


# ── Answers ───────────────────────────────────────────────────
class Answer(Base):
    __tablename__ = "answers"
    __table_args__ = (
        UniqueConstraint("attempt_id", "question_id"),
        CheckConstraint(
            "selected_label IN ('A','B','C','D','E','F','G','H','I','J')",
            name="ck_answer_label",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    attempt_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("attempts.id", ondelete="CASCADE"), index=True, nullable=False
    )
    question_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("questions.id", ondelete="CASCADE"), index=True, nullable=False
    )
    selected_label: Mapped[str] = mapped_column(String(1), nullable=False)
    selected_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    attempt: Mapped[Attempt] = relationship(back_populates="answers")
