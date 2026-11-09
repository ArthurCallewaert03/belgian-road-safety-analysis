"""Build compact vehicle summaries for the dashboard from the gold dataset."""
from pathlib import Path
import hashlib
import json

import pandas as pd
from weather_categories import weather_category

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/gold/vehicle_collisions/vehicle_collisions.parquet"
OUTPUT = ROOT / "dashboard_demo/dist/vehicles.json"

COLUMNS = {
    "year": "analysis_year",
    "region": "TX_REGION_COLLISON_NL",
    "province": "TX_PROV_COLLISION_NL",
    "road": "TX_ROAD_TYPE_NL",
    "collision": "TX_COLLISON_TYPE_NL",
    "severity": "TX_ACCIDENT_CLASS_NL",
    "weather": "CD_WEATHER",
    "vehicle": "TX_VEHICLE_SEGMENT_B_NL",
}


def build() -> None:
    frame = pd.read_parquet(SOURCE, columns=list(COLUMNS.values())).rename(
        columns={value: key for key, value in COLUMNS.items()}
    )
    frame["province"] = frame["province"].replace("Brussel-Hoofdstad", "Brussels-Capital Region")
    frame["road"] = frame["road"].str.capitalize()
    frame["weather"] = frame["weather"].map(weather_category)
    for column in COLUMNS:
        if column != "year":
            frame[column] = frame[column].fillna("Onbekend").astype(str)
    frame["year"] = frame["year"].fillna(0).astype(int)

    dimensions = list(COLUMNS)
    categories = {column: sorted(frame[column].unique().tolist()) for column in dimensions if column != "year"}
    grouped = frame.groupby(dimensions, observed=True, dropna=False).size().reset_index(name="count")
    for column, values in categories.items():
        grouped[column] = pd.Categorical(grouped[column], categories=values).codes
    rows = grouped[dimensions + ["count"]].astype(int).values.tolist()
    payload = {
        "meta": {
            "source": "data/gold/vehicle_collisions/vehicle_collisions.parquet",
            "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
            "source_rows": len(frame),
            "columns": dimensions + ["count"],
            "categories": categories,
            "grain": "vehicles involved in police-recorded injury crashes; grouped by dashboard filters",
            "missing_year_code": 0,
        },
        "rows": rows,
    }
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    assert sum(row[-1] for row in rows) == len(frame)
    print(f"Vehicle summary: {len(frame):,} source records, {len(rows):,} groups, {OUTPUT.stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    build()
