from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True, slots=True)
class EnergyReading:
    timestamp: datetime
    region: str
    consumption_mwh: float
    production_mwh: float
    source: str = "unknown"

    def __post_init__(self) -> None:
        if not self.region.strip():
            raise ValueError("region must not be empty")
        if self.consumption_mwh < 0:
            raise ValueError("consumption_mwh must not be negative")
        if self.production_mwh < 0:
            raise ValueError("production_mwh must not be negative")
        if self.timestamp.tzinfo is None:
            object.__setattr__(
                self, "timestamp", self.timestamp.replace(tzinfo=timezone.utc)
            )

    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> "EnergyReading":
        timestamp = data.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        if not isinstance(timestamp, datetime):
            raise ValueError("timestamp must be an ISO-8601 string or datetime")

        try:
            return cls(
                timestamp=timestamp,
                region=str(data["region"]),
                consumption_mwh=float(data["consumption_mwh"]),
                production_mwh=float(data["production_mwh"]),
                source=str(data.get("source", "unknown")),
            )
        except KeyError as exc:
            raise ValueError(f"missing required field: {exc.args[0]}") from exc

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["timestamp"] = self.timestamp.isoformat()
        return value
