# Belgian Road Safety dashboard

An offline, presentation-ready dashboard based on the supplied Statbel crash map data for 2017–2024. It follows sections 3–6 of `analysis_notebooks/01_geopandas_belgie.ipynb`: road network, location coverage, crash concentrations and a Brussels street-level example.

## Run locally

From the `group_assignment` directory:

```powershell
python -m http.server 8765 --directory dashboard_demo/dist
```

Open `http://localhost:8765`. A local server is needed because browsers do not reliably load `data.json` from a `file://` page.

## Interactions

- Year, region, province, road type, crash type and severity filter the metrics, maps and most charts together. Click a year on either line chart, or a bar in the road type or crash type chart, to filter directly.
- The local ranking switches between **Provinces** and **Municipalities**. Click a province to filter the dashboard and zoom to that area; click it again to clear the province filter. Brussels-Capital appears as a region because it is not a province.
- Switch between **Road network**, **Concentrations** and **Brussels · locations**. The national view shows OSM motorways and main roads; Brussels adds local streets and individual crash points.
- Use the municipality picker, **Brussels**, zoom buttons, mouse wheel or drag to navigate. At 7× zoom, the heatmap switches from 5 km to 500 m cells.
- Hover a grid cell or point for its municipality, crash type and severity. Click a visible named road to inspect its OSM name and counts within 2 km of the clicked point nationally, or 500 m when zoomed in. These are proximity counts, **not crashes assigned to a road or entire route**.
- **Download selection** exports filtered records as CSV.

## Rebuild the bundled data

```powershell
analysis_notebooks/.venv/Scripts/python.exe dashboard_demo/build_data.py
```

This reads `data/gold/accident_map/accident_map.parquet`, geographic exclusions in `analysis_notebooks/tables/geo_uitgesloten.csv`, the GISCO Belgian boundary and the OSM road cache in `analysis_notebooks/reference_data`. It writes `dist/data.json` and `dist/roads.json`. The data metadata includes the source hash, column order and row count.

## Definitions and limits

- One record is one police-recorded road crash with a death or injury. Property-damage-only crashes are excluded.
- Severe crash classes are source codes 1, 2 and 3. Severe share uses selected injury crashes as its denominator.
- Map cells and crash points include only plausible coordinates. The displayed point coordinates are rounded to 10 m. EPSG:31370 is the coordinate-system assumption documented in the notebook.
- The Brussels detail is the fixed 20 × 20 km window from the notebook, not the administrative region boundary. Local OSM streets are bundled only for this window; other cities show main roads.
- Road geometries come from OSM/Geofabrik, while crash classifications come from Statbel. They are separate sources. There is no validated crash-to-road assignment or traffic exposure denominator, so counts do not measure risk per trip.
- The location coverage chart uses the full map source per year and highlights the selected year. Other charts reflect active filters. Improved geolocation from 2022 limits direct comparisons of map hotspots across earlier years.

Sources: supplied Statbel data 2017–2024; Belgian boundary © EuroGeographics / Eurostat-GISCO 2024; roads © OpenStreetMap contributors / Geofabrik, 2025-01-01. Source download details and hashes are in `analysis_notebooks/reference_data/sources.json`.
