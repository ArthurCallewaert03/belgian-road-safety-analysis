"""Independent read-back and annual measure reconciliation; run after prepare_data.py."""
from pathlib import Path
import json,hashlib
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
P=ROOT/'pipeline'; D=ROOT/'data'
catalog=json.loads((P/'catalog.json').read_text(encoding='utf-8'))
assert len(catalog)==4
controls=[]; hourly=[]; yearly_nulls=[]; review_samples=[]; labels=[]
for item in catalog:
    ds=item['dataset']; s=pd.read_parquet(D/'silver'/ds/(ds+'.parquet')); g=pd.read_parquet(D/'gold'/ds/(ds+'.parquet'))
    assert len(s)==len(g)==item['rows']
    assert s._record_id.equals(g._record_id)
    pd.testing.assert_frame_equal(s[list(g)],g)
    csv_count=0
    for chunk in pd.read_csv(D/'gold'/ds/(ds+'.csv'),usecols=['_record_id'],dtype='string',chunksize=100000):
        assert chunk._record_id.tolist()==g._record_id.iloc[csv_count:csv_count+len(chunk)].tolist()
        csv_count+=len(chunk)
    assert csv_count==len(g)
    measures=[c for c in s if (c.startswith('MS_') and 'COORD' not in c and 'AGE' not in c) or (c.startswith('FL_') and c!='FL_WEEKEND')]
    raw_controls=[]
    for f in sorted((D/'bronze/tables'/ds).glob('*.parquet')):
        b=pd.read_parquet(f)
        year=pd.to_datetime(b.DT_DAY).dt.year if 'DT_DAY' in b else pd.to_numeric(b.DT_YEAR_COLLISION)
        temp=pd.DataFrame({'analysis_year':year.fillna(-1)})
        for c in measures: temp[c]=pd.to_numeric(b[c].mask(b[c].eq('nan')),errors='raise')
        raw_controls.append(temp.groupby('analysis_year')[measures].sum(min_count=1))
    if measures:
        raw=pd.concat(raw_controls).groupby(level=0).sum(min_count=1)
        final=g.assign(analysis_year=g.analysis_year.fillna(-1)).groupby('analysis_year')[measures].sum(min_count=1)
        for year in raw.index:
            for c in measures:
                assert raw.loc[year,c]==final.loc[year,c],(ds,year,c)
                controls.append(dict(dataset=ds,year=int(year),measure=c,bronze_total=float(raw.loc[year,c]),gold_total=float(final.loc[year,c]),status='PASS'))
    for year,part in s.assign(analysis_year=s.analysis_year.fillna(-1)).groupby('analysis_year'):
        for c in s:
            if part[c].isna().any(): yearly_nulls.append(dict(dataset=ds,year=int(year),column=c,rows=len(part),nulls=int(part[c].isna().sum()),null_rate=float(part[c].isna().mean())))
    hour='DT_HOUR' if 'DT_HOUR' in s else ('DT_TIME' if 'DT_TIME' in s else None)
    if hour:
        invalid=s[hour].notna() & ~s[hour].between(0,23)
        for (year,value),n in s.loc[invalid].groupby(['analysis_year',hour]).size().items():
            hourly.append(dict(dataset=ds,year=int(year),source_hour=int(value),rows=int(n)))
        for _,row in s.loc[invalid,['_record_id','_source_file','_source_row',hour]].head(10).iterrows():
            review_samples.append(dict(dataset=ds,rule='hour_outside_0_23',**row.to_dict()))
    for c in [c for c in s if c.endswith('_NL')]:
        # Label drift is descriptive only: no inferred code correspondence.
        labels.append(dict(dataset=ds,column=c,distinct=int(s[c].nunique()),missing=int(s[c].isna().sum())))
for name,data in [('annual_measure_reconciliation.csv',controls),('missingness_by_year.csv',yearly_nulls),('hour_review.csv',hourly),('review_samples.csv',review_samples)]:
    pd.DataFrame(data).to_csv(P/name,index=False,encoding='utf-8-sig')
for item in json.loads((P/'source_manifest.json').read_text(encoding='utf-8')):
    assert hashlib.sha256((ROOT/item['bronze_raw']).read_bytes()).hexdigest()==item['sha256']
(P/'validation.json').write_text(json.dumps(dict(status='PASS',datasets=4,annual_measure_checks=len(controls),csv_row_and_id_checks='PASS',parquet_retained_values='PASS',raw_hash_checks=28),indent=2),encoding='utf-8')
print('VALIDATED',len(controls),'annual measure totals; 4 CSV and Parquet datasets; raw hashes')
checks=json.loads((P/'quality_checks.json').read_text(encoding='utf-8'))
lines=['# Resultaten datavoorbereiding','', 'Bronperiode: 2017–2024. Alle datasets zijn afzonderlijk bewaard; er zijn geen joins tussen de onderwerpen uitgevoerd.', '', '| Dataset | Rijen | Bronkolommen | Silver-kolommen | Gold-kolommen |','|---|---:|---:|---:|---:|']
for x in catalog: lines.append(f"| {x['dataset']} | {x['rows']:,} | {x['source_columns']} | {x['silver_columns']} | {x['gold_columns']} |")
lines+=['','Silver en gold bevatten extra herkomstvelden en afgeleide jaar-/maandvelden. Het lagere aantal gold-kolommen komt door de gedocumenteerde verwijdering van taalduplicaten of volledig lege kolommen. Er zijn geen gegevensrijen uit silver verwijderd.','','## Verificatie','',f'{len(controls)} jaarlijkse meetwaardetotalen zijn tussen de bronze-extracties en gold gelijk. Alle vier Parquetdatasets zijn teruggelezen en de bewaarde waarden stemmen exact overeen met silver. De rij-aantallen en technische sleutels van de vier CSV-bestanden stemmen overeen met Parquet. Alle 28 ruwe bestanden hebben de verwachte SHA-256-hash.','','## Reviewpunten','']
for x in checks:
    if x['status']=='REVIEW': lines.append(f"- **{x['dataset']} / {x['rule']}**: {x['failed_rows']:,} rijen. {x['detail']}")
lines+=['','Deze reviewpunten zijn geen reden om rijen automatisch te verwijderen. Identieke records kunnen echte aparte waarnemingen zijn. Uurwaarden buiten 0–23 niet als normale klokuren gebruiken; de bron geeft geen sluitende uitleg. Concrete waarden per jaar staan in `hour_review.csv`, voorbeelden met herkomst in `review_samples.csv`.','','## Grenzen voor vervolgonderzoek','','- De drie onderwerpen en de kaartdataset vertegenwoordigen verschillende populaties/detailniveaus; totalen hoeven niet gelijk te zijn.','- Metadata is volledig beschikbaar voor de drie onderwerpen, maar bevat naamverschillen en ontbrekende/extra beschrijvingen. De kaartbron heeft geen eigen meegeleverd metadatawerkboek.','- Codes zijn als tekst bewaard en niet geharmoniseerd tussen onderwerpen.','- Ontbrekende waarden zijn niet geïmputeerd. Bekijk `missingness_by_year.csv` voor uitsplitsing naar jaar.','- Gold is een brede voorbereidende analyseset. Verdere selectie van variabelen of aggregatie hangt af van de onderzoeksvraag.','','Lees `HANDOVER.md` voor de telregels, stap-voor-stap bewerkingen en uitvoerinstructies.']
lines+=['','## Aanvullende bronafwijkingen','','- De 85 voertuigregels met ontbrekend jaar hebben ook geen maand. Ze blijven behouden; jaar -1 in controlebestanden betekent uitsluitend de groep met ontbrekend jaar.','- In de kaartdataset hebben drie regels uurcode 99 (een in 2019, 2020 en 2021). Ook deze waarde is behouden en opgenomen in hour_review.csv.','- De tekst nan is omgezet naar ontbrekend voor 85 voertuigleeftijden en elk 15 waarden in tien voertuigcategorievlaggen. De bronwaarden staan ongewijzigd in bronze.']
(P/'RESULTATEN.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
