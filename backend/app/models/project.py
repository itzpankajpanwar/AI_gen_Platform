import uuid
from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, utcnow


def new_id() -> str:
    return uuid.uuid4().hex


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(200))

    model_name: Mapped[str] = mapped_column(String(100))
    width: Mapped[int] = mapped_column(Integer)
    height: Mapped[int] = mapped_column(Integer)
    steps: Mapped[int] = mapped_column(Integer)
    batch_size: Mapped[int] = mapped_column(Integer, default=1)
    image_format: Mapped[str] = mapped_column(String(10), default="png")
    seed: Mapped[int | None] = mapped_column(Integer, nullable=True)

    csv_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    prompt_count: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    @property
    def model(self) -> str:
        """API-facing alias; `model_` is a reserved prefix in pydantic."""
        return self.model_name

    prompts: Mapped[list["Prompt"]] = relationship(  # noqa: F821
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="Prompt.order_index",
    )
    jobs: Mapped[list["Job"]] = relationship(  # noqa: F821
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="Job.created_at",
    )
