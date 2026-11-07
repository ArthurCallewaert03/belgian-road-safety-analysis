# Belgian road safety analysis

Reproducible analysis of Belgian injury crashes, with bronze/silver/gold datasets, six analysis notebooks, a preparation pipeline, and an interactive local dashboard.

## Repository layout

| Folder | Contents |
| --- | --- |
| `data/bronze/raw` | Original supplied source files |
| `data/silver` | Cleaned, full-size analytical datasets |
| `data/gold` | Focused datasets for analysis |
| `pipeline` | Preparation code, validation, catalog and handover notes |
| `analysis_notebooks` | GeoPandas analyses, figures, tables and reference geography |
| `dashboard_demo` | Interactive dashboard and bundled map data |

## Set up

Install [Git LFS](https://git-lfs.com/) before cloning, then run `git lfs pull` if the large files were not downloaded automatically. Follow the detailed instructions in [`pipeline/HANDOVER.md`](pipeline/HANDOVER.md), [`analysis_notebooks/README.md`](analysis_notebooks/README.md), and [`dashboard_demo/README.md`](dashboard_demo/README.md).

From the repository root, run the dashboard with:

```powershell
python -m http.server 8765 --directory dashboard_demo/dist
```

Open `http://localhost:8765`.

The dashboard shows recorded counts and geographic concentrations. It does not estimate risk per trip or attribute each crash to a specific OSM road.
