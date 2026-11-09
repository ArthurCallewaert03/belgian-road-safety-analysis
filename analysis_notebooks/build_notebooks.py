from pathlib import Path
import nbformat as nbf
import textwrap

BASE=Path(__file__).resolve().parent
def md(s): return nbf.v4.new_markdown_cell(textwrap.dedent(s).strip())
def code(s): return nbf.v4.new_code_cell(textwrap.dedent(s).strip())
COMMON='''
from pathlib import Path
import json, hashlib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from IPython.display import display, Markdown

BASE = Path.cwd()
if not (BASE / 'reference_data').exists():
    BASE = BASE / 'analysis_notebooks'
assert (BASE / 'reference_data').exists(), 'Start Jupyter in group_assignment or analysis_notebooks.'
ROOT = BASE.parent
GOLD = ROOT / 'data' / 'gold'
FIG = BASE / 'figures'; FIG.mkdir(exist_ok=True)
TABLES = BASE / 'tables'; TABLES.mkdir(exist_ok=True)
YEAR = 2024
BLUE, ORANGE, GREY = '#175A78', '#D76B32', '#657581'
plt.rcParams.update({'figure.figsize':(12,7),'figure.dpi':110,'savefig.dpi':200,
 'font.family':'DejaVu Sans','font.size':11,'axes.titlesize':17,'axes.labelsize':11,
 'axes.spines.top':False,'axes.spines.right':False,'axes.edgecolor':'#BBC4CA',
 'axes.titleweight':'bold','axes.labelcolor':'#243440','text.color':'#243440',
 'xtick.color':'#465662','ytick.color':'#465662','figure.facecolor':'white'})
def number(v): return f'{v:,.0f}'.replace(',', '.')
def export(fig, name, source):
    fig.text(0.015, 0.015, source, fontsize=8, color=GREY)
    fig.savefig(FIG / f'{name}.png', bbox_inches='tight', facecolor='white')
    fig.savefig(FIG / f'{name}.svg', bbox_inches='tight', facecolor='white')
    plt.show()
    plt.close(fig)
def load(name): return pd.read_parquet(GOLD/name/f'{name}.parquet')
'''

geo=[md('''
# België: wegen en ongevalslocaties met GeoPandas
## tl;dr
Dit notebook onderzoekt het wegennet, de ruimtelijke spreiding van geregistreerde letselongevallen en de kwaliteit van de coördinaten. De berekende kernpunten staan bij de resultaten en in `tables/`.

## Context & Methods
We tonen **2024** in detail en gebruiken 2017–2024 om de dekking te beoordelen. Kaartpunten zijn registraties uit `accident_map`, geen koppeling met de andere facttabellen.

### Key Assumptions
- Broncoördinaten worden geïnterpreteerd als **Belgian Lambert 72 (EPSG:31370)**. Dit wordt ruimtelijk gecontroleerd tegenover België; de lokale bron bevatte geen CRS-declaratie. De verificatie is een plausibiliteitstoets, geen bewijs van landmeetkundige precisie.
- Landgrens: Eurostat/GISCO 2024, schaal 1:1 miljoen. Wegen: © OpenStreetMap-bijdragers via Geofabrik, snapshot **1 januari 2025**, ODbL. De wegen zijn een contextlaag en geen verkeersvolume-noemer.
- We gebruiken de nationale grens met een **1 km buffer** voor de plausibiliteitscontrole vanwege grensvereenvoudiging. Punten buiten de buffer en onmogelijke coördinaten blijven in de brondataset, maar worden niet geplot.
- Concentraties tonen aantallen; zonder gereden kilometers of verkeersintensiteit zijn dit **geen risicoscores** of bewezen gevaarlijke wegen.
- De [Statbel-bronpagina](https://statbel.fgov.be/nl/open-data/geolocalisatie-van-de-verkeersongevallen-2017-2024) meldt een verbetering van geolokalisatie vanaf 2022. Kaarttrends mogen niet zonder dekkingscontrole worden geïnterpreteerd.
'''),code(COMMON),md('## Data\n### 1. Lokale bronnen en geometrie laden'),code('''
import geopandas as gpd
from shapely.geometry import box
from matplotlib.lines import Line2D
from matplotlib.colors import LogNorm
REF = BASE/'reference_data'
country = gpd.read_file(REF/'belgium_2024.geojson').to_crs(31370)
assert country.geometry.is_valid.all()
border = country.geometry.union_all()
road_cache = REF/'roads_belgium.parquet'
if road_cache.exists():
    roads = gpd.read_parquet(road_cache)
else:
    roads = gpd.read_file(REF/'roads/gis_osm_roads_free_1.shp',
                          columns=['osm_id','fclass','name','ref','geometry']).to_crs(31370)
    # Spatial index restricts the candidates; only border-crossing segments need clipping.
    import shapely
    roads = roads.iloc[roads.sindex.query(border,predicate='intersects')].copy()
    shapely.prepare(border)
    crossing = ~shapely.contains(border,roads.geometry.array)
    roads.loc[crossing,'geometry'] = roads.loc[crossing].geometry.intersection(border)
    roads = roads[~roads.geometry.is_empty].copy()
    roads.to_parquet(road_cache,index=False)
assert roads.crs == country.crs
raw = load('accident_map')
display(pd.DataFrame({'bron':['Kaartregistraties','OSM-wegsegmenten'],
                      'rijen':[len(raw),len(roads)]}))
'''),md('### 2. Coördinaten valideren en uitgesloten rijen bewaren'),code('''
has_xy = raw[['MS_X_COORD','MS_Y_COORD']].notna().all(axis=1)
# Ruime Lambert-72 box rond België, vóór het aanmaken van geometrieën.
plausible = has_xy & raw.MS_X_COORD.between(0,300000) & raw.MS_Y_COORD.between(0,300000)
points = gpd.GeoDataFrame(raw.loc[plausible].copy(),
    geometry=gpd.points_from_xy(raw.loc[plausible,'MS_X_COORD'],raw.loc[plausible,'MS_Y_COORD']),crs=31370)
inside = points.geometry.intersects(border.buffer(1000))
raw['geo_status'] = 'ontbrekende_coordinaten'
raw.loc[has_xy & ~plausible,'geo_status'] = 'onmogelijke_coordinaten'
raw.loc[points.index,'geo_status'] = np.where(inside,'bruikbaar','buiten_belgie_buffer')
points = points.loc[inside].copy()
assert points._record_id.is_unique
assert len(points) == (raw.geo_status=='bruikbaar').sum()
exceptions = raw.loc[raw.geo_status!='bruikbaar',
    ['_record_id','_source_row','analysis_year','CD_NIS','MS_X_COORD','MS_Y_COORD','geo_status']]
exceptions.to_csv(TABLES/'geo_uitgesloten.csv',index=False)
coverage = pd.crosstab(raw.analysis_year,raw.geo_status).reindex(
    columns=['bruikbaar','ontbrekende_coordinaten','onmogelijke_coordinaten','buiten_belgie_buffer'],fill_value=0)
coverage['totaal_kaart'] = coverage.sum(axis=1)
coverage['dekking_pct'] = 100*coverage.bruikbaar/coverage.totaal_kaart
accidents = load('road_accidents')
coverage['totaal_ongevallen'] = accidents.groupby('analysis_year').MS_ACCT.sum()
coverage['verschil_kaart_totaal'] = coverage.totaal_kaart - coverage.totaal_ongevallen
coverage.to_csv(TABLES/'kaartdekking_per_jaar.csv')
display(coverage.round(2))
display(Markdown(f"**Controle:** {number(len(points))} punten bruikbaar; {number((~has_xy).sum())} zonder coördinaten; "
 f"{number((has_xy & ~plausible).sum())} met onmogelijke waarden; {number((~inside).sum())} buiten de grensbuffer."))
# Maak de CRS-aanname inspecteerbaar met een kleine, herkenbare steekproef.
display(points[['TX_MUNTY_COLLISION_NL','geometry']].head(5).to_crs(4326))
'''),md('## Results\n### 3. Belgisch wegennet\nDe nationale kaart toont snelwegen en hoofd-/secundaire wegen. Lokale straten staan in de cache en in de detailkaart. Zo blijft het landelijk patroon leesbaar.'),code('''
major_classes = ['motorway','motorway_link','trunk','trunk_link','primary','primary_link','secondary','secondary_link']
major = roads[roads.fclass.isin(major_classes)]
motorways = major[major.fclass.isin(['motorway','motorway_link'])]
other = major[~major.fclass.isin(['motorway','motorway_link'])]
def base_map(ax):
    country.plot(ax=ax,color='#F4F6F7',edgecolor='#9AA8B2',linewidth=.7)
    ax.set_aspect('equal'); ax.set_axis_off()
    xmin,ymin,xmax,ymax=country.total_bounds
    ax.set_xlim(xmin-8000,xmax+8000); ax.set_ylim(ymin-8000,ymax+8000)
def scale_bar(ax):
    xmin,ymin,xmax,ymax=country.total_bounds
    ax.plot([xmin+15000,xmin+65000],[ymin+12000,ymin+12000],color='#243440',lw=2)
    ax.text(xmin+40000,ymin+16000,'50 km',ha='center',fontsize=9)
    ax.annotate('N',xy=(.93,.91),xytext=(.93,.80),xycoords='axes fraction',ha='center',arrowprops={'arrowstyle':'->','color':'#243440'})
fig,ax=plt.subplots(figsize=(12,9))
base_map(ax)
other.plot(ax=ax,color='#8FA4B1',linewidth=.45)
motorways.plot(ax=ax,color=BLUE,linewidth=.9)
scale_bar(ax)
ax.set_title('België: snelwegen en belangrijkste verbindingswegen',loc='left',pad=16)
ax.legend(handles=[Line2D([0],[0],color=BLUE,lw=2,label='Snelwegen'),
 Line2D([0],[0],color='#8FA4B1',lw=2,label='Hoofd- en secundaire wegen')],loc='lower left',frameon=False)
export(fig,'01_belgie_wegennet','Wegen: © OpenStreetMap contributors / Geofabrik, 01-01-2025. Grens: © EuroGeographics / Eurostat-GISCO 2024.')
'''),md('### 4. Geografische dekking door de jaren\nDe noemer is alle registraties in het kaartbestand van dat jaar. Het verschil tegenover MS_ACCT staat in de tabel; de twee bronnen worden niet geforceerd gelijk gemaakt.'),code('''
fig,ax=plt.subplots(figsize=(12,6))
ax.plot(coverage.index,coverage.dekking_pct,color=BLUE,marker='o',lw=2.5)
ax.set(ylim=(0,100),ylabel='Bruikbare kaartpunten / alle kaartregistraties (%)',xlabel='Jaar')
ax.set_xticks(coverage.index)
ax.axvline(2021.5,color=GREY,ls='--',lw=1)
ax.text(2021.65,38,'Statbel: verbeterde\\ngeolokalisatie vanaf 2022',fontsize=11,color=GREY)
for yr,r in coverage.iterrows(): ax.annotate(f'{r.dekking_pct:.1f}%',(yr,r.dekking_pct),xytext=(0,9),textcoords='offset points',ha='center')
ax.set_title('Meer bruikbare locaties vanaf 2022',loc='left',pad=18)
ax.grid(axis='y',alpha=.15)
fig.tight_layout(rect=(0,.05,1,1))
export(fig,'02_kaartdekking','Bron: lokale Statbel-kaartdataset 2017–2024; bruikbaar = coördinaten binnen België + 1 km grensbuffer.')
'''),md('### 5. Concentraties in een vast raster\nVierkanten van 5 × 5 km in EPSG:31370, verankerd op gehele veelvouden van 5.000 meter. Alleen cellen met waarnemingen krijgen kleur. Dit zijn aantallen geregistreerde locaties, geen risico per weggebruiker.'),code('''
selected=points[points.analysis_year==YEAR].copy()
CELL=5000
selected['grid_x']=(selected.geometry.x//CELL).astype(int)
selected['grid_y']=(selected.geometry.y//CELL).astype(int)
counts=selected.groupby(['grid_x','grid_y']).size().rename('observaties').reset_index()
grid=gpd.GeoDataFrame(counts,geometry=[box(x*CELL,y*CELL,(x+1)*CELL,(y+1)*CELL)
    for x,y in zip(counts.grid_x,counts.grid_y)],crs=31370)
assert int(grid.observaties.sum())==len(selected)
grid.to_parquet(TABLES/'concentraties_5km_2024.parquet',index=False)
grid.drop(columns='geometry').sort_values('observaties',ascending=False).to_csv(TABLES/'concentraties_5km_2024.csv',index=False)
fig,ax=plt.subplots(figsize=(12,9)); base_map(ax)
grid.plot(ax=ax,column='observaties',cmap='YlOrRd',norm=LogNorm(vmin=1,vmax=grid.observaties.max()),
    linewidth=0,legend=True,legend_kwds={'label':'Kaartregistraties per 5 × 5 km (log-schaal)','shrink':.7})
major.plot(ax=ax,color='#526877',linewidth=.25,alpha=.7)
country.boundary.plot(ax=ax,color='#637784',linewidth=.8)
ax.set_title(f'Waar concentreren de geregistreerde letselongevallen zich? — {YEAR}',loc='left',pad=16)
ax.text(.01,.02,f'{number(len(selected))} bruikbare locaties • vaste cellen van 25 km²',transform=ax.transAxes,fontsize=10)
export(fig,'03_concentraties_2024','Statbel lokale kaartdata; © OSM contributors / Geofabrik 01-01-2025; © EuroGeographics / GISCO 2024. Aantallen ≠ risico.')
top_cells=grid.nlargest(10,'observaties').copy()
top_cells['aandeel_pct']=100*top_cells.observaties/len(selected)
display(top_cells.drop(columns='geometry').round(2))
'''),md('### 6. Detailvoorbeeld: Brussel\nAlleen een vast uitsnedevenster rond Brussel; dit is geen administratieve afbakening van het gewest. Punten worden niet automatisch aan het dichtstbijzijnde wegsegment gekoppeld.'),code('''
window=box(140000,160000,160000,180000)
local_roads=roads[roads.intersects(window)].copy()
local_roads.geometry=local_roads.geometry.intersection(window)
drivable=['motorway','motorway_link','trunk','trunk_link','primary','primary_link','secondary','secondary_link',
          'tertiary','tertiary_link','residential','unclassified','living_street','service']
local_roads=local_roads[local_roads.fclass.isin(drivable)]
local_points=selected[selected.intersects(window)]
fig,ax=plt.subplots(figsize=(11,9))
local_roads.plot(ax=ax,color='#ABB8C0',linewidth=.55)
local_points.plot(ax=ax,color=ORANGE,markersize=5,alpha=.4,rasterized=True)
ax.set(xlim=(140000,160000),ylim=(160000,180000)); ax.set_aspect('equal'); ax.set_axis_off()
ax.set_title(f'Brussel en omgeving: wegen en ongevalslocaties — {YEAR}',loc='left',pad=18)
ax.text(.01,.01,f'{number(len(local_points))} kaartpunten in dit venster',transform=ax.transAxes)
ax.plot([141000,146000],[161000,161000],color='#243440',lw=2); ax.text(143500,161300,'5 km',ha='center')
export(fig,'04_brussel_detail','Statbel lokale kaartdata; © OpenStreetMap contributors / Geofabrik 01-01-2025. Geen toewijzing aan individuele wegen.')
geo_summary={'usable_points':len(points),'selected_year':YEAR,'selected_points':len(selected),
 'coverage_2017':float(coverage.loc[2017,'dekking_pct']),'coverage_2024':float(coverage.loc[2024,'dekking_pct']),
 'missing_coordinates':int((~has_xy).sum()),'impossible_coordinates':int((has_xy & ~plausible).sum()),
 'outside_border':int((~inside).sum()),'map_total_difference_2024':int(coverage.loc[2024,'verschil_kaart_totaal']),
 'top10_cell_share':float(top_cells.aandeel_pct.sum()),'road_segments':len(roads)}
(TABLES/'geo_summary.json').write_text(json.dumps(geo_summary,indent=2),encoding='utf-8')
display(Markdown(f"**Resultaat:** de tien drukste rastercellen bevatten {geo_summary['top10_cell_share']:.1f}% van de bruikbare kaartregistraties van {YEAR}. "
 'Dit meet ruimtelijke concentratie; het is geen rangschikking van verkeersrisico.'))
'''),md('''
## Takeaways
1. Het wegennet en de locaties zijn met GeoPandas in één geprojecteerd stelsel gezet; de wegenlaag is daadwerkelijk vectorgeometrie.
2. Vergelijk kaartjaren altijd samen met de geolokalisatiedekking. De verbetering vanaf 2022 beperkt directe hotspot-trendvergelijkingen.
3. Coördinatenfouten worden zichtbaar gemaakt en uitgesloten van kaarten, zonder gold of de bron te wijzigen. Bekijk `tables/geo_uitgesloten.csv`.
4. Het kaartbestand telt in 2024 niet exact evenveel registraties als `SUM(MS_ACCT)`. Gebruik de algemene ongevalstabel voor nationale trends en de kaartbron voor ruimtelijke patronen.
5. Een volgende stap is onderzoek op wegsegmentniveau met verkeersintensiteiten en gevalideerde ongeval-wegkoppelingen. De huidige kaarten rechtvaardigen geen causale claims.

Bronnen: [Statbel geolokalisatie](https://statbel.fgov.be/nl/open-data/geolocalisatie-van-de-verkeersongevallen-2017-2024), [Geofabrik België](https://download.geofabrik.de/europe/belgium.html), [GISCO](https://gisco-services.ec.europa.eu/distribution/v2/countries/), [OSM-licentie](https://www.openstreetmap.org/copyright). Downloads, URL's en hashes: `reference_data/sources.json`. De notebooks draaien na download offline.
''')]

analysis=[md('''
# Verkeersveiligheid in België: analyse voor een presentatie
## tl;dr
Dit notebook vergelijkt de jaren 2017–2024 en onderzoekt in 2024 wanneer ongevallen gebeuren, wie de gewonde slachtoffers zijn en hoe de betrokken voertuigpopulatie is samengesteld. Alle conclusies worden uit de cellen hieronder berekend; losse figuren staan in `figures`.

## Context & Methods
De vier gold-datasets hebben verschillende detailniveaus. We aggregeren elke bron zelfstandig; er is geen join op ongevalniveau.

### Key Assumptions
- Ongevallen: `SUM(MS_ACCT)`. Slachtoffers: aparte sommen van lichtgewonden, zwaargewonden en doden binnen 30 dagen. Ongedeerden zijn geen gewonden.
- Ernstpercentage: (zwaargewonden + doden binnen 30 dagen) / (lichtgewonden + zwaargewonden + doden binnen 30 dagen). Dit is een verdeling **onder geregistreerde gewonden/doden**, geen ongevalsrisico per rit of inwoner.
- Voertuigen: `SUM(FL_VEHICLE)` in de aangeleverde voertuigbron; een ongeval kan meerdere voertuigen hebben. De populatie van die bron is niet identiek aan alle weggebruikers.
- Geen verkeersintensiteiten, afgelegde kilometers of voertuigpark als noemer. Verschillen naar weggebruikers/voertuigen zijn beschrijvend, niet causaal.
- Tijdpatronen worden gecorrigeerd voor het aantal kalenderdagen per weekdag; ongeldige/ontbrekende uren worden expliciet buiten de uurfiguur gehouden.
- Categorieën hebben soms gewijzigde labels; de analyse naar weggebruiker gebruikt een expliciete, exporteerbare groepering van codes en focust op 2024.
'''),code(COMMON),md('## Data\n### 1. Laden en tellingen vastleggen'),code('''
a=load('road_accidents'); v=load('road_casualties'); vehicles=load('vehicle_collisions')
annual=a.groupby('analysis_year').MS_ACCT.sum().rename('ongevallen').to_frame()
victim_annual=v.groupby('analysis_year')[['MS_SLY_INJ','MS_SERLY_INJ','MS_DEAD_30_DAYS','MS_VIC_OK']].sum()
annual=annual.join(victim_annual,validate='one_to_one')
annual['gewonden_en_doden']=annual.MS_SLY_INJ+annual.MS_SERLY_INJ+annual.MS_DEAD_30_DAYS
annual['ernstig_of_dood']=annual.MS_SERLY_INJ+annual.MS_DEAD_30_DAYS
annual['ernstaandeel_pct']=100*annual.ernstig_of_dood/annual.gewonden_en_doden
assert annual.ongevallen.sum()==a.MS_ACCT.sum()
assert annual.gewonden_en_doden.sum()==v[['MS_SLY_INJ','MS_SERLY_INJ','MS_DEAD_30_DAYS']].sum().sum()
annual.to_csv(TABLES/'jaartotalen.csv')
display(annual.round(2))
a24=a[a.analysis_year==YEAR].copy(); v24=v[v.analysis_year==YEAR].copy()
veh24=vehicles[vehicles.analysis_year==YEAR].copy()
v24['gewonden_en_doden']=v24.MS_SLY_INJ+v24.MS_SERLY_INJ+v24.MS_DEAD_30_DAYS
v24['ernstig_of_dood']=v24.MS_SERLY_INJ+v24.MS_DEAD_30_DAYS
'''),md('## Results\n### 2. Nationale ontwikkeling\nDrie afzonderlijke panelen houden de eenheden uit elkaar. De periode omvat 2020; de grafiek alleen identificeert geen oorzaak van de daling.'),code('''
fig,axes=plt.subplots(1,3,figsize=(15,6))
for ax,col,title,color in zip(axes,['ongevallen','MS_SERLY_INJ','MS_DEAD_30_DAYS'],
 ['Letselongevallen','Zwaargewonden','Doden binnen 30 dagen'],[BLUE,GREY,ORANGE]):
    ax.plot(annual.index,annual[col],marker='o',color=color,lw=2.5)
    ax.set_title(title,loc='left',fontsize=15); ax.set_ylim(bottom=0)
    ax.set_xticks([2017,2019,2021,2024]); ax.set_xlabel('Jaar'); ax.grid(axis='y',alpha=.15)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x,p:number(x)))
    change=100*(annual.loc[YEAR,col]/annual.loc[2017,col]-1)
    ax.text(.03,.94,f'{change:+.1f}% sinds 2017',transform=ax.transAxes,fontsize=13,color=color,va='top')
    ax.annotate(number(annual.loc[YEAR,col]),(YEAR,annual.loc[YEAR,col]),xytext=(-6,12),textcoords='offset points',ha='right',fontweight='bold')
fig.suptitle('Nationale ontwikkeling van geregistreerde letselongevallen en slachtoffers',x=.05,ha='left',fontweight='bold',fontsize=18)
fig.tight_layout(rect=(0,.07,1,.91))
export(fig,'05_nationale_trends','Bron: lokale Statbel gold-datasets 2017–2024. Ongevallen en personen zijn verschillende tel-eenheden.')
acc_change=float(100*(annual.loc[YEAR,'ongevallen']/annual.loc[2017,'ongevallen']-1))
death_change=float(100*(annual.loc[YEAR,'MS_DEAD_30_DAYS']/annual.loc[2017,'MS_DEAD_30_DAYS']-1))
display(Markdown(f"**Kernpunt:** {number(annual.loc[YEAR,'ongevallen'])} letselongevallen en {number(annual.loc[YEAR,'MS_DEAD_30_DAYS'])} doden binnen 30 dagen in {YEAR}. "
 f"Verandering tegenover 2017: {acc_change:+.1f}% en {death_change:+.1f}%."))
'''),md('### 3. Gewesten: volume en ernst afzonderlijk\nDe aandelen worden berekend binnen hetzelfde slachtofferbestand. Niet delen door aantallen ongevallen uit een andere bron om een individueel risico te suggereren.'),code('''
regions=a24.groupby('TX_RGN_DESCR_NL').MS_ACCT.sum().rename('ongevallen').to_frame()
vr=v24.groupby('TX_RGN_DESCR_NL')[['gewonden_en_doden','ernstig_of_dood']].sum()
regions=regions.join(vr,validate='one_to_one').sort_values('ongevallen')
regions['ernstaandeel_pct']=100*regions.ernstig_of_dood/regions.gewonden_en_doden
assert regions.ongevallen.sum()==a24.MS_ACCT.sum()
regions.to_csv(TABLES/'gewesten_2024.csv')
names={'Vlaams Gewest':'Vlaanderen','Waals Gewest':'Wallonië','Brussels Hoofdstedelijk Gewest':'Brussel'}
labels=[names.get(x,x) for x in regions.index]
fig,axes=plt.subplots(1,2,figsize=(13,6))
axes[0].barh(labels,regions.ongevallen,color=BLUE)
axes[0].set_title('Aantal letselongevallen',loc='left',fontsize=15)
axes[0].bar_label(axes[0].containers[0],labels=[number(x) for x in regions.ongevallen],padding=5)
axes[0].set_xlim(0,regions.ongevallen.max()*1.25)
axes[1].barh(labels,regions.ernstaandeel_pct,color=ORANGE)
axes[1].set_title('Ernstig of overleden onder gewonden/doden',loc='left',fontsize=14)
axes[1].bar_label(axes[1].containers[0],labels=[f'{x:.1f}%' for x in regions.ernstaandeel_pct],padding=5)
axes[1].set_xlim(0,regions.ernstaandeel_pct.max()*1.3); axes[1].set_xlabel('Percentage')
fig.suptitle(f'Volume en geregistreerde ernst geven een ander perspectief — {YEAR}',x=.03,ha='left',fontsize=17,fontweight='bold')
fig.tight_layout(rect=(0,.1,1,.9))
export(fig,'06_gewesten_volume_ernst','Bron: Statbel gold 2024. Ernst = (zwaargewonden + doden 30 dagen) / alle gewonden en doden; geen blootstellingsrisico.')
display(regions.round(2))
'''),md('### 4. Wanneer gebeuren ongevallen?\nGemiddeld aantal geregistreerde ongevallen per kalenderdag van de betreffende weekdag, per uur. Geen correctie voor verkeersdrukte; onbekende uren worden apart verantwoord.'),code('''
valid_hour=a24.DT_HOUR.between(0,23).fillna(False)
excluded_hour=int(a24.loc[~valid_hour,'MS_ACCT'].sum())
time_data=a24.loc[valid_hour].copy()
time_data['weekday']=time_data.DT_DAY.dt.dayofweek
counts=time_data.pivot_table(index='weekday',columns='DT_HOUR',values='MS_ACCT',aggfunc='sum',fill_value=0).reindex(index=range(7),columns=range(24),fill_value=0)
calendar=pd.date_range(f'{YEAR}-01-01',f'{YEAR}-12-31')
days=pd.Series(calendar.dayofweek).value_counts().sort_index()
heat=counts.div(days,axis=0)
heat.to_csv(TABLES/'weekdag_uur_gemiddeld_2024.csv')
assert int(counts.to_numpy().sum())+excluded_hour==int(a24.MS_ACCT.sum())
fig,ax=plt.subplots(figsize=(14,6))
im=ax.imshow(heat.to_numpy(dtype=float),cmap='YlOrRd',aspect='auto')
ax.set_yticks(range(7),['Ma','Di','Wo','Do','Vr','Za','Zo']); ax.set_xticks(range(0,24,2))
ax.set_xlabel('Uur van de dag'); ax.set_title(f'Tijdpatroon van letselongevallen — {YEAR}',loc='left',pad=18)
fig.colorbar(im,ax=ax,label='Ongevallen per kalenderdag van die weekdag en uur')
fig.tight_layout(rect=(0,.08,1,1))
export(fig,'07_weekdag_uur',f'Bron: Statbel ongevallen {YEAR}. {number(excluded_hour)} ongevallen met ongeldig/onbekend uur niet in de heatmap.')
peak=np.unravel_index(np.nanargmax(heat.to_numpy(dtype=float)),heat.shape)
weekday_names=['maandag','dinsdag','woensdag','donderdag','vrijdag','zaterdag','zondag']
display(Markdown(f"**Piek in deze registratie:** {weekday_names[peak[0]]} om {peak[1]} uur, gemiddeld {heat.iloc[peak]:.2f} ongevallen per betreffende kalenderdag. "
 f"{number(excluded_hour)} ongevallen hebben geen bruikbaar uur. Verkeersintensiteit is niet beschikbaar."))
'''),md('### 5. Welke weggebruikers dragen de geregistreerde letsellast?\nDe codegroepen hieronder zijn expliciet. Negatieve broncodes zijn echte categorieën in deze levering en worden niet als ontbrekend behandeld. De groepering is analytisch, geen nieuwe officiële classificatie.'),code('''
groups={
 'Auto / minibus / camper':['01','02','03','05'],
 'Fiets (zonder hulpmotor)':['18'],
 'E-fiets / speed pedelec':['25','26','27','-8'],
 'Motorfiets':['13','14','-5'],
 'Bromfiets':['15','16','17','-4'],
 'Voetganger / rolstoel':['20','21','22'],
 'Bestel- / vrachtverkeer':['04','06','07','08'],
 'Bus / tram':['10','11','12','-6'],
 'Step / voortbeweging':['28','95']}
lookup={c:name for name,codes in groups.items() for c in codes}
assert len(lookup)==sum(len(x) for x in groups.values())
v24['weggebruiker']=v24.CD_ROAD_USER_TYPE.map(lookup).fillna('Overig / onbekend')
mapping=v24[['CD_ROAD_USER_TYPE','TX_ROAD_USR_TYPE_DESCR_NL','weggebruiker']].drop_duplicates().sort_values('CD_ROAD_USER_TYPE')
mapping.to_csv(TABLES/'mapping_weggebruikers.csv',index=False)
mode=v24.groupby('weggebruiker')[['gewonden_en_doden','ernstig_of_dood','MS_DEAD_30_DAYS']].sum().sort_values('gewonden_en_doden')
mode['ernstaandeel_pct']=100*mode.ernstig_of_dood/mode.gewonden_en_doden.replace(0,np.nan)
assert mode.gewonden_en_doden.sum()==v24.gewonden_en_doden.sum()
mode.to_csv(TABLES/'weggebruikers_2024.csv')
fig,axes=plt.subplots(1,2,figsize=(15,8),gridspec_kw={'width_ratios':[1.25,1]})
axes[0].barh(mode.index,mode.gewonden_en_doden,color=BLUE)
axes[0].set_title('Aantal gewonden en doden',loc='left',fontsize=15)
axes[0].bar_label(axes[0].containers[0],labels=[number(x) for x in mode.gewonden_en_doden],padding=4,fontsize=9)
axes[0].set_xlim(0,mode.gewonden_en_doden.max()*1.25)
axes[1].barh(mode.index,mode.ernstaandeel_pct,color=ORANGE)
axes[1].set_yticks([]); axes[1].set_xlabel('Percentage ernstig of overleden')
axes[1].set_title('Ernstaandeel binnen dezelfde groep',loc='left',fontsize=15)
axes[1].bar_label(axes[1].containers[0],labels=[f'{x:.1f}%' for x in mode.ernstaandeel_pct],padding=4,fontsize=10)
axes[1].set_xlim(0,mode.ernstaandeel_pct.max()*1.25)
fig.suptitle(f'Weggebruikers: letsellast en geregistreerde ernst — {YEAR}',x=.03,ha='left',fontsize=18,fontweight='bold')
fig.tight_layout(rect=(0,.09,1,.92))
export(fig,'08_weggebruikers',f'Statbel slachtoffers {YEAR}; analytische codegroepering. Ernstig = zwaargewond of dood binnen 30 dagen. Geen risico per rit.')
display(mode.round(2))
'''),md('### 6. Voertuigpopulatie bij geregistreerde aanrijdingen\nDe grafiek toont samenstelling, niet welk voertuigtype intrinsiek gevaarlijker is. Een verandering van het aandeel kan samenhangen met het wagenpark, het gebruik, de registratie of de ongevalsbetrokkenheid.'),code('''
segment_names={'01':'Stadswagens','02':'Compacte auto’s','03':'Sedans','04':'SUV','05':'Monovolumes',
 '06':'Pick-up / bestel- / bedrijfswagen','07':'Vrachtwagens / bussen','08':'Motoren / bromfietsen',
 '09':'Sportwagens','99':'Onbekend'}
vehicles['segment']=vehicles.CD_VEHICLE_SEGMENT_B.map(segment_names).fillna('Onbekend')
mix=vehicles[vehicles.analysis_year.isin([2017,YEAR])].groupby(['analysis_year','segment']).FL_VEHICLE.sum().unstack(0,fill_value=0)
share=100*mix.div(mix.sum(axis=0),axis=1)
order=share[YEAR].sort_values().index; share=share.loc[order]
share.to_csv(TABLES/'voertuigmix_aandelen.csv'); mix.to_csv(TABLES/'voertuigmix_aantallen.csv')
fig,ax=plt.subplots(figsize=(13,7)); y=np.arange(len(share))
ax.barh(y-.18,share[2017],height=.34,color='#B7C9D2',label='2017')
ax.barh(y+.18,share[YEAR],height=.34,color=BLUE,label=str(YEAR))
ax.set_yticks(y,share.index); ax.set_xlabel('Aandeel van voertuigen in deze bron (%)')
ax.set_title('De mix van betrokken voertuigen verschuift',loc='left',pad=16); ax.legend(frameon=False)
ax.grid(axis='x',alpha=.12); fig.tight_layout(rect=(0,.09,1,1))
export(fig,'09_voertuigmix','Bron: Statbel voertuigbestand; som FL_VEHICLE. Geen correctie voor omvang/gebruik van het wagenpark.')
unknown_year_vehicles=int(vehicles.loc[vehicles.analysis_year.isna(),'FL_VEHICLE'].sum())
display(Markdown(f"**Afbakening:** {number(unknown_year_vehicles)} voertuigen zonder bronjaar zijn buiten de jaarvergelijking gehouden. "
 f"Het SUV-aandeel in deze bron gaat van {share.loc['SUV',2017]:.1f}% naar {share.loc['SUV',YEAR]:.1f}%. Dit bewijst geen groter individueel ongevalsrisico."))
'''),md('### 7. Maandpatroon met kalendercorrectie\nAantal ongevallen gedeeld door het aantal dagen in de betreffende maand. Deze correctie maakt maanden vergelijkbaar qua lengte, maar corrigeert niet voor verkeer of weer.'),code('''
monthly=a24.groupby('analysis_month').MS_ACCT.sum().reindex(range(1,13))
month_days=pd.Series({m:pd.Period(f'{YEAR}-{m:02d}').days_in_month for m in range(1,13)})
monthly_daily=monthly/month_days
pd.DataFrame({'ongevallen':monthly,'kalenderdagen':month_days,'gemiddeld_per_dag':monthly_daily}).to_csv(TABLES/'maandpatroon_2024.csv')
fig,ax=plt.subplots(figsize=(12,6)); ax.plot(range(1,13),monthly_daily,color=BLUE,marker='o',lw=2.5)
ax.set_xticks(range(1,13),['Jan','Feb','Mrt','Apr','Mei','Jun','Jul','Aug','Sep','Okt','Nov','Dec'])
ax.set_ylim(bottom=0); ax.set_ylabel('Gemiddeld aantal ongevallen per kalenderdag')
ax.set_title(f'Letselongevallen door het jaar — {YEAR}',loc='left',pad=16); ax.grid(axis='y',alpha=.15)
fig.tight_layout(rect=(0,.08,1,1)); export(fig,'10_maandpatroon',f'Bron: Statbel ongevallen {YEAR}; gecorrigeerd voor maandlengte, niet voor verkeersintensiteit.')
summary={'year':YEAR,'accidents_2024':int(annual.loc[YEAR,'ongevallen']),'deaths_2024':int(annual.loc[YEAR,'MS_DEAD_30_DAYS']),
 'seriously_injured_2024':int(annual.loc[YEAR,'MS_SERLY_INJ']),'accident_change_pct':acc_change,'death_change_pct':death_change,
 'invalid_hour_accidents_2024':excluded_hour,'peak_weekday':weekday_names[peak[0]],'peak_hour':int(peak[1]),
 'peak_accidents_per_day':float(heat.iloc[peak]),'suv_share_2017':float(share.loc['SUV',2017]),'suv_share_2024':float(share.loc['SUV',YEAR]),
 'unknown_year_vehicles':unknown_year_vehicles,'highest_severity_group':str(mode.ernstaandeel_pct.idxmax()),
 'highest_severity_pct':float(mode.ernstaandeel_pct.max())}
(TABLES/'analysis_summary.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False),encoding='utf-8')
'''),md('''
## Takeaways
- Gebruik de nationale trend als opening, gevolgd door het onderscheid tussen aantallen en geregistreerde ernst.
- De GeoPandas-kaarten geven ruimtelijke context. Vertel erbij hoeveel registraties geografisch bruikbaar zijn.
- De uur- en maandpatronen geven aanknopingspunten voor nader onderzoek. Zonder verkeersvolumes is er geen bewijs dat een tijdstip gevaarlijker is per rit.
- De letsellast per weggebruiker ondersteunt de keuze van vervolgvragen. De ernstpercentages zijn conditioneel op geregistreerde gewonden/doden en kunnen beïnvloed zijn door onderregistratie en samenstelling.
- De voertuigverdeling is een beschrijving van deze bron. Koppel een groeiend SUV-aandeel niet aan een causaal effect zonder wagenpark, gebruik en confounders te onderzoeken.

Alle exacte tabellen staan in `tables`. De berekende waarden staan in `tables/`. De eerdere datavoorbereiding staat in `../pipeline/HANDOVER.md`.

Brondefinities en beperkingen: [Statbel verkeersongevallen](https://statbel.fgov.be/nl/themas/mobiliteit/verkeer/verkeersongevallen), [methodologische nota voertuiggegevens](https://statbel.fgov.be/sites/default/files/files/opendata/Datalab-accidents/Accident_Method_en.pdf). De analyses gebruiken uitsluitend de aangeleverde periode 2017–2024, geen recentere tellingen van de website.
''')]

for name,cells in [('01_geopandas_belgie.ipynb',geo),('02_analyse_presentatie.ipynb',analysis)]:
    nb=nbf.v4.new_notebook(cells=cells,metadata={'kernelspec':{'display_name':'Python (MDP analyse)','language':'python','name':'python3'},'language_info':{'name':'python','version':'3.13'}})
    nbf.validate(nb); nbf.write(nb,BASE/name)
    print('Wrote',name)

