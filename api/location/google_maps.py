"""Resolve reported Maps links without treating camera coordinates as a pickup pin."""

from __future__ import annotations

import math
import re
from urllib.parse import parse_qs, unquote, urljoin, urlsplit

import httpx
from pydantic import BaseModel, ConfigDict, Field

from api.location.pinpoint import _config


class ReviewLocation(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    address: str | None = Field(default=None, max_length=1000)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    source: str = "unresolved"
    status: str = "unresolved"
    map_url: str | None = None


def maps_url(value: str) -> bool:
    try:
        url = urlsplit(value)
        if url.scheme != "https" or url.username or url.password or url.port not in (None, 443):
            return False
        if url.hostname == "maps.app.goo.gl":
            return True
        if url.hostname == "goo.gl":
            return url.path.startswith("/maps/")
        if url.hostname in {"maps.google.com", "maps.google.co.th"}:
            return True
        return url.hostname in {"google.com", "www.google.com", "google.co.th", "www.google.co.th"} and (url.path == "/maps" or url.path.startswith("/maps/"))
    except ValueError:
        return False


def point(value: str | None) -> tuple[float, float] | None:
    if not value:
        return None
    try:
        latitude, longitude = (float(v.strip()) for v in value.split(","))
        if math.isfinite(latitude) and math.isfinite(longitude) and -90 <= latitude <= 90 and -180 <= longitude <= 180:
            return latitude, longitude
    except (ValueError, TypeError):
        pass
    return None


def _expand(link: str) -> str:
    with httpx.Client(timeout=8, follow_redirects=False) as client:
        for _ in range(5):
            if urlsplit(link).hostname not in {"maps.app.goo.gl", "goo.gl"}:
                return link
            # Read redirect headers only; never scrape a Maps page or follow an arbitrary host.
            with client.stream("GET", link) as response:
                if response.status_code not in (301, 302, 303, 307, 308):
                    return link
                target = urljoin(link, response.headers.get("location", ""))
            if not maps_url(target):
                raise ValueError("Unrecognized Maps redirect")
            link = target
    return link


def _geocode(address: str | None, coordinates: tuple[float, float] | None, place_id: str | None) -> dict | None:
    key = _config("GOOGLE_MAPS_API_KEY")
    if not key or _config("REACHPOINT_MAPS_GEOCODING") != "on":
        return None
    params = {"key": key, "language": "th"}
    if place_id:
        params["place_id"] = place_id
    elif coordinates:
        params["latlng"] = f"{coordinates[0]},{coordinates[1]}"
    elif address:
        params["address"] = address
    else:
        return None
    response = httpx.get("https://maps.googleapis.com/maps/api/geocode/json", params=params, timeout=8, follow_redirects=False)
    response.raise_for_status()
    data = response.json()
    results = data.get("results", [])
    # Reverse lookup returns an ordered address hierarchy (building, road, district, ...).
    # Multiple forward/place matches remain ambiguous; retain the reported pin on reverse lookup.
    reverse = coordinates is not None and not place_id
    if data.get("status") != "OK" or not results or (not reverse and len(results) != 1):
        return None
    result = results[0]
    if result.get("partial_match"):
        return None
    location = result.get("geometry", {}).get("location", {})
    parsed = point(f"{location.get('lat')},{location.get('lng')}")
    if not parsed or not isinstance(result.get("formatted_address"), str) or not 1 <= len(result["formatted_address"]) <= 1000:
        return None
    return {"address": result["formatted_address"], "latitude": parsed[0], "longitude": parsed[1]}


def resolve(caller: dict, *, network: bool = True) -> dict:
    reported = str(caller.get("location") or "").strip()
    coordinates = point(caller.get("coordinates"))
    address = reported if reported and not re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", reported) else None
    link = reported if maps_url(reported) else None
    place_id = None
    source = "caller" if address or coordinates else "unresolved"
    if link:
        source = "google_maps_link"
        try:
            expanded = _expand(link) if network else link
            query = parse_qs(urlsplit(expanded).query)
            if urlsplit(expanded).path.startswith("/maps/dir") or any(k in query for k in ("origin", "destination", "waypoints")):
                return ReviewLocation(source=source, map_url=link).model_dump()
            value = next((query[k][0] for k in ("query", "q") if query.get(k)), None)
            search = re.search(r"/maps/search/([^/]+)", urlsplit(expanded).path)
            search_value = unquote(search[1].replace("+", " ")).strip() if search else None
            if value is None and point(search_value):
                value = search_value
            place_id = (query.get("query_place_id") or query.get("place_id") or [None])[0]
            pins = set(re.findall(r"!3d(-?\d+(?:\.\d+)?)!4d(-?\d+(?:\.\d+)?)", unquote(expanded)))
            if len(pins) > 1:
                return ReviewLocation(source=source, map_url=link).model_dump()
            pin = next(iter(pins), None)
            # @lat,lng and ll= represent the camera/viewport, not a selected destination.
            coordinates = point(f"{pin[0]},{pin[1]}") if pin else (None if place_id else point(value) or coordinates)
            if value and not point(value) and not value.startswith("place_id:"):
                address = value
            elif value and value.startswith("place_id:"):
                place_id = value.removeprefix("place_id:")
            place = re.search(r"/maps/place/([^/]+)", urlsplit(expanded).path)
            if not address and place:
                label = unquote(place[1].replace("+", " ")).strip()
                if not point(label):
                    address = label
        except (httpx.HTTPError, ValueError):
            pass
    if network and (address or coordinates or place_id):
        try:
            match = _geocode(address, coordinates, place_id)
            if match:
                # Reverse geocoding supplies an address; retain the caller's exact pin.
                address = match["address"]
                coordinates = (match["latitude"], match["longitude"]) if place_id else coordinates or (match["latitude"], match["longitude"])
                source = "google_maps_geocoding"
        except (httpx.HTTPError, ValueError, TypeError, KeyError):
            pass  # Never log caller locations, key-bearing URLs, or provider diagnostics.
    return ReviewLocation(address=address, latitude=coordinates[0] if coordinates else None,
                          longitude=coordinates[1] if coordinates else None, source=source,
                          status="resolved" if address and coordinates else "partial" if address or coordinates else "unresolved",
                          map_url=link).model_dump()
