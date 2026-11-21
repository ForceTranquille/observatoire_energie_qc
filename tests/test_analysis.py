from observatoire_energie_qc.analysis import daily_summary
from observatoire_energie_qc.models import EnergyReading


def test_daily_summary_aggregates_region_and_day():
    readings = [
        EnergyReading.from_mapping(
            {"timestamp": "2026-11-21T12:00:00Z", "region": "Québec", "consumption_mwh": 100, "production_mwh": 120}
        ),
        EnergyReading.from_mapping(
            {"timestamp": "2026-11-21T18:00:00Z", "region": "Québec", "consumption_mwh": 50, "production_mwh": 80}
        ),
    ]

    summary = daily_summary(readings)

    assert summary["2026-11-21|Québec"]["consumption_mwh"] == 150
    assert summary["2026-11-21|Québec"]["production_mwh"] == 200
    assert summary["2026-11-21|Québec"]["net_mwh"] == 50
