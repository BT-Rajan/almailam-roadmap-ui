from sqlalchemy import JSON, Boolean, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import TimestampMixin
from app.models.user import BigPK

AI_PROVIDER_IDS = ("claude", "deepseek")


class AIConfiguration(Base, TimestampMixin):
    __tablename__ = "ai_configuration"

    # Single-row settings table, same pattern as company_settings.
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    default_provider: Mapped[str] = mapped_column(String(20), nullable=False, default="claude")
    provider_priority: Mapped[list] = mapped_column(JSON, nullable=False, default=lambda: ["claude", "deepseek"])
    timeout_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    max_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=2000)
    temperature: Mapped[float] = mapped_column(Float, nullable=False, default=0.3)
    cache_duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=15)
    retry_limit: Mapped[int] = mapped_column(Integer, nullable=False, default=2)


class AIProviderConfig(Base):
    __tablename__ = "ai_provider_configs"

    id: Mapped[int] = mapped_column(BigPK, primary_key=True)
    provider_id: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    label: Mapped[str] = mapped_column(String(80), nullable=False)
    model: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    # Deliberately NOT storing the raw API key -- only whether one has been
    # provided and its last 4 characters, for display purposes. There is no
    # secrets-manager integration in this environment; if real provider
    # credentials need to be stored, they belong in an encrypted secret
    # store, not this settings table.
    has_api_key: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    api_key_hint: Mapped[str] = mapped_column(String(4), nullable=False, default="")


class PromptTemplate(Base, TimestampMixin):
    __tablename__ = "ai_prompt_templates"

    id: Mapped[int] = mapped_column(BigPK, primary_key=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str] = mapped_column(String(300), nullable=False, default="")
    module: Mapped[str] = mapped_column(String(50), nullable=False)
    template: Mapped[str] = mapped_column(Text, nullable=False, default="")
