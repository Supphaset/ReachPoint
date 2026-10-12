"""Intake-to-map handoff. No coordinates, identity merging or authoritative review fields."""
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class WaterInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    submissionId: str = Field(min_length=1, max_length=120)
    quote: str = Field(min_length=2, max_length=200)
    reportId: str = Field(min_length=1, max_length=120)
    segmentId: str = Field(min_length=1, max_length=80)
    siteId: str = Field(min_length=1, max_length=80)  # reported observation site, not household identity
    evidenceRef: str | None = Field(default=None, min_length=1, max_length=120)
    observedAt: datetime | None = None
    reference: Literal["street_ground", "indoor_floor", "upper_floor", "unknown"] = "unknown"
    source: Literal["text", "simulated_call", "phone_transcript", "field"] = "text"
    band: Literal["knee", "waist", "chest", "over_head", "second_floor"] | None = None
    depthM: float | None = Field(default=None, ge=0, le=15, allow_inf_nan=False)
    uncertaintyM: float = Field(default=0.15, ge=0.05, le=5, allow_inf_nan=False)
    trend: Literal["rising", "steady", "falling", "unknown"] = "unknown"

    @model_validator(mode="after")
    def observation(self):
        if self.band is None and self.depthM is None:
            raise ValueError("A water observation needs a band or a measurement")
        if self.observedAt is not None and self.observedAt.tzinfo is None:
            raise ValueError("Observation time needs a timezone")
        return self


class ReplayStep(BaseModel):
    model_config = ConfigDict(extra="forbid")
    submissionId: str = Field(min_length=1, max_length=120)
    expectedCursor: int = Field(ge=0)
    expectedRevision: int = Field(ge=0)
    count: int = Field(default=20, ge=1, le=200)


class ReplayReset(BaseModel):
    model_config = ConfigDict(extra="forbid")
    submissionId: str = Field(min_length=1, max_length=120)
    expectedCursor: int = Field(ge=0)
    expectedRevision: int = Field(ge=0)
