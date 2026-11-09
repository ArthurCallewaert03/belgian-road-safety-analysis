from pathlib import Path
import json,hashlib,datetime,importlib.metadata
import pandas as pd
import nbformat
from nbconvert import HTMLExporter
BASE=Path(__file__).resolve().parent
T=BASE/'tables'
a=json.loads((T/'analysis_summary.json').read_text(encoding='utf-8'))
g=json.loads((T/'geo_summary.json').read_text(encoding='utf-8'))
def n(v): return f'{v:,.0f}'.replace(',','.')
summaries={
 '01_geopandas_belgie.ipynb':f"**Uitgevoerde resultaten:** {n(g['selected_points'])} bruikbare kaartpunten in 2024 ({g['coverage_2024']:.1f}% van het kaartbestand). De tien drukste rastercellen bevatten {g['top10_cell_share']:.1f}% van die punten. Over 2017–2024 zijn {n(g['impossible_coordinates'])} onmogelijke coördinaten en {n(g['outside_border'])} punten buiten de 1-km-grensbuffer uitgesloten van de kaarten; de brondata zijn behouden.",
 '02_analyse_presentatie.ipynb':f"**Uitgevoerde resultaten:** {n(a['accidents_2024'])} letselongevallen en {n(a['deaths_2024'])} doden binnen 30 dagen in 2024. Ten opzichte van 2017: respectievelijk {a['accident_change_pct']:+.1f}% en {a['death_change_pct']:+.1f}%. De resultaten zijn beschrijvend; zonder verkeersblootstelling zijn verschillen geen risico per rit."
}
validation=[]
for name,summary in summaries.items():
    path=BASE/name; nb=nbformat.read(path,as_version=4)
    cells=[c for c in nb.cells if c.cell_type=='code']
    assert all(c.execution_count is not None for c in cells)
    assert not any(o.output_type=='error' for c in cells for o in c.outputs)
    images=sum('image/png' in o.get('data',{}) for c in cells for o in c.outputs)
    assert images>=4
    if '## Samenvatting van de uitgevoerde run' not in nb.cells[0].source:
        nb.cells[0].source=nb.cells[0].source.replace('## Context & Methods',f'## Samenvatting van de uitgevoerde run\n{summary}\n\n## Context & Methods')
    nbf_path=path; nbformat.validate(nb); nbformat.write(nb,nbf_path)
    # The executed notebook retains all charts; HTML is optional when a template is installed.
    validation.append(dict(notebook=name,code_cells=len(cells),rendered_figures=images,execution='PASS'))
files=[]
for name in ['road_accidents','road_casualties','vehicle_collisions','accident_map']:
    p=BASE.parent/'data/gold'/name/(name+'.parquet')
    files.append(dict(path=str(p.relative_to(BASE.parent)),sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
packages=['geopandas','shapely','pyproj','pyogrio','pandas','numpy','matplotlib','pyarrow','nbformat','nbclient','nbconvert','ipykernel','requests']
versions={p:importlib.metadata.version(p) for p in packages}
(BASE/'requirements.txt').write_text('\n'.join(f'{k}=={v}' for k,v in versions.items())+'\n',encoding='utf-8')
(BASE/'validation.json').write_text(json.dumps(dict(completed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),notebooks=validation,input_hashes=files,packages=versions,visual_review='See VALIDATIE.md'),indent=2),encoding='utf-8')
print(json.dumps({'analysis':a,'geo':g,'notebooks':validation},indent=2))

