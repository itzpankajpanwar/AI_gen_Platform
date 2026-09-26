from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Prompt(Base):
    __tablename__ = "prompts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    external_id: Mapped[str] = mapped_column(String(64))
    order_index: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text)

    # Timeline position of this prompt's image in the rendered video.
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

    project: Mapped["Project"] = relationship(back_populates="prompts")  # noqa: F821
