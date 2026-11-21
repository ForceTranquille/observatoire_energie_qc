from pathlib import Path

from observatoire_energie_qc.collector import collect_records, parse_records


def test_parse_json_object_data():
    assert parse_records('{"data":[{"region":"Québec"}]}') == [{"region": "Québec"}]


def test_collect_csv(tmp_path: Path):
    path = tmp_path / "readings.csv"
    path.write_text(
        "timestamp,region,consumption_mwh,production_mwh\n"
        "2026-11-21T12:00:00Z,Québec,12500,13100\n",
        encoding="utf-8",
    )

    readings = collect_records(path)

    assert len(readings) == 1
    assert readings[0].region == "Québec"
    assert readings[0].production_mwh == 13100
