# RoadLens - Belgian Road Safety dashboard

An offline, presentation-ready dashboard based on the supplied Statbel crash map data for 2017–2024. It follows sections 3–6 of `analysis_notebooks/01_geopandas_belgie.ipynb`: road network, location coverage, crash concentrations and a Brussels street-level example.

The RoadLens logo appears in the sidebar and its icon in the browser tab. The dashboard uses local copies in `dist/assets`, taken from the project’s `logo` folder; no external image service is required.

## Run locally

From the repository root after cloning (Python 3 only; no package installation or original data folder is needed):

```powershell
python -m http.server 8765 --bind 127.0.0.1 --directory dashboard_demo/dist
```

Open `http://127.0.0.1:8765`. A local server is needed because browsers do not reliably load `data.json` from a `file://` page. The committed `dist/data.json` and `dist/roads.json` are enough to view the dashboard; rebuilding is optional.

## Interactions

- Year, region, province, road type, crash type, severity and recorded weather filter the metrics, maps and most charts together. Click a year on a line chart, or a bar in the road type or crash type chart, to filter directly.
- The local ranking switches between **Provinces** and **Municipalities**. Click a province to filter the dashboard and zoom to that area; click it again to clear the province filter. Brussels-Capital appears as a region because it is not a province.
- Switch between **Road network**, **Concentrations** and **Brussels · locations**. The national view shows OSM motorways and main roads; Brussels adds local streets and individual crash points. The map's **Fatal** mode displays only crashes in source class 1.
- Use the municipality picker, **Brussels**, zoom buttons, mouse wheel or drag to navigate. At 7× zoom, the heatmap switches from 5 km to 500 m cells.
- Hover a grid cell or point for its municipality, crash type and severity. Click a visible named road to inspect its OSM name and counts within 2 km of the clicked point nationally, or 500 m when zoomed in. These are proximity counts, **not crashes assigned to a road or entire route**.
- **Download selection** exports filtered records as CSV.
- The **Vehicles** section adds three views from the separate `vehicle_collisions` dataset: involved-vehicle counts, severe-crash share among involved vehicles, and collision-type mix. All dashboard filters, including weather, apply to these charts. The map and its KPIs still use `accident_map`; their totals need not match vehicle counts because a crash may involve multiple vehicles.
- The **Fatal crashes** section shows source-class-1 crash counts, a yearly trend, collision types and fatal-crash share within each recorded weather category. This counts crashes classified “with deaths,” not people killed; class 2 (“fatally injured”) is excluded. Weather categories are grouped from the source codes and remain available as a dashboard filter. Small weather groups are suppressed below 100 selected crashes in the share chart.
- Choose **Fatal crashes** in the Severity filter to apply that class across the dashboard, including the map and vehicle charts. With this filter, the weather chart switches from shares to fatal-crash counts so the comparison remains informative. Severity share charts and the fatal summary percentage use all injury crashes under the other active filters as their denominator.
- The Fatal crashes section also ranks road types, regions and municipalities under the active filters. Road-type and region bars can be clicked to filter; municipality bars zoom the map. The named motorway-route chart covers 2017–2024 and follows all dashboard filters. It matches fatal motorway-class crash coordinates to the nearest named OSM road within 30 m; 494 of 557 source records have such a match. It is a shortlist for investigation, not a verified road assignment or risk per trip. Rebuild it with `analysis_notebooks/.venv/Scripts/python.exe dashboard_demo/build_fatal_routes.py` after updating the source or OSM road cache.

## Rebuild the bundled data

First download the Git LFS files with `git lfs pull` and install the analysis dependencies as described in [`analysis_notebooks/README.md`](../analysis_notebooks/README.md). Then, from the repository root in PowerShell, run:

```powershell
& ./analysis_notebooks/.venv/Scripts/python.exe dashboard_demo/build_data.py
```

On macOS/Linux, use `analysis_notebooks/.venv/bin/python` instead.

This reads `data/gold/accident_map/accident_map.parquet`, geographic exclusions in `analysis_notebooks/tables/geo_uitgesloten.csv`, the GISCO Belgian boundary and the OSM road cache in `analysis_notebooks/reference_data`. It also groups `data/gold/vehicle_collisions/vehicle_collisions.parquet` for the vehicle charts. It writes `dist/data.json`, `dist/roads.json`, `dist/vehicles.json` and `dist/fatal_routes.json`. The data metadata includes source hashes, column order and row counts. To rebuild only the vehicle summary, run `python dashboard_demo/build_vehicle_data.py` with the same environment. To rebuild only named fatal-route matches, run `analysis_notebooks/.venv/Scripts/python.exe dashboard_demo/build_fatal_routes.py` on Windows (or the equivalent venv Python path on macOS/Linux).

## Definitions and limits

- One record is one police-recorded road crash with a death or injury. Property-damage-only crashes are excluded.
- Severe crash classes are source codes 1, 2 and 3. Severe share uses selected injury crashes as its denominator.
- Map cells and crash points include only plausible coordinates. The displayed point coordinates are rounded to 10 m. EPSG:31370 is the coordinate-system assumption documented in the notebook.
- The Brussels detail is the fixed 20 × 20 km window from the notebook, not the administrative region boundary. Local OSM streets are bundled only for this window; other cities show main roads.
- Road geometries come from OSM/Geofabrik, while crash classifications come from Statbel. They are separate sources. There is no validated crash-to-road assignment or traffic exposure denominator, so counts do not measure risk per trip.
- The location coverage chart uses the full map source per year and highlights the selected year. Other charts reflect active filters. Improved geolocation from 2022 limits direct comparisons of map hotspots across earlier years.
- Vehicle severity describes the crash involving that vehicle, not the injury of its occupants or the vehicle's responsibility. These records have no fleet-size or travel-distance denominator, so vehicle counts and severe shares do not estimate the probability that a vehicle type will crash.
- Fatal-crash share by weather is conditional on already-recorded injury crashes. The data have no traffic exposure by weather, so apparent differences do not measure the chance of a fatal crash per trip or establish a weather effect. Missing and combined weather codes are kept as `Unknown` and `Mixed conditions`.

Sources: supplied Statbel data 2017–2024; Belgian boundary © EuroGeographics / Eurostat-GISCO 2024; roads © OpenStreetMap contributors / Geofabrik, 2025-01-01. Source download details and hashes are in `analysis_notebooks/reference_data/sources.json`.
