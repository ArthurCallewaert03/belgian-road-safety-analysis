"""Reproducible local bronze/silver/gold preparation. Run with Python 3 + requirements.txt."""
from pathlib import Path
import hashlib, json, shutil, platform, datetime, sys
import pandas as pd
import openpyxl
import pyarrow

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
DOC = ROOT / 'pipeline'
GROUPS = {'road_accidents':'Road accidents', 'road_casualties':'Road casualties', 'vehicle_collisions':'Traffic accidents by type of vehicle', 'accident_map':None}
manifest, checks, profiles, decisions, catalog, metadata, schema_changes = [], [], [], [], [], [], []

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()

def read_sheet(path):
    w=openpyxl.load_workbook(path,read_only=True,data_only=True)
    assert len(w.sheetnames)==1, f'Unexpected sheets: {path}'
    s=w.active; title=s.title; declared=s.max_row
    s.reset_dimensions()  # Several sources declare 1,048,576 rows due to formatting.
    rows=[]; positions=[]
    for i,row in enumerate(s.iter_rows(values_only=True),1):
        if any(v is not None and v!='' for v in row): rows.append(list(row)); positions.append(i)
    w.close()
    return title,declared,rows,positions

def save_json(name,obj):
    (DOC/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2,default=str),encoding='utf-8')

def check(ds,rule,bad,detail=''):
    checks.append(dict(dataset=ds,rule=rule,failed_rows=int(bad),status='PASS' if bad==0 else 'REVIEW',detail=detail))

def main():
    if '--resume' in sys.argv:
        for name,target in [('catalog.json',catalog),('quality_checks.json',checks),('schema_changes.json',schema_changes)]:
            if (DOC/name).exists(): target.extend(json.loads((DOC/name).read_text(encoding='utf-8')))
        for name,target in [('data_dictionary.csv',profiles),('transformation_log.csv',decisions),('source_metadata.csv',metadata)]:
            if (DOC/name).exists(): target.extend(pd.read_csv(DOC/name).fillna('').to_dict('records'))
    for layer in ['bronze/raw','bronze/tables','silver','gold']:
        (DATA/layer).mkdir(parents=True,exist_ok=True)
    # Preserve originals byte for byte; never overwrite a changed bronze snapshot.
    sources=sorted(p for p in DATA.rglob('*.xlsx') if not any(x in p.relative_to(DATA).parts for x in ['bronze','silver','gold']))
    if not sources: sources=sorted((DATA/'bronze/raw').rglob('*.xlsx'))
    for src in sources:
        rel=src.relative_to(DATA/'bronze/raw') if src.is_relative_to(DATA/'bronze/raw') else src.relative_to(DATA)
        dst=DATA/'bronze/raw'/rel; dst.parent.mkdir(parents=True,exist_ok=True)
        digest=sha(src)
        if dst.exists(): assert sha(dst)==digest, f'Bronze source changed: {rel}'
        else: shutil.copy2(src,dst)
        assert sha(dst)==digest
        manifest.append(dict(source=str(rel),bronze_raw=str(dst.relative_to(ROOT)),sha256=digest,bytes=dst.stat().st_size))
    save_json('source_manifest.json',manifest)
    for ds,folder in GROUPS.items():
        if ds in [x['dataset'] for x in catalog]: continue
        paths=sorted((DATA/'bronze/raw'/folder).glob('*.xlsx')) if folder else [DATA/'bronze/raw/OPENDATA_MAP_2017-2024.xlsx']
        frames=[]; definitions={}; baseline=None; partitions=[]
        for p in paths:
            print('READ',ds,p.name,flush=True)
            cache=DATA/'bronze/tables'/ds/(p.stem+'.parquet')
            if '--resume' in sys.argv and cache.exists():
                frame=pd.read_parquet(cache); header=[c for c in frame if not c.startswith('_')]
                if baseline is None: baseline=header
                w=openpyxl.load_workbook(p,read_only=True,data_only=True); declared=w.active.max_row; w.close()
                schema_changes.append(dict(dataset=ds,file=p.name,added=sorted(set(header)-set(baseline)),missing=sorted(set(baseline)-set(header)),declared_excel_rows=declared,actual_data_rows=len(frame)))
                partitions.append(dict(file=p.name,rows=len(frame))); frames.append(frame)
                continue
            sheet,declared,rows,positions=read_sheet(p)
            if not any(str(y) in p.stem for y in range(2017,2025)):
                for row in rows:
                    if row[0] in ('NAME','Variables in Creation Order','#'): continue
                    variable=row[1] if len(row)>2 else row[0]
                    label=row[5] if len(row)>2 else row[1]
                    definitions[variable]=label
                    metadata.append(dict(dataset=ds,source=p.name,variable=variable,description=label,raw_row=json.dumps(row,ensure_ascii=False)))
                continue
            header=[str(v).strip() for v in rows[0]]
            assert len(set(header))==len(header)
            frame=pd.DataFrame([r[:len(header)]+[None]*max(0,len(header)-len(r)) for r in rows[1:]],columns=header)
            # Bronze tabular extraction uses strings to preserve lexical codes and avoid mixed type coercion.
            for c in header: frame[c]=frame[c].map(lambda v: None if v is None else str(v)).astype('string')
            frame['_source_file']=str(p.relative_to(DATA/'bronze/raw')); frame['_source_sheet']=sheet
            frame['_source_row']=positions[1:]
            frame['_record_id']=[f'{ds}:{p.stem}:{i}' for i in positions[1:]]
            out=DATA/'bronze/tables'/ds; out.mkdir(parents=True,exist_ok=True)
            frame.to_parquet(out/(p.stem+'.parquet'),index=False)
            if baseline is None: baseline=header
            schema_changes.append(dict(dataset=ds,file=p.name,added=sorted(set(header)-set(baseline)),missing=sorted(set(baseline)-set(header)),declared_excel_rows=declared,actual_data_rows=len(frame)))
            partitions.append(dict(file=p.name,rows=len(frame)))
            frames.append(frame)
        df=pd.concat(frames,ignore_index=True); original=[c for c in df if not c.startswith('_')]
        for c in original:
            s=df[c]; trimmed=s.str.strip(); trimmed=trimmed.mask(trimmed.eq(''))
            changes=int((s.fillna('')!=trimmed.fillna('')).sum())
            if changes: decisions.append(dict(dataset=ds,column=c,action='trim_whitespace',reason='Normalize surrounding whitespace; empty string to null',affected=changes))
            df[c]=trimmed
            numeric=c.startswith('MS_') or (c.startswith('FL_') and c!='FL_WEEKEND') or c in ['DT_HOUR','DT_YEAR_COLLISION','DT_MONTH_COLLISION','DT_TIME']
            if numeric:
                sentinel=trimmed.eq('nan').fillna(False)
                if sentinel.any():
                    decisions.append(dict(dataset=ds,column=c,action='nan_literal_to_null',reason='Non-numeric literal nan in numeric source field; preserve original in bronze',affected=int(sentinel.sum())))
                    trimmed=trimmed.mask(sentinel)
                v=pd.to_numeric(trimmed,errors='coerce'); bad=trimmed.notna() & v.isna()
                check(ds,'parse_numeric:'+c,bad.sum()); assert not bad.any(),c
                df[c]=v.astype('Int64' if ((v.dropna()%1)==0).all() else 'Float64')
            elif c=='DT_DAY':
                v=pd.to_datetime(trimmed,errors='coerce'); bad=trimmed.notna() & v.isna()
                check(ds,'parse_date',bad.sum()); assert not bad.any()
                df[c]=v
        if 'DT_DAY' in df:
            df['analysis_year']=df.DT_DAY.dt.year.astype('Int64'); df['analysis_month']=df.DT_DAY.dt.month.astype('Int64')
            check(ds,'weekday_matches_date',(df.CD_DAY_OF_WEEK.astype('Int64')!=df.DT_DAY.dt.dayofweek+1).sum())
        else:
            df['analysis_year']=df.DT_YEAR_COLLISION; df['analysis_month']=df.DT_MONTH_COLLISION
        check(ds,'year_range',(~df.analysis_year.between(2017,2024) | df.analysis_year.isna()).sum())
        check(ds,'month_range',(~df.analysis_month.between(1,12) | df.analysis_month.isna()).sum())
        if folder:
            expected=df._source_file.str.extract(r'(20\d{2})\.xlsx$',expand=False).astype('Int64')
            check(ds,'filename_year_matches_data',(expected!=df.analysis_year).sum())
        check(ds,'unique_technical_record_id',df._record_id.duplicated().sum())
        check(ds,'identical_source_rows_retained',df.duplicated(subset=original).sum(),'Informational: no event ID; identical observations can represent separate events. Never automatically deduplicate.')
        for c in original:
            if c.startswith('MS_') or (c.startswith('FL_') and c!='FL_WEEKEND'):
                check(ds,'negative_value:'+c,(df[c]<0).sum(),'Negative values retained for review; may be source sentinel codes.')
            if c.startswith('FL_') and c not in ['FL_VEHICLE','FL_WEEKEND']:
                check(ds,'binary_flag:'+c,(df[c].notna() & ~df[c].isin([0,1])).sum())
        if ds=='road_casualties': check(ds,'victim_components_sum',(df.MS_VICT!=df[['MS_VIC_OK','MS_SLY_INJ','MS_SERLY_INJ','MS_DEAD_30_DAYS']].sum(axis=1,min_count=4)).sum())
        if 'DT_HOUR' in df: check(ds,'hour_range',(~df.DT_HOUR.between(0,23)&df.DT_HOUR.notna()).sum(),'Out-of-range source values retained; review unknown hour codes.')
        silver=DATA/'silver'/ds; silver.mkdir(exist_ok=True)
        df.to_parquet(silver/(ds+'.parquet'),index=False)
        drop=[]
        for c in original:
            partner=c[:-3]+'_NL' if c.endswith('_FR') else None
            if c=='TX_COLLISON_TYPE_FR' and 'TX_COLLISION_TYPE_NL' in df: partner='TX_COLLISION_TYPE_NL'
            if partner in df and not (df[c].notna() & df[partner].isna()).any():
                drop.append(c); reason='French label removed; Dutch counterpart populated wherever French is populated: '+partner
            elif df[c].isna().all(): drop.append(c); reason='Entire column empty across all source years'
            else: continue
            decisions.append(dict(dataset=ds,column=c,action='drop_from_gold',reason=reason,affected=len(df)))
        gold=df.drop(columns=drop)
        dest=DATA/'gold'/ds; dest.mkdir(exist_ok=True)
        gold.to_parquet(dest/(ds+'.parquet'),index=False)
        gold.to_csv(dest/(ds+'.csv'),index=False,encoding='utf-8-sig')
        aliases={'MS_VICT':'MS_VCT','CD_VICT_TYPE':'CD_VCT_TYPE','TX_VICT_TYPE_DESCR_NL':'TX_VCT_TYPE_DESCR_NL','TX_VICT_TYPE_DESCR_FR':'TX_VCT_TYPE_DESCR_FR','CD_ROAD_USER_TYPE':'CD_ROAD_USR_TYPE','TX_VEHICLE_CLASS_AGE_AT_COLL_YR':'TX_CLASS_VEHICLE_AGE_AT_COLL_YR'}
        for c in df:
            meta=aliases.get(c,c); desc=definitions.get(meta)
            if c.startswith('_'): desc='Technical provenance; not a business event key'
            if c in ['analysis_year','analysis_month']: desc='Derived calendar component from source date/year/month'
            profiles.append(dict(dataset=ds,column=c,type=str(df[c].dtype),rows=len(df),nulls=int(df[c].isna().sum()),distinct=int(df[c].nunique()),in_gold=c in gold,description=desc or '',metadata_match='exact' if c in definitions else ('alias' if meta in definitions else 'not_documented'),min=str(df[c].min()) if pd.api.types.is_numeric_dtype(df[c]) else '',max=str(df[c].max()) if pd.api.types.is_numeric_dtype(df[c]) else ''))
        # Read-back verifies serialization, schema, values, row order and measures.
        pd.testing.assert_frame_equal(pd.read_parquet(silver/(ds+'.parquet')),df)
        pd.testing.assert_frame_equal(pd.read_parquet(dest/(ds+'.parquet')),gold)
        check(ds,'bronze_silver_row_reconciliation',abs(sum(x['rows'] for x in partitions)-len(df)))
        check(ds,'silver_gold_row_reconciliation',abs(len(df)-len(gold)))
        catalog.append(dict(dataset=ds,rows=len(df),source_columns=len(original),silver_columns=len(df.columns),gold_columns=len(gold.columns),removed_columns=drop,partitions=partitions,years=sorted(int(v) for v in df.analysis_year.dropna().unique())))
        print('DONE',ds,len(df),len(df.columns),len(gold.columns),flush=True)
        # Save progress after each dataset.
        for name,obj in [('catalog.json',catalog),('quality_checks.json',checks),('schema_changes.json',schema_changes)]: save_json(name,obj)
        for name,obj in [('data_dictionary.csv',profiles),('transformation_log.csv',decisions),('source_metadata.csv',metadata)]: pd.DataFrame(obj).to_csv(DOC/name,index=False,encoding='utf-8-sig')
    save_json('run.json',dict(completed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),python=platform.python_version(),pandas=pd.__version__,openpyxl=openpyxl.__version__,pyarrow=pyarrow.__version__,script_sha256=sha(Path(__file__))))
    print('COMPLETE',flush=True)

if __name__=='__main__': main()

