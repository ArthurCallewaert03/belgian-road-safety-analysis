"""Match fatal motorway-class crashes from every year to nearby OSM routes."""
from pathlib import Path
import json

import geopandas as gpd
import pandas as pd

from weather_categories import weather_category

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / 'dashboard_demo/dist/fatal_routes.json'


def build():
    source = pd.read_parquet(ROOT / 'data/gold/accident_map/accident_map.parquet', columns=[
        '_record_id', 'analysis_year', 'TX_RGN_COLLISION_NL',
        'TX_PROV_COLLISION_NL', 'TX_MUNTY_COLLISION_NL',
        'CD_ROAD_TYPE_NL', 'TX_COLLISION_TYPE_NL',
        'CD_CLASS_ACCIDENTS', 'CD_WEATHER', 'MS_X_COORD', 'MS_Y_COORD',
    ])
    fatal = source[(source.CD_ROAD_TYPE_NL == 'Autosnelweg') & (source.CD_CLASS_ACCIDENTS.astype(str) == '1')].copy()
    bad = set(pd.read_csv(ROOT / 'analysis_notebooks/tables/geo_uitgesloten.csv', usecols=['_record_id'])._record_id)
    located = fatal[~fatal._record_id.isin(bad)].copy()
    points = gpd.GeoDataFrame(located, geometry=gpd.points_from_xy(located.MS_X_COORD, located.MS_Y_COORD), crs=31370)
    roads = gpd.read_parquet(ROOT / 'analysis_notebooks/reference_data/roads_belgium.parquet', columns=['osm_id', 'fclass', 'name', 'ref', 'geometry'])
    drivable = {'motorway', 'motorway_link', 'trunk', 'trunk_link', 'primary', 'primary_link',
                'secondary', 'secondary_link', 'tertiary', 'tertiary_link', 'residential',
                'unclassified', 'living_street', 'service'}
    network = roads[roads.fclass.isin(drivable) & roads.geometry.notna()]
    match = gpd.sjoin_nearest(points, network, how='left', max_distance=30, distance_col='distance_m')
    match = match.sort_values(['_record_id', 'distance_m', 'osm_id']).drop_duplicates('_record_id')
    match['route'] = match['ref'].fillna(match['name'])
    match = match[match.route.notna()].copy()
    rows = [dict(
        year=int(r.analysis_year), region=r.TX_RGN_COLLISION_NL,
        province=r.TX_PROV_COLLISION_NL if pd.notna(r.TX_PROV_COLLISION_NL) else 'Brussels-Capital Region',
        municipality=r.TX_MUNTY_COLLISION_NL, road=r.CD_ROAD_TYPE_NL,
        collision=r.TX_COLLISION_TYPE_NL, severity=str(r.CD_CLASS_ACCIDENTS),
        weather=weather_category(r.CD_WEATHER), ref=str(r.route),
        osm_class=r.fclass, distance_m=round(float(r.distance_m), 1),
    ) for r in match.itertuples()]
    by_year = {str(year): dict(total=int((fatal.analysis_year == year).sum()),
                               located=int((located.analysis_year == year).sum()),
                               matched=sum(r['year'] == year for r in rows))
               for year in sorted(fatal.analysis_year.unique())}
    assert len(rows) <= len(located) <= len(fatal)
    assert by_year['2024']['total'] == 48 and by_year['2024']['matched'] == 46, by_year['2024']
    OUTPUT.write_text(json.dumps(dict(
        source='Fatal motorway-class crashes, 2017–2024; nearest named OSM drivable road within 30 m',
        total=len(fatal), located=len(located), matched=len(rows), by_year=by_year, rows=rows,
    ), ensure_ascii=False, separators=(',', ':'), default=lambda value: value.item()), encoding='utf-8')
    print('Fatal motorway crashes:', len(fatal), 'located:', len(located), 'named route matches:', len(rows))
    print('2024:', by_year['2024'])


if __name__ == '__main__':
    build()
