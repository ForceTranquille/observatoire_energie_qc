from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Iterable

from .models import EnergyReading


def daily_summary(readings: Iterable[EnergyReading]) -> dict[str, dict[str, float | str]]:
    """Aggregate readings by UTC day and region."""
    totals: dict[tuple[str, str], dict[str, float]] = defaultdict(
        lambda: {"consumption_mwh": 0.0, "production_mwh": 0.0}
    )
    for reading in readings:
        day = reading.timestamp.date().isoformat()
        key = (day, reading.region)
        totals[key]["consumption_mwh"] += reading.consumption_mwh
        totals[key]["production_mwh"] += reading.production_mwh

    result: dict[str, dict[str, float | str]] = {}
    for (day, region), values in sorted(totals.items()):
        consumption = values["consumption_mwh"]
        production = values["production_mwh"]
        result[f"{day}|{region}"] = {
            "day": day,
            "region": region,
            "consumption_mwh": consumption,
            "production_mwh": production,
            "net_mwh": production - consumption,
        }
    return result
