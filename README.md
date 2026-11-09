# RoadLens - Belgian road safety analysis

Reproducible analysis of Belgian injury crashes, with bronze/silver/gold datasets, six analysis notebooks, a preparation pipeline, and an interactive local dashboard.

The interactive dashboard is branded **RoadLens**. Its sidebar logo and browser icon are bundled in `dashboard_demo/dist/assets`, so they appear when someone runs the dashboard from a fresh clone.

## Repository layout

| Folder | Contents |
| --- | --- |
| `data/bronze/raw` | Original supplied source files |
| `data/silver` | Cleaned, full-size analytical datasets |
| `data/gold` | Focused datasets for analysis |
| `pipeline` | Preparation code, validation, catalog and handover notes |
| `analysis_notebooks` | GeoPandas analyses, figures, tables and reference geography |
| `dashboard_demo` | Interactive dashboard and bundled map data |

## Open the dashboard from a fresh clone

You need Git and Python 3. The dashboard's `data.json` and `roads.json` are committed to this repository, so you do **not** need the author's local data folder, Git LFS downloads, or any Python packages to view it.

```powershell
git clone https://github.com/ArthurCallewaert03/belgian-road-safety-analysis.git
cd belgian-road-safety-analysis
python -m http.server 8765 --bind 127.0.0.1 --directory dashboard_demo/dist
```

Open [http://127.0.0.1:8765](http://127.0.0.1:8765). Keep the terminal running while using the dashboard. Use the local server rather than opening `index.html` directly: the browser loads the bundled JSON files over HTTP. If `python` is unavailable on Windows, try `py -3` in its place.

## Work with the source datasets

The bronze, silver and gold files are stored with [Git LFS](https://git-lfs.com/). Install Git LFS and run `git lfs pull` from the cloned repository before running the pipeline, notebooks, or dashboard data builder. This downloads the supplied 2017–2024 source files and derived datasets; no separate copy of the author's `data` directory is required. These files are large (about 1.8 GB in LFS).

For the data pipeline, follow [`pipeline/HANDOVER.md`](pipeline/HANDOVER.md). For the analyses, follow [`analysis_notebooks/README.md`](analysis_notebooks/README.md). Dashboard controls, limitations and the optional rebuild are documented in [`dashboard_demo/README.md`](dashboard_demo/README.md).

The dashboard shows recorded counts and geographic concentrations. It does not estimate risk per trip or attribute each crash to a specific OSM road.
