from pathlib import Path
import json,hashlib
import pandas as pd
import geopandas as gpd
from shapely.geometry import mapping, box
B=Path(__file__).resolve().parent; ROOT=B.parent; OUT=B/'dist';OUT.mkdir(exist_ok=True)
d=pd.read_parquet(ROOT/'data/gold/accident_map/accident_map.parquet')
bad=set(pd.read_csv(ROOT/'analysis_notebooks/tables/geo_uitgesloten.csv',usecols=['_record_id'])._record_id)
e=d[['_record_id','analysis_year','analysis_month','TX_RGN_COLLISION_NL','CD_ROAD_TYPE_NL','TX_COLLISION_TYPE_NL','CD_CLASS_ACCIDENTS','TX_MUNTY_COLLISION_NL','MS_X_COORD','MS_Y_COORD','TX_PROV_COLLISION_NL']].copy()
e['valid']=~e._record_id.isin(bad)
e['gx']=(e.MS_X_COORD//5000).where(e.valid).astype('Int64')
e['gy']=(e.MS_Y_COORD//5000).where(e.valid).astype('Int64')
e['gx500']=(e.MS_X_COORD//500).where(e.valid).astype('Int64')
e['gy500']=(e.MS_Y_COORD//500).where(e.valid).astype('Int64')
e['x']=e.MS_X_COORD.round(-1).where(e.valid).astype('Int64')
e['y']=e.MS_Y_COORD.round(-1).where(e.valid).astype('Int64')
e=e.drop(columns=['_record_id','MS_X_COORD','MS_Y_COORD'])
e.columns=['year','month','region','road','collision','severity','municipality','province','valid','gx','gy','gx500','gy500','x','y']
e=e[['year','month','region','road','collision','severity','municipality','valid','gx','gy','gx500','gy500','x','y','province']]
e['province']=e['province'].fillna('Brussels-Capital Region')
for c in ['region','road','collision','severity','municipality','province'] : e[c]=e[c].fillna('Onbekend').astype(str)
cats={c:sorted(e[c].unique().tolist()) for c in ['region','road','collision','severity','municipality','province']}
for c in cats: e[c]=pd.Categorical(e[c],categories=cats[c]).codes
rows=[[None if pd.isna(v) else int(v) if c!='valid' else bool(v) for c,v in zip(e.columns,row)] for row in e.itertuples(index=False,name=None)]
geo=gpd.read_file(ROOT/'analysis_notebooks/reference_data/belgium_2024.geojson').to_crs(31370)
shape=mapping(geo.geometry.iloc[0].simplify(300,preserve_topology=True))
meta={'columns':list(e.columns),'categories':cats,'years':sorted(int(x) for x in e.year.dropna().unique()),'source_rows':len(e),'source':'Statbel kaartbestand 2017–2024, gold/accident_map.parquet','geometry_source':'Eurostat/GISCO België 2024, 1:1 miljoen','coordinate_crs':'EPSG:31370 (plausibiliteitsaanname)','rows_sha256':hashlib.sha256((ROOT/'data/gold/accident_map/accident_map.parquet').read_bytes()).hexdigest()}
(OUT/'data.json').write_text(json.dumps({'meta':meta,'rows':rows,'shape':shape},ensure_ascii=False,separators=(',',':')),encoding='utf-8')
print('Rows:',len(rows),'JSON MB:',round((OUT/'data.json').stat().st_size/1e6,1))

# OSM-vectorwegen voor dezelfde drie kaartschaalniveaus als het GeoPandas-notebook.
roads=gpd.read_parquet(ROOT/'analysis_notebooks/reference_data/roads_belgium.parquet',columns=['fclass','name','ref','geometry'])
major_classes={'motorway','motorway_link','trunk','trunk_link','primary','primary_link','secondary','secondary_link'}
drivable=major_classes|{'tertiary','tertiary_link','residential','unclassified','living_street','service'}
brussels=box(140000,160000,160000,180000)
local=roads.iloc[roads.sindex.query(brussels,predicate='intersects')]
def paths(frame,tolerance,step):
    result=[]
    for geom in frame.geometry:
        if geom.is_empty: continue
        geom=geom.simplify(tolerance,preserve_topology=False)
        lines=[geom] if geom.geom_type=='LineString' else list(geom.geoms) if geom.geom_type=='MultiLineString' else []
        for line in lines:
            pts=[]
            for x,y in line.coords:
                q=[round(x/step)*step,round(y/step)*step]
                if not pts or pts[-1]!=q: pts.append(q)
            if len(pts)>1: result.append(pts)
    return result
def named_paths(frame,tolerance,step):
    result=[]
    for row in frame.itertuples():
        name=str(row.name).strip() if pd.notna(row.name) else ''
        ref=str(row.ref).strip() if pd.notna(row.ref) else ''
        if not name and not ref: continue
        label=' · '.join(x for x in [ref,name] if x)
        geom=row.geometry.simplify(tolerance,preserve_topology=False)
        lines=[geom] if geom.geom_type=='LineString' else list(geom.geoms) if geom.geom_type=='MultiLineString' else []
        for line in lines:
            pts=[]
            for x,y in line.coords:
                q=[round(x/step)*step,round(y/step)*step]
                if not pts or pts[-1]!=q: pts.append(q)
            if len(pts)>1: result.append([label,row.fclass,pts])
    return result
roads_out={
    'motorways':paths(roads[roads.fclass.isin({'motorway','motorway_link'})],60,50),
    'major':paths(roads[roads.fclass.isin(major_classes-{'motorway','motorway_link'})],70,50),
    'brussels_local':paths(local[local.fclass.isin(drivable-major_classes)],25,20),
    'named_major':named_paths(roads[roads.fclass.isin(major_classes)],70,50),
    'named_brussels_local':named_paths(local[local.fclass.isin(drivable-major_classes)],25,20),
    'brussels_window':[140000,160000,160000,180000],
    'source':'OpenStreetMap / Geofabrik 2025-01-01; cache uit analysis_notebooks/reference_data/roads_belgium.parquet'
}
(OUT/'roads.json').write_text(json.dumps(roads_out,separators=(',',':')),encoding='utf-8')
print('Road vectors MB:',round((OUT/'roads.json').stat().st_size/1e6,1))

