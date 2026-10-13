"""The caller-request fields shared by form input, conversation facts and persistence."""

import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class HelpRequestDetails(BaseModel):
    model_config = ConfigDict(extra="forbid")

    phone_number: str | None = Field(default=None, max_length=100)
    type: Literal["food", "evacuation"] | None = None
    people_details: str | None = Field(default=None, max_length=1000)
    n_children: int | None = Field(default=None, ge=0)
    n_elders: int | None = Field(default=None, ge=0)
    n_pets: int | None = Field(default=None, ge=0)
    location: str | None = Field(default=None, max_length=1000)
    coordinates: str | None = Field(default=None, max_length=1000)
    location_details: str | None = Field(default=None, max_length=1000)
    water_level: str | None = Field(default=None, max_length=1000)
    situation_details: str | None = Field(default=None, max_length=1000)
    emergency_detail: str | None = Field(default=None, max_length=1000)
    other_details: str | None = Field(default=None, max_length=1000)

    @field_validator("*", mode="before")
    @classmethod
    def blank_is_unknown(cls, value):
        return value.strip() or None if isinstance(value, str) else value

    @field_validator("phone_number")
    @classmethod
    def valid_phone_number(cls, value):
        if value is None:
            return None
        normalized = re.sub(r"[\s().-]", "", value)
        if not re.fullmatch(r"\+?[0-9]{7,15}", normalized):
            raise ValueError("Enter a phone number with 7–15 digits and an optional leading +")
        return normalized

    @field_validator("coordinates")
    @classmethod
    def valid_coordinates(cls, value):
        if value is not None:
            try:
                lat, lon = (float(part.strip()) for part in value.split(","))
            except ValueError:
                raise ValueError("Use latitude, longitude") from None
            if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                raise ValueError("Coordinates are outside latitude/longitude ranges")
        return value


class HelpRequest(HelpRequestDetails):
    phone_number: str = Field(min_length=1, max_length=100)
    type: Literal["food", "evacuation"]
    report_id: str
    channel: Literal["chat", "voice", "form"]


HELP_REQUEST_FIELDS = ("report_id", "channel", *HelpRequestDetails.model_fields)
