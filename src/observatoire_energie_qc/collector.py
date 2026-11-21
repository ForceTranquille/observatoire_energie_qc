from __future__ import annotations

import csv
import json
from io import StringIO
from pathlib import Path
from typing import Iterable
from urllib.request import Request, urlopen

from .models import EnergyReading


def parse_records(payload: str, source: str = "unknown") -> list[dict]:
    """Parse a JSON array, JSON Lines payload or CSV document."""
    payload = payload.strip()
    if not payload:
        return []

    if payload.startswith("["):
        parsed = json.loads(payload)
    elif payload.startswith("{"):
        lines = payload.splitlines()
        if len(lines) > 1 and all(line.strip().startswith("{") for line in lines):
            parsed = [json.loads(line) for line in lines]
        else:
            parsed = json.loads(payload)
        if isinstance(parsed, dict):
            if "data" in parsed and isinstance(parsed["data"], list):
                parsed = parsed["data"]
            elif "results" in parsed and isinstance(parsed["results"], list):
                parsed = parsed["results"]
            else:
                parsed = [parsed]
    else:
        return list(csv.DictReader(StringIO(payload)))

    if not isinstance(parsed, list):
        raise ValueError("JSON payload must contain an object or array")
    return parsed


def collect_records(
    source: str | Path,
    *,
    timeout: float = 30,
) -> list[EnergyReading]:
    """Collect and normalize records from a URL or local file."""
    source_name = str(source)
    if isinstance(source, Path) or source_name.startswith("file://"):
        path = source if isinstance(source, Path) else Path(source_name.removeprefix("file://"))
        payload = path.read_text(encoding="utf-8")
    elif source_name.startswith(("http://", "https://")):
        request = Request(source_name, headers={"Accept": "application/json,text/csv"})
        with urlopen(request, timeout=timeout) as response:
            payload = response.read().decode("utf-8")
    else:
        payload = Path(source_name).read_text(encoding="utf-8")

    records: Iterable[dict] = parse_records(payload, source_name)
    readings: list[EnergyReading] = []
    for record in records:
        normalized = dict(record)
        normalized.setdefault("source", source_name)
        readings.append(EnergyReading.from_mapping(normalized))
    return readings
