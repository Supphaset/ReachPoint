"""Server-side Pinpoint lookup tools; credentials never enter model context."""

import math
import os

import httpx
from langchain_core.tools import tool

BASE_URL = "https://pin-point.co/g/search"


async def _request(endpoint: str, data: dict) -> dict:
    key = os.environ.get("PINPOINT_API_KEY")
    if not key:
        return {"status": "error", "reason": "not_configured"}
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                f"{BASE_URL}/{endpoint}",
                data={**data, "key": key},
                headers={"Referer": os.environ.get("PINPOINT_REFERER") or "https://pin-point.co"},
            )
        if response.status_code in (401, 403):
            return {"status": "error", "reason": "authentication"}
        if response.status_code == 429:
            return {"status": "error", "reason": "rate_limit"}
        if response.is_error:
            return {"status": "error", "reason": "service"}
        payload = response.json()
        if not isinstance(payload, dict) or payload.get("success") is False:
            return {"status": "error", "reason": "service"}
        return {"status": "ok", "data": payload.get("data")}
    except httpx.TimeoutException:
        return {"status": "error", "reason": "timeout"}
    except (httpx.HTTPError, ValueError):
        # Do not propagate provider bodies or request details containing the key.
        return {"status": "error", "reason": "service"}


@tool
async def search_locations(query: str) -> dict:
    """Search a Thai address or landmark with Pinpoint; return up to 3 unconfirmed matches.

    Pass only address/landmark text, never names, medical details or the full conversation.
    Results are candidates, not confirmed victim coordinates.
    """
    query = query.strip()
    if not 3 <= len(query) <= 256:
        return {"status": "error", "reason": "query_length"}
    result = await _request("autocomplete", {"keyword": query, "maxResult": "3"})
    if result["status"] != "ok":
        return result
    data = result.get("data")
    if not isinstance(data, list):
        return {"status": "error", "reason": "invalid_response"}
    candidates = []
    seen = set()
    for item in data:
        if not isinstance(item, dict):
            continue
        identifier, label = item.get("LocationID"), item.get("FormattedAddress")
        if isinstance(identifier, str) and identifier and isinstance(label, str) and label and identifier not in seen:
            candidates.append({"location_id": identifier, "label": label})
            seen.add(identifier)
    return {"status": "candidates" if candidates else "not_found", "candidates": candidates[:3]}


@tool
async def get_location_details(location_id: str) -> dict:
    """Get coordinates for a Pinpoint candidate explicitly selected by the user.

    The caller must validate this ID against the current search results first.
    This tool does not confirm a rescue or send anything to responders.
    """
    result = await _request("details", {"locationid": location_id})
    if result["status"] != "ok":
        return result
    data = result.get("data")
    if not isinstance(data, dict) or data.get("LocationID") != location_id:
        return {"status": "error", "reason": "invalid_response"}
    try:
        latitude, longitude = [float(value.strip()) for value in data["LAT_LON"].split(",")]
        if not (math.isfinite(latitude) and math.isfinite(longitude) and -90 <= latitude <= 90 and -180 <= longitude <= 180):
            raise ValueError("Invalid coordinates")
    except (KeyError, TypeError, AttributeError, ValueError):
        return {"status": "error", "reason": "invalid_coordinates"}
    label = data.get("FormattedAddress")
    if not isinstance(label, str) or not label:
        return {"status": "error", "reason": "invalid_response"}
    return {"status": "resolved", "location_id": location_id, "label": label,
            "latitude": latitude, "longitude": longitude}
