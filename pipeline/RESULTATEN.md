# Resultaten datavoorbereiding

Bronperiode: 2017–2024. Alle datasets zijn afzonderlijk bewaard; er zijn geen joins tussen de onderwerpen uitgevoerd.

| Dataset | Rijen | Bronkolommen | Silver-kolommen | Gold-kolommen |
|---|---:|---:|---:|---:|
| road_accidents | 288,107 | 35 | 41 | 32 |
| road_casualties | 648,681 | 43 | 49 | 37 |
| vehicle_collisions | 362,123 | 63 | 69 | 54 |
| accident_map | 289,532 | 45 | 51 | 37 |

Silver en gold bevatten extra herkomstvelden en afgeleide jaar-/maandvelden. Het lagere aantal gold-kolommen komt door de gedocumenteerde verwijdering van taalduplicaten of volledig lege kolommen. Er zijn geen gegevensrijen uit silver verwijderd.

## Verificatie

187 jaarlijkse meetwaardetotalen zijn tussen de bronze-extracties en gold gelijk. Alle vier Parquetdatasets zijn teruggelezen en de bewaarde waarden stemmen exact overeen met silver. De rij-aantallen en technische sleutels van de vier CSV-bestanden stemmen overeen met Parquet. Alle 28 ruwe bestanden hebben de verwachte SHA-256-hash.

## Reviewpunten

- **road_accidents / identical_source_rows_retained**: 1 rijen. Informational: no event ID; identical observations can represent separate events. Never automatically deduplicate.
- **road_accidents / hour_range**: 5,729 rijen. Out-of-range source values retained; review unknown hour codes.
- **road_casualties / identical_source_rows_retained**: 178 rijen. Informational: no event ID; identical observations can represent separate events. Never automatically deduplicate.
- **road_casualties / hour_range**: 4 rijen. Out-of-range source values retained; review unknown hour codes.
- **vehicle_collisions / year_range**: 85 rijen. 
- **vehicle_collisions / month_range**: 85 rijen. 
- **vehicle_collisions / identical_source_rows_retained**: 2,409 rijen. Informational: no event ID; identical observations can represent separate events. Never automatically deduplicate.
- **accident_map / identical_source_rows_retained**: 66 rijen. Informational: no event ID; identical observations can represent separate events. Never automatically deduplicate.

Deze reviewpunten zijn geen reden om rijen automatisch te verwijderen. Identieke records kunnen echte aparte waarnemingen zijn. Uurwaarden buiten 0–23 niet als normale klokuren gebruiken; de bron geeft geen sluitende uitleg. Concrete waarden per jaar staan in `hour_review.csv`, voorbeelden met herkomst in `review_samples.csv`.

## Grenzen voor vervolgonderzoek

- De drie onderwerpen en de kaartdataset vertegenwoordigen verschillende populaties/detailniveaus; totalen hoeven niet gelijk te zijn.
- Metadata is volledig beschikbaar voor de drie onderwerpen, maar bevat naamverschillen en ontbrekende/extra beschrijvingen. De kaartbron heeft geen eigen meegeleverd metadatawerkboek.
- Codes zijn als tekst bewaard en niet geharmoniseerd tussen onderwerpen.
- Ontbrekende waarden zijn niet geïmputeerd. Bekijk `missingness_by_year.csv` voor uitsplitsing naar jaar.
- Gold is een brede voorbereidende analyseset. Verdere selectie van variabelen of aggregatie hangt af van de onderzoeksvraag.

Lees `HANDOVER.md` voor de telregels, stap-voor-stap bewerkingen en uitvoerinstructies.

## Aanvullende bronafwijkingen

- De 85 voertuigregels met ontbrekend jaar hebben ook geen maand. Ze blijven behouden; jaar -1 in controlebestanden betekent uitsluitend de groep met ontbrekend jaar.
- In de kaartdataset hebben drie regels uurcode 99 (een in 2019, 2020 en 2021). Ook deze waarde is behouden en opgenomen in hour_review.csv.
- De tekst nan is omgezet naar ontbrekend voor 85 voertuigleeftijden en elk 15 waarden in tien voertuigcategorievlaggen. De bronwaarden staan ongewijzigd in bronze.
