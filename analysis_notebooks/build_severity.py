from pathlib import Path
import nbformat as nb
p=Path(__file__).resolve().parent
def m(x):return nb.v4.new_markdown_cell(x)
def c(x):return nb.v4.new_code_cell(x)
cells=[m('''# Ernst van letselongevallen: wat valt op?

## Definitie
Dit notebook gebruikt het kaartbestand van Statbel. Een **ernstig ongeval** heeft bronklasse `1` (met doden), `2` (dodelijk gewonden) of `3` (zwaargewonden); klasse `4` heeft lichtgewonden. Het percentage is het aandeel onder geregistreerde letselongevallen, geen kans per rit. De kaartbron van 2024 telt 35.916 registraties, 16 minder dan de algemene ongevalstabel. Alle nationale vergelijkingen hieronder gebruiken uitsluitend de kaartbron.'''),c('''from pathlib import Path
import pandas as pd,numpy as np,matplotlib.pyplot as plt
from IPython.display import display
B=Path.cwd()
if not (B/'figures').exists():B=B/'analysis_notebooks'
F=B/'figures';T=B/'tables';G=B.parent/'data/gold'
d=pd.read_parquet(G/'accident_map/accident_map.parquet')
d['ernstig']=d.CD_CLASS_ACCIDENTS.isin(['1','2','3']);x=d[d.analysis_year==2024].copy()
def tab(group,min_n=100):
 z=x.groupby(group,dropna=False).agg(ongevallen=('_record_id','count'),ernstig=('ernstig','sum'))
 z['ernst_pct']=100*z.ernstig/z.ongevallen
 return z[z.ongevallen>=min_n].sort_values('ernst_pct',ascending=False)
def plot(z,title,name):
 fig,ax=plt.subplots(figsize=(11,6));z.ernst_pct.sort_values().plot.barh(ax=ax,color='#D76B32');ax.set(title=title,xlabel='Ernstige ongevallen / alle letselongevallen (%)',ylabel='');fig.tight_layout();fig.savefig(F/(name+'.png'),dpi=200,bbox_inches='tight');fig.savefig(F/(name+'.svg'),bbox_inches='tight');plt.show();plt.close(fig)
'''),m('''## 1. Verandert de ernstverdeling door de jaren?
Controleer teller, noemer en aandeel. Een verschuiving in registratie of samenstelling kan het aandeel beïnvloeden.'''),c('''annual=d.groupby('analysis_year').agg(ongevallen=('_record_id','count'),ernstig=('ernstig','sum'));annual['ernst_pct']=100*annual.ernstig/annual.ongevallen
annual.to_csv(T/'ernst_per_jaar_kaart.csv');display(annual.round(2))
fig,ax=plt.subplots(figsize=(10,5));annual.ernst_pct.plot(ax=ax,marker='o',color='#175A78');ax.set(title='Aandeel ernstige letselongevallen per jaar',ylabel='Ernstig (%)',xlabel='Jaar');fig.tight_layout();fig.savefig(F/'18_ernst_trend.png',dpi=200,bbox_inches='tight');fig.savefig(F/'18_ernst_trend.svg',bbox_inches='tight');plt.show();plt.close(fig)
'''),m('''## 2. Botsingstype: een val of een aanrijding?
Sommige typen hebben weinig ongevallen maar een hoger aandeel ernstige gevolgen. De figuur toont alleen typen met minstens 100 registraties.'''),c('''types=tab('TX_COLLISION_TYPE_NL');types.to_csv(T/'ernst_per_botsingstype_2024.csv');display(types.round(2));plot(types,'Ernstverdeling per ongevalstype, 2024','19_ernst_botsingstype')
'''),m('''## 3. Licht en locatieconditie
Onbekend is een aparte categorie. Het verschil tussen dag en onverlichte nacht kan samenhangen met snelheid, tijdstip, type weg of type ongeval. Deze analyse toont verbanden, geen effect van verlichting.'''),c('''light=tab('TX_LIGHT_CONDITION_NL');light.to_csv(T/'ernst_per_licht_2024.csv');display(light.round(2));plot(light,'Ernstverdeling naar lichtomstandigheid, 2024','20_ernst_licht')
junction=tab('TX_CROSSWAY_NL');junction.to_csv(T/'ernst_per_kruispunt_2024.csv');display(junction.round(2))
'''),m('''## 4. Houdt het nachtverschil stand binnen wegtype en botsingstype?
We vergelijken dag en onverlichte nacht in dezelfde wegtypecategorie. Daarna bekijken we de samenstelling van ongevalstypen. Kleine cellen worden niet als betrouwbare ranglijst behandeld.'''),c('''choice=['Dag','Nacht, geen openbare verlichting aanwezig'];z=x[x.TX_LIGHT_CONDITION_NL.isin(choice)]
cross=z.groupby(['CD_ROAD_TYPE_NL','TX_LIGHT_CONDITION_NL']).agg(n=('_record_id','count'),ernstig=('ernstig','sum'));cross['ernst_pct']=100*cross.ernstig/cross.n
cross.to_csv(T/'ernst_licht_binnen_wegtype.csv');display(cross.round(2))
mix=pd.crosstab(z.TX_LIGHT_CONDITION_NL,z.TX_COLLISION_TYPE_NL,normalize='index')*100
mix.to_csv(T/'botsingstype_mix_dag_nacht.csv');display(mix.round(1).T.sort_values('Nacht, geen openbare verlichting aanwezig',ascending=False).head(8))
'''),m('''## 5. Waar liggen concentraties van ernstige ongevallen?
Een vast raster van 500 meter toont cellen met minstens 20 gegeocodeerde letselongevallen. De kaartregistraties zonder valide coördinaten blijven in de nationale tabellen, maar zijn niet op de kaart te lokaliseren. Cellen met de meeste ernstige ongevallen worden als **onderzoeksgebieden** genoemd, niet als bewijs voor een lokale oorzaak.'''),c('''import geopandas as gpd
bad=set(pd.read_csv(T/'geo_uitgesloten.csv',usecols=['_record_id'])._record_id)
located=x[~x._record_id.isin(bad)].copy();located['gx']=(located.MS_X_COORD//500).astype(int);located['gy']=(located.MS_Y_COORD//500).astype(int)
cells=located.groupby(['gx','gy']).agg(ongevallen=('_record_id','count'),ernstig=('ernstig','sum'),gemeente=('TX_MUNTY_COLLISION_NL',lambda s:s.mode().iloc[0] if not s.mode().empty else 'Onbekend'))
cells=cells[cells.ongevallen>=20].copy();cells['ernst_pct']=100*cells.ernstig/cells.ongevallen
cells.sort_values(['ernstig','ongevallen'],ascending=False).to_csv(T/'ernstige_locaties_500m_2024.csv')
display(cells.sort_values(['ernstig','ongevallen'],ascending=False).head(15).round(1))
fig,ax=plt.subplots(figsize=(10,8));country=gpd.read_file(B/'reference_data/belgium_2024.geojson').to_crs(31370);country.plot(ax=ax,color='#F5F6F7',edgecolor='#9BA9B2')
top=cells.sort_values('ernstig',ascending=False).head(20).reset_index();ax.scatter((top.gx+.5)*500,(top.gy+.5)*500,s=top.ernstig*80,color='#D76B32',alpha=.7,edgecolor='white');ax.set(title='Onderzoeksgebieden met veel ernstige ongevallen, 2024');ax.axis('off');fig.tight_layout();fig.savefig(F/'21_ernstige_locaties.png',dpi=200,bbox_inches='tight');fig.savefig(F/'21_ernstige_locaties.svg',bbox_inches='tight');plt.show();plt.close(fig)
'''),m('''## Vervolg voor de presentatie
De hoogste percentages zijn signalen voor gerichte vragen. Controleer per kandidaatlocatie het type botsing, het wegontwerp, zicht, snelheid en verkeersintensiteit. Een ernstig aandeel zonder noemer voor afgelegde kilometers is geen individueel risico. Een kaartcel kan meerdere wegen en kruispunten omvatten; bevestig de locatie voordat je maatregelen aan een weg koppelt.''')]
cells.insert(-1,m('''## 6. Een concrete locatie nader bekijken
De 500-m-cel met de meeste ernstige ongevallen in 2024 ligt in Antwerpen. We bekijken alle botsingstypen en omstandigheden in die cel, inclusief de lichte ongevallen. Dit levert een onderzoeksvraag op, geen bewijs voor een oorzaak.'''))
cells.insert(-1,c('''top_cell=cells.sort_values(['ernstig','ongevallen'],ascending=False).head(1).reset_index().iloc[0]
case=located[(located.gx==top_cell.gx)&(located.gy==top_cell.gy)].copy()
cols=['_record_id','TX_MUNTY_COLLISION_NL','CD_ROAD_TYPE_NL','TX_COLLISION_TYPE_NL','TX_CROSSWAY_NL','TX_LIGHT_CONDITION_NL','TX_CLASS_ACCIDENTS_NL']
case[cols].to_csv(T/'ernstigste_cel_bronregels_2024.csv',index=False)
for col in cols[2:]:
 print('\\n'+col);display(case[col].value_counts(dropna=False).to_frame('ongevallen'))
print('Celcentrum in Lambert 72:',(top_cell.gx+.5)*500,(top_cell.gy+.5)*500)
'''))
b=nb.v4.new_notebook(cells=cells,metadata={'kernelspec':{'display_name':'Python (MDP analyse)','language':'python','name':'mdp-analysis'}});nb.validate(b);nb.write(b,p/'05_ernst_verdieping.ipynb')
