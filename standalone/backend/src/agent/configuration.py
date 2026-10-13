"""Model settings for the conversational assistant."""

import os

from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel, Field


class Configuration(BaseModel):
    """Configure the Gemini model used for chat."""

    model: str = Field(default="gemini-3.8-flash", description="Gemini chat model")

    @classmethod
    def from_runnable_config(cls, config: RunnableConfig | None = None) -> "Configuration":
        """Read the model from the environment or graph configuration."""
        configurable = (config or {}).get("configurable", {})
        return cls(model=os.environ.get("GEMINI_MODEL") or configurable.get("model") or cls.model_fields["model"].default)
