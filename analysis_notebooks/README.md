# Analyse-notebooks — Belgische verkeersveiligheid

Begin met `01_geopandas_belgie.ipynb` voor de kaarten en de coördinatencontrole. Ga daarna naar `02_analyse_presentatie.ipynb` voor trends, gewesten, tijdpatronen, weggebruikers en voertuigkenmerken. De opgeslagen notebooks bevatten de berekende uitvoer; de figuren zijn ook los te openen.

## Indeling

- `01_geopandas_belgie.ipynb`: Belgische wegenkaart, geolokalisatiedekking, 5-km-concentratiekaart en detailkaart Brussel.
- `02_analyse_presentatie.ipynb`: zes aanvullende figuren met tabellen en interpretaties.
- `figures/`: PNG en SVG voor een presentatie. PNG werkt rechtstreeks in PowerPoint; SVG blijft scherp bij vergroten.
- `tables/`: onderliggende berekeningen, bronafwijkingen en expliciete codegroeperingen.
- `PRESENTATIEVERHAAL.md`: voorgestelde slidevolgorde en spreekpunten met berekende cijfers.
- `reference_data/`: gecachte landsgrens, wegen, aanvullende Statbel-metadata en bronmanifest.
- `VALIDATIE.md`: uitvoeringsstatus en controles.

De notebooks lezen `../data/gold`. Ze wijzigen bronze, silver en gold niet. De nieuwe geografische kwaliteitscontrole is aanvullend op de eerdere pipeline; afgekeurde kaartpunten staan in `tables/geo_uitgesloten.csv` en blijven in gold behouden.

## Uitvoeren

In VS Code: open de map `group_assignment`, open een notebook en selecteer de Python-interpreter `analysis_notebooks/.venv/Scripts/python.exe`. De lokale omgeving bevat GeoPandas; algemene notebookbibliotheken worden in deze werkplek ook uit de bestaande Python-installatie gebruikt.

Uitvoering van beide notebooks vanuit PowerShell:

```powershell
& './analysis_notebooks/.venv/Scripts/python.exe' './analysis_notebooks/execute_notebooks.py'
```

De uitvoerder registreert alleen een projectlokale kernel, zet tijdelijke bestanden in `.runtime`, voert alle cellen in volgorde uit. `build_notebooks.py` is de auteurshulp: deze overschrijft notebooks en verwijdert daarbij oude outputs. Gebruik voor gewoon opnieuw rekenen uitsluitend `execute_notebooks.py`.

Op een andere computer: maak een nieuwe virtuele omgeving en installeer `requirements.txt`. Selecteer die omgeving als notebookkernel. Pas eventueel de interpreterlocatie in `execute_notebooks.py` aan bij een ander besturingssysteem. De notebooks zelf gebruiken relatieve projectpaden.

De eerste wegenverwerking is zwaarder: circa 500 MB bron-Shapefiles wordt geprojecteerd en op België uitgesneden. De GeoParquet-cache versnelt volgende runs. Alle figuren kunnen vervolgens offline worden gereproduceerd. `download_reference_data.py` haalt alleen ontbrekende openbare referentiebestanden op; het verandert de oorspronkelijke gold-datasets niet.

## Bronnen, periode en beperkingen

1. Lokale Statbel-gegevens 2017–2024 uit de eerdere voorbereiding. Tellingen volgen de bronmaten, niet zomaar het aantal rijen.
2. OpenStreetMap via Geofabrik, snapshot 1 januari 2025. De nationale figuur selecteert snelwegen en hoofd-/secundaire wegen; de detailkaart bevat ook lokale rijwegen. De cache bevat eveneens niet-gemotoriseerde paden, die niet in de detailkaart als rijweg worden getoond.
3. Eurostat/GISCO-landgrens 2024, schaal 1:1 miljoen. De grens is vereenvoudigd; daarom heeft de geografische plausibiliteitscontrole een buffer van 1 km.
4. Aanvullende Statbel-kolomuitleg is opgehaald en lokaal bewaard. Ook die metadata noemt geen expliciet coördinatenstelsel. EPSG:31370 is een gemarkeerde aanname, getoetst aan de geografische ligging. Niet gebruiken voor landmeetkundige of precieze wegsegmentanalyses zonder verdere bronbevestiging.

Geografische concentratie is geen risico per rit. Het aandeel ernstig gewonde of overleden slachtoffers is conditioneel op de geregistreerde letselpopulatie. Geen causale conclusies over infrastructuur, SUV's, weersomstandigheden of individuele weggebruikers. Wegennet en verkeersvolumes zijn niet hetzelfde. De verbetering van geolokalisatie vanaf 2022 en de afwijkende kaarttotalen worden expliciet getoond.

## Naamsvermelding bij gebruik

Behoud de bronvermelding onder de figuren:

- Statbel / Federale Politie, lokale levering 2017–2024.
- © OpenStreetMap contributors, ODbL 1.0; extract door Geofabrik, 01-01-2025. https://www.openstreetmap.org/copyright
- © EuroGeographics voor de administratieve grenzen; Eurostat/GISCO 2024. https://gisco-services.ec.europa.eu/distribution/v2/countries/

Bron-URL's en hashes staan in `reference_data/sources.json`; inputhashes en uitvoeringsdetails in `validation.json`.


## Aanvullend onderzoek

Open `03_paradoxen_en_extremen.ipynb` voor ranglijsten naar wegtype, vergelijking van ongevalsvolume met ernst, voertuigtypen bij ernstige ongevallen en een controle over de jaren. De notebook is volledig uitgevoerd; de figuren `11` tot en met `14` staan in `figures/`. De gebruikte drie GetYouStarted-notebooks uit de ACRM-map zijn als inspiratie gelezen; hun spoorweggegevens zijn niet gebruikt.

## Wegen en ongevalstypeclusters

`04_wegen_en_botsingstype_hotspots.ipynb` is volledig uitgevoerd. De figuren 15–17 en controlelijsten staan in `figures/` en `tables/`. De wegtoewijzing is benaderend (maximaal 30 meter tot OSM) en de twee typeclusters zijn signalen, geen bewezen oorzaken. Zie `PRESENTATIEVERHAAL.md` voor de exacte uitkomsten en mogelijke vervolgonderzoeken.

## Ernstverdieping

`05_ernst_verdieping.ipynb` is uitgevoerd. Het onderzoekt de ernstverdeling door de jaren, naar botsingstype, lichtomstandigheid, wegtype en locatie. Tabellen met teller en noemer staan in `tables/`; figuren 18–21 in `figures/`. De Antwerpse casus is een aanleiding voor lokaal vervolgonderzoek, geen vastgestelde oorzaak.

## Geografische heatmaps

`06_geografische_heatmaps.ipynb` bevat vier uitgevoerde GeoPandas-heatmaps op de kaart van België (2024): alle, ernstige en voetgangerongevallen, plus ernstaandeel bij voldoende observaties. Figuren 22–25 staan in `figures/`; celwaarden in `tables/heatmap_raster_2km_2024.csv` en `.parquet`.
