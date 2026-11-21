from datetime import datetime, timezone

import pytest

from observatoire_energie_qc.models import EnergyReading


def test_from_mapping_normalizes_timestamp_and_numbers():
    reading = EnergyReading.from_mapping(
        {
            "timestamp": "2026-11-21T12:00:00Z",
            "region": "Québec",
            "consumption_mwh": "12500",
            "production_mwh": "13100",
        }
    )

    assert reading.timestamp.tzinfo == timezone.utc
    assert reading.consumption_mwh == 12500
    assert reading.production_mwh == 13100


@pytest.mark.parametrize(
    "data",
    [
        {"timestamp": "2026-11-21T12:00:00Z", "region": "", "consumption_mwh": 1, "production_mwh": 1},
        {"timestamp": "2026-11-21T12:00:00Z", "region": "Québec", "consumption_mwh": -1, "production_mwh": 1},
    ],
)
def test_invalid_readings_are_rejected(data):
    with pytest.raises(ValueError):
        EnergyReading.from_mapping(data)
