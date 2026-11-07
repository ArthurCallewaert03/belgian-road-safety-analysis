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
story=f'''# Presentatievoorstel — Belgische verkeersveiligheid, 2017–2024

Voorstel voor circa 12–15 minuten. De slides hieronder zijn een inhoudelijk draaiboek; er is geen PowerPointbestand aangemaakt. Gebruik de PNG- of SVG-figuren uit `figures`.

## 1. Vraag en afbakening

**Vraag:** wat leren de registraties over ontwikkeling, plaats, tijd en betrokken weggebruikers?

Vier afzonderlijke datasets: letselongevallen, betrokken personen, voertuigkenmerken en geografische registraties. Tellingen gebruiken de juiste bronmaat. De levering loopt tot 2024. Materiële-schade-ongevallen zitten niet in deze letselstatistiek. Spreek over geregistreerde letselongevallen, niet alle ongevallen op Belgische wegen.

## 2. Nationale ontwikkeling

Figuur: `05_nationale_trends.png`.

In 2024 zijn er **{n(a['accidents_2024'])} geregistreerde letselongevallen**, **{n(a['seriously_injured_2024'])} zwaargewonden** en **{n(a['deaths_2024'])} doden binnen 30 dagen**. Ten opzichte van 2017 verandert het aantal ongevallen met **{a['accident_change_pct']:+.1f}%** en het aantal verkeersdoden met **{a['death_change_pct']:+.1f}%**. Een dalende trend betekent niet dat de resterende letsellast klein is. De dip in 2020 is zichtbaar; deze analyse stelt de oorzaak niet vast.

## 3. Het Belgische wegennet als context

Figuur: `01_belgie_wegennet.png`.

De kaart toont snelwegen en hoofd-/secundaire wegen uit OpenStreetMap. De onderliggende Belgische cache bevat {n(g['road_segments'])} segmenten, inclusief andere weg-/padklassen. Een segment is geen afzonderlijke weg. Dit netwerk is een contextlaag, geen maat voor gereden kilometers.

## 4. Eerst controleren: wat kunnen we op de kaart zien?

Figuur: `02_kaartdekking.png`.

De bruikbare geografische dekking gaat van **{g['coverage_2017']:.1f}% in 2017** naar **{g['coverage_2024']:.1f}% in 2024**. Statbel meldt een verbeterde geolokalisatiemethode vanaf 2022. Over alle jaren zijn er **{n(g['missing_coordinates'])} registraties zonder coördinaten**, **{n(g['impossible_coordinates'])} met onmogelijke coördinaten** en **{n(g['outside_border'])} buiten de gebruikte landsgrensbuffer**. Geen daarvan is stilzwijgend hersteld. Meer kaartpunten is niet automatisch meer ongevallen.

## 5. Ruimtelijke concentraties

Figuur: `03_concentraties_2024.png`.

De kaart gebruikt **{n(g['selected_points'])} bruikbare locaties in 2024**. De tien 5 × 5 km-cellen met de meeste registraties bevatten **{g['top10_cell_share']:.1f}%** van die locaties. Dit is een indicatie van concentratie. Zonder verkeersintensiteiten mag dit niet worden vertaald naar een rangschikking van gevaarlijkste wegen. Het kaartbestand verschilt in 2024 met {g['map_total_difference_2024']:+d} registraties van de algemene ongevalstelling; er is geen individuele koppeling gemaakt.

## 6. Een lokale blik

Figuur: `04_brussel_detail.png`.

Toon hoe punten zich in een stratenpatroon situeren. Dit is een rechthoekig venster rond Brussel, geen gewestvergelijking. Er is geen automatische toewijzing aan wegen en geen uitspraak over schuld of infrastructuurkwaliteit.

## 7. Volume en ernst verschillen per gewest

Figuur: `06_gewesten_volume_ernst.png`. Exacte waarden: `tables/gewesten_2024.csv`.

Het linker paneel telt ongevallen, het rechter paneel geeft het aandeel zwaargewonden en doden binnen de geregistreerde gewonden/doden. Een gewest kan een ander beeld geven op volume dan op ernst. De percentages zijn geen kans op letsel per rit of per inwoner.

## 8. Wanneer gebeuren de registraties?

Figuur: `07_weekdag_uur.png`; optioneel `10_maandpatroon.png`.

In 2024 ligt de hoogste uur-weekdagcel op **{a['peak_weekday']} om {a['peak_hour']} uur**, met gemiddeld **{a['peak_accidents_per_day']:.2f} ongevallen per betreffende kalenderdag**. De heatmap sluit {n(a['invalid_hour_accidents_2024'])} ongevallen met een onbruikbaar uur uit. Correctie voor aantal kalenderdagen is wel uitgevoerd; correctie voor verkeersintensiteit niet.

## 9. Wie draagt de geregistreerde letsellast?

Figuur: `08_weggebruikers.png`. Exacte waarden: `tables/weggebruikers_2024.csv`.

Vergelijk aantallen gewonden/doden met het aandeel ernstig letsel binnen dezelfde groep. In deze groepering heeft **{a['highest_severity_group']}** het hoogste geregistreerde ernstaandeel (**{a['highest_severity_pct']:.1f}%**). Dat kan samenhangen met kwetsbaarheid, omstandigheden en registratieverschillen; deze beschrijvende analyse isoleert die verklaringen niet. Laat de denominatoren in de bijbehorende tabel zien als er vragen komen.

## 10. Voertuigmix en conclusie

Figuur: `09_voertuigmix.png`.

Het SUV-aandeel in de voertuigbron stijgt van **{a['suv_share_2017']:.1f}% naar {a['suv_share_2024']:.1f}%**. Dat beschrijft de betrokken voertuigpopulatie en is geen bewijs dat SUV's vaker botsen per voertuig of per kilometer. {n(a['unknown_year_vehicles'])} voertuigen zonder bronjaar vallen buiten de jaarvergelijking.

**Afsluiting:** de datasets geven bruikbare prioriteiten voor vervolgonderzoek naar locatie, tijd en letsellast. Voor onderbouwde risicorangschikkingen ontbreken blootstellingsmaten, een gevalideerde ongeval-wegkoppeling en een model dat rekening houdt met verschillen tussen groepen. Eerst die informatie toevoegen, dan pas causale of beleidsmatige effectclaims toetsen.

## Bronvermelding en reproduceerbaarheid

Broncijfers: aangeleverde Statbel-data 2017–2024. Wegen: © OpenStreetMap contributors / Geofabrik, 01-01-2025, ODbL. Landsgrens: © EuroGeographics / Eurostat-GISCO 2024. De figuren bevatten deze bronvermeldingen; behoud ze in de presentatie.

Alle berekeningen staan in de twee uitgevoerde notebooks; ruwe bronhashes staan in `../pipeline/source_manifest.json`, geografische referentiehashes in `reference_data/sources.json`, en controle-uitkomsten in `validation.json`.
'''
(BASE/'PRESENTATIEVERHAAL.md').write_text(story,encoding='utf-8')
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

