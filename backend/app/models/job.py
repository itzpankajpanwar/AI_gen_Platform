from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, utcnow


class JobStatus:
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"
    EXPIRED = "expired"

    ACTIVE = (QUEUED, RUNNING)
    TERMINAL = (COMPLETED, CANCELLED, FAILED, EXPIRED)


class ItemStatus:
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    project_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )

    status: Mapped[str] = mapped_column(String(20), default=JobStatus.QUEUED, index=True)
    total: Mapped[int] = mapped_column(Integer, default=0)
    successful: Mapped[int] = mapped_column(Integer, default=0)
    failed: Mapped[int] = mapped_column(Integer, default=0)

    current_index: Mapped[int] = mapped_column(Integer, default=0)
    current_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    cancel_requested: Mapped[bool] = mapped_column(Boolean, default=False)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    output_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    output_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    output_frame_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    output_duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    output_created_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    cleaned_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    project: Mapped["Project"] = relationship(back_populates="jobs")  # noqa: F821
    items: Mapped[list["JobItem"]] = relationship(
        back_populates="job",
        cascade="all, delete-orphan",
        order_by="JobItem.order_index",
    )


class JobItem(Base):
    __tablename__ = "job_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("jobs.id", ondelete="CASCADE"), index=True
    )
    prompt_id: Mapped[int] = mapped_column(Integer, ForeignKey("prompts.id", ondelete="CASCADE"))

    order_index: Mapped[int] = mapped_column(Integer)
    external_id: Mapped[str] = mapped_column(String(64))
    prompt_text: Mapped[str] = mapped_column(Text)
    start_seconds: Mapped[float] = mapped_column(Float, default=0.0)
    end_seconds: Mapped[float] = mapped_column(Float, default=0.0)

    transition: Mapped[str | None] = mapped_column(String(32), nullable=True)
    transition_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    ken_burns: Mapped[str | None] = mapped_column(String(32), nullable=True)
    ken_burns_scale: Mapped[float | None] = mapped_column(Float, nullable=True)
    grade: Mapped[str | None] = mapped_column(String(32), nullable=True)
    grain: Mapped[int | None] = mapped_column(Integer, nullable=True)
    music: Mapped[str | None] = mapped_column(String(255), nullable=True)
    text_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    text_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    narration: Mapped[str | None] = mapped_column(Text, nullable=True)
    voice: Mapped[str | None] = mapped_column(String(64), nullable=True)
    animation: Mapped[str | None] = mapped_column(String(32), nullable=True)
    animation_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    animation_params: Mapped[str | None] = mapped_column(Text, nullable=True)
    needs_image: Mapped[bool] = mapped_column(Boolean, default=True, nullable=True)
    audio_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    audio_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)

    status: Mapped[str] = mapped_column(String(20), default=ItemStatus.PENDING, index=True)
    filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    file_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    seed: Mapped[int | None] = mapped_column(Integer, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    job: Mapped["Job"] = relationship(back_populates="items")
