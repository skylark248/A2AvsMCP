"""Travel fixture mock. SINGLE FAULT CHOKEPOINT per D-25.

Backs the book_travel task's TARGETS: search_flights, search_hotels,
book_itinerary. Faults route through race.failure.inject_fault().
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..failure import inject_fault
from ...trace import TraceRecorder
from . import get_active_fault


FIXTURES_PATH = Path(__file__).resolve().parents[4] / "data" / "race" / "fixtures" / "travel" / "inventory.json"


def _load() -> dict[str, Any]:
    return json.loads(FIXTURES_PATH.read_text())


def search_flights(origin: str, destination: str, *, recorder: TraceRecorder, run_id: str) -> list[dict[str, Any]]:
    fixtures = _load()
    response = [f for f in fixtures["flights"] if f["origin"] == origin and f["destination"] == destination]
    target = "travel_api.search_flights"
    fault = get_active_fault(target)
    if fault is not None:
        return inject_fault(
            recorder=recorder,
            fault_id=fault.fault_id,
            kind=fault.kind,
            target=target,
            original_response=response,
        )
    return response


def search_hotels(city: str, *, recorder: TraceRecorder, run_id: str) -> list[dict[str, Any]]:
    fixtures = _load()
    response = [h for h in fixtures["hotels"] if h["city"] == city]
    target = "travel_api.search_hotels"
    fault = get_active_fault(target)
    if fault is not None:
        return inject_fault(
            recorder=recorder,
            fault_id=fault.fault_id,
            kind=fault.kind,
            target=target,
            original_response=response,
        )
    return response


def book_itinerary(flight_ids: list[str], hotel_id: str, nights: int, *, recorder: TraceRecorder, run_id: str) -> dict[str, Any]:
    """Confirm a booking. Cost = sum(flight prices) + hotel.nightly_usd * nights."""
    fixtures = _load()
    flights = [f for f in fixtures["flights"] if f["id"] in flight_ids]
    hotel = next((h for h in fixtures["hotels"] if h["id"] == hotel_id), None)
    if hotel is None:
        raise KeyError(f"unknown hotel_id: {hotel_id}")
    if len(flights) != len(flight_ids):
        raise KeyError("one or more flight ids unknown")
    total_cost = sum(f["price_usd"] for f in flights) + hotel["nightly_usd"] * nights
    response = {
        "confirmation_id": f"BK-{run_id[:8]}",
        "flights": flights,
        "hotel": hotel,
        "nights": nights,
        "total_cost_usd": total_cost,
    }
    target = "travel_api.book_itinerary"
    fault = get_active_fault(target)
    if fault is not None:
        return inject_fault(
            recorder=recorder,
            fault_id=fault.fault_id,
            kind=fault.kind,
            target=target,
            original_response=response,
        )
    return response
