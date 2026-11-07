# Overdracht datavoorbereiding

## Doel en structuur

Deze pipeline bereidt de aangeleverde verkeersgegevens voor verdere analyse voor. Er worden geen conclusies over verkeersveiligheid berekend. De bronbestanden zijn de lokale Excelbestanden, niet een live of vernieuwde externe dataset.

Alle datalagen staan onder `group_assignment/data`:

- `bronze/raw`: ongewijzigde Excelbestanden inclusief de metadatawerkboeken; SHA-256 gecontroleerd.
- `bronze/tables/<onderwerp>`: één Parquetbestand per gegevenswerkboek. Bronwaarden worden als tekst uitgelezen; Excel-opmaak wordt uitsluitend in raw bewaard. Volledig lege rijen worden uitgesloten. Bronblad en werkelijk Excel-rijnummer blijven beschikbaar.
- `silver/<onderwerp>/<onderwerp>.parquet`: alle jaren samengevoegd, alle bronkolommen behouden, datatypes opgeschoond, technische herkomst toegevoegd.
- `gold/<onderwerp>`: slankere Nederlandstalige dataset als Parquet en UTF-8 CSV. Beide bestanden bevatten dezelfde dataset: laad er slechts één.

De onderwerpen zijn `road_accidents`, `road_casualties`, `vehicle_collisions` en aanvullend `accident_map`. Het kaartbestand stond los van de drie onderwerp-mappen en wordt afzonderlijk verwerkt. De oorspronkelijke foldernamen zijn in bronze/raw behouden.

## Bewerkingen in volgorde

1. Inventariseren en kopiëren van alle 28 bronwerkboeken naar bronze/raw; hash en bestandsgrootte registreren in `source_manifest.json`. Bestaande bronze-bestanden met een afwijkende hash blokkeren de verwerking.
2. Metadata herkennen aan het ontbreken van een bronjaar in de bestandsnaam. De daadwerkelijk gelezen uitleg wordt opgeslagen in `source_metadata.csv`; metadata wordt nooit als waarnemingen toegevoegd.
3. Excel uitlezen. Sommige werkbladen melden 1.048.576 rijen door opmaak. De echte aanwezige rijen worden gelezen, volledig lege rijen uitgesloten. `schema_changes.json` bevat de gedeclareerde omvang en het daadwerkelijke aantal gegevensrijen.
4. Jaarbestanden per onderwerp onder elkaar zetten, op kolomnaam. Toegevoegde/ontbrekende kolommen ten opzichte van het eerste jaar worden geregistreerd. Er wordt niet tussen de onderwerpen gekoppeld.
5. Omliggende witruimte verwijderen en lege tekst als ontbrekend behandelen. Codes blijven tekst, inclusief voorloopnullen. Numerieke maten en vlaggen worden getypeerd; datums worden datums. De aangetroffen tekst `nan` in 85 voertuigleeftijden wordt expliciet ontbrekend, met logvermelding en behoud in bronze. Andere onparseerbare numerieke waarden of datums stoppen de pipeline. Onbekend-codes blijven intact; geen imputatie.
6. `analysis_year` en `analysis_month` afleiden uit de brondatum of de bestaande jaar-/maandkolommen. Er wordt geen dagdatum verzonnen voor maandgegevens.
7. Gold verwijdert een Frans label alleen als de Nederlandse tegenhanger aanwezig is bij iedere gevulde Franse waarde. Volledig lege kolommen mogen ook weg. Alle overige velden blijven behouden, ook codes, maten, categorievlaggen en technische herkomst. `transformation_log.csv` geeft per verwijderde kolom de reden.
8. Validatie van rij-aantallen, technische sleutels, kalender, jaartallen tegenover bestandsnamen, negatieve maten, binaire vlaggen, slachtoffercomponenten en identieke rijen. De Parquetbestanden worden teruggelezen en exact met de voorbereide frames vergeleken.

## Betekenis en telregels

- **Road accidents:** bronregels met datum, uur, locatie en omstandigheden plus aantallen ongevallen. Gebruik `SUM(MS_ACCT)` voor het aantal ongevallen, niet zonder controle het aantal rijen. Ernstcategorieën zijn geen bewezen onderling uitsluitende categorieën en mogen niet zomaar worden opgeteld.
- **Road casualties:** bronregels met kenmerken van betrokken personen. `MS_VICT` omvat ook `MS_VIC_OK` (ongedeerden). Gebruik `MS_SLY_INJ`, `MS_SERLY_INJ` en `MS_DEAD_30_DAYS` voor de betreffende uitkomsten. Noem alle betrokkenen niet automatisch gewonden.
- **Vehicle collisions:** voertuigkenmerken bij aanrijdingen, met `FL_VEHICLE` als bronmaat voor voertuigen. Dit is geen unieke ongevalstelling. Eén ongeval kan meerdere voertuigen hebben. Voertuigleeftijd is een kenmerk, geen optelbare maat voor een totaal.
- **Accident map:** geografische bronobservaties met jaar, maand en uur. Het bestand heeft geen expliciete ongevalssleutel of tellingmaat; gebruik rijtellingen alleen als telling van kaartobservaties. Het coördinatenstelsel is niet gedocumenteerd in de aangeleverde bestanden: niet behandelen als lengte-/breedtegraden zonder verificatie.

Dit detailniveau is afgeleid van de bronkolommen en metadata; de bestanden leveren geen stabiele zakelijke primaire sleutel. `_record_id` identificeert alleen een bronregel en blijft stabiel zolang bestandsnaam en rijnummer gelijk blijven. Het is geen ongeval-ID.

Identieke bronregels worden bewust behouden: afzonderlijke gebeurtenissen kunnen dezelfde gepubliceerde kenmerken hebben. De telling in de kwaliteitstoets is een reviewpunt, geen toestemming tot deduplicatie. Er worden geen outliers verwijderd en geen ontbrekende waarden met nul gevuld.

Bij 85 voertuigregels ontbreken ook het ongevalsjaar en de maand. Die blijven ontbrekend: het bestandsjaar wordt niet stilzwijgend als ongevalsjaar ingevuld. Een groepering op jaar met standaardinstellingen kan deze rijen uitsluiten. In de **controlebestanden** staat jaar `-1` uitsluitend voor de groep met ontbrekend bronjaar; in silver/gold blijft het jaar null. Neem deze groep apart mee bij reconciliatie van totalen.

Naast de 85 voertuigleeftijden bevatten de tien voertuigcategorievlaggen elk 15 keer de tekst `nan`. Ook die waarden zijn ontbrekend gemaakt, niet nul. De exacte kolommen en aantallen staan in het transformatielog.

## Metadata en vergelijkbaarheid

`data_dictionary.csv` bevat voor elke silver-kolom het type, ontbrekende waarden, aantal verschillende waarden, gold-status en beschikbare bronuitleg. `metadata_match=alias` wijst op expliciet vastgelegde naamverschillen, bijvoorbeeld `MS_VCT` in de metadata tegenover `MS_VICT` in de data. `not_documented` betekent dat geen exacte of expliciete aliasmatch beschikbaar is; er is geen uitleg verzonnen.

De metadata benoemt de weekdaglabels ten onrechte als “Day of the month”. De originele tekst is behouden; de kalendercontrole toetst de weekdagcode aan de datum. De metadata van slachtoffers noemt ook velden die niet in de feitelijke gegevens voorkomen; die worden niet aangemaakt.

Codewaarden zijn **onderwerpgebonden**. Zo heeft wegtype niet noodzakelijk dezelfde categorie-indeling in alle datasets. Ook categorieën en gemeentegrenzen kunnen door de jaren veranderen. Niet koppelen op codes of labels zonder eerst de betekenis en periode te vergelijken. Ontbrekende provincie bij Brussel kan structureel zijn; niet automatisch imputeren.

Er is geen veilige rechtstreekse koppeling op ongevalniveau. Een join op gemeente/datum/uur kan veel-op-veel worden en tellingen vermenigvuldigen. Voor vergelijking eerst elke tabel afzonderlijk aggregeren naar een gecontroleerd gemeenschappelijk niveau en de codebetekenissen harmoniseren. Een dergelijke harmonisatie valt buiten deze voorbereidingsversie.

## Uitvoeren en onderhouden

Benodigd: Python met de versies in `requirements.txt`. Uitvoering vanuit een willekeurige werkmap:

```powershell
python "C:/Users/arthu/Documents/Vlerick/1_Courses/MDP/group_assignment/pipeline/prepare_data.py"
python "C:/Users/arthu/Documents/Vlerick/1_Courses/MDP/group_assignment/pipeline/validate_outputs.py"
```

De uitvoermap wordt afgeleid van de locatie van het script. Het script kan opnieuw uit bronze/raw draaien wanneer de oorspronkelijke bestanden naar die map zijn georganiseerd. Silver/gold en documentatie worden bij een nieuwe run vervangen; bronze/raw blijft beschermd tegen stille wijzigingen. Maak voor een toekomstige gewijzigde bronlevering een aparte versie/snapshot. Deze pipeline is afgestemd op de aangeleverde 2017–2024-bestanden; pas de jaarherkenning en controles expliciet aan bij nieuwe jaren. Onderbreking kan gedeeltelijk vernieuwde output achterlaten: alleen een run met `COMPLETE` en een bijgewerkt `run.json` als geslaagd beschouwen.

Voorkeursformaat voor analyse is Parquet, zodat codes en ontbrekende waarden hun type behouden. CSV is voor brede import beschikbaar; importeer codevelden expliciet als tekst in Excel/Power BI om voorloopnullen te bewaren. CSV is komma-gescheiden, met punt als decimaalteken.

```python
from pathlib import Path
import pandas as pd
data = Path('C:/Users/arthu/Documents/Vlerick/1_Courses/MDP/group_assignment/data')
accidents = pd.read_parquet(data/'gold/road_accidents/road_accidents.parquet')
annual = accidents.groupby('analysis_year')['MS_ACCT'].sum(min_count=1)
```

## Bestanden voor overdracht

`--resume` is uitsluitend bedoeld om een onderbroken run met ongewijzigde bronnen te hervatten. Het hergebruikt bestaande bronze-extracties en slaat al geregistreerde datasets over; gebruik dit niet na wijzigingen aan bronnen of transformatielogica. De initiële run is na de expliciete `nan`-correctie op deze manier hervat.

`organize_raw.ps1` ruimt uitsluitend oorspronkelijke kopieën op nadat bron en bronze/raw byte-identiek zijn bevonden. Hierdoor bevat data uiteindelijk alleen de drie lagen. Deze eenmalige ordening is los van de verwerking gehouden.

- `catalog.json`: aantallen, kolommen, jaren en bronpartities per dataset.
- `source_manifest.json`: broninventaris en hashes.
- `source_metadata.csv`: oorspronkelijke kolomuitleg.
- `data_dictionary.csv`: kolommen en profiel, inclusief niet-gedocumenteerde velden.
- `transformation_log.csv`: concrete normalisaties en verwijderde gold-kolommen.
- `schema_changes.json`: schema-afwijkingen en rij-aantallen per werkboek.
- `quality_checks.json`: controles met PASS/REVIEW en aantallen.
- `run.json`: voltooiingstijd, versies en hash van het uitvoerscript.
- `validation.json` en `annual_measure_reconciliation.csv`: onafhankelijke teruglees- en jaarlijkse somcontroles.
- `missingness_by_year.csv`, `hour_review.csv` en `review_samples.csv`: ontbrekende waarden en concrete reviewpunten.
- `RESULTATEN.md`: samenvatting van de daadwerkelijk uitgevoerde run en resterende reviewpunten.

Bewaar deze bestanden samen met het script. Voor toekomstige analyses moeten de reviewpunten eerst worden beoordeeld voor de specifieke onderzoeksvraag.
