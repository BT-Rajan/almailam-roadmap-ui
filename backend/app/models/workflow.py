from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import SoftDeleteMixin, TimestampMixin
from app.models.user import BigPK


class WorkflowTemplate(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "workflow_templates"

    id: Mapped[int] = mapped_column(BigPK, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    stages: Mapped[list["WorkflowStage"]] = relationship(
        back_populates="template",
        order_by="WorkflowStage.sequence_number",
        cascade="all, delete-orphan",
    )


class WorkflowStage(Base):
    __tablename__ = "workflow_stages"

    id: Mapped[int] = mapped_column(BigPK, primary_key=True)
    template_id: Mapped[int] = mapped_column(ForeignKey("workflow_templates.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)

    template: Mapped[WorkflowTemplate] = relationship(back_populates="stages")
