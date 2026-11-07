# Presentatievoorstel — Belgische verkeersveiligheid, 2017–2024

Voorstel voor circa 12–15 minuten. De slides hieronder zijn een inhoudelijk draaiboek; er is geen PowerPointbestand aangemaakt. Gebruik de PNG- of SVG-figuren uit `figures`.

## 1. Vraag en afbakening

**Vraag:** wat leren de registraties over ontwikkeling, plaats, tijd en betrokken weggebruikers?

Vier afzonderlijke datasets: letselongevallen, betrokken personen, voertuigkenmerken en geografische registraties. Tellingen gebruiken de juiste bronmaat. De levering loopt tot 2024. Materiële-schade-ongevallen zitten niet in deze letselstatistiek. Spreek over geregistreerde letselongevallen, niet alle ongevallen op Belgische wegen.

## 2. Nationale ontwikkeling

Figuur: `05_nationale_trends.png`.

In 2024 zijn er **35.932 geregistreerde letselongevallen**, **2.999 zwaargewonden** en **469 doden binnen 30 dagen**. Ten opzichte van 2017 verandert het aantal ongevallen met **-5.5%** en het aantal verkeersdoden met **-23.0%**. Een dalende trend betekent niet dat de resterende letsellast klein is. De dip in 2020 is zichtbaar; deze analyse stelt de oorzaak niet vast.

## 3. Het Belgische wegennet als context

Figuur: `01_belgie_wegennet.png`.

De kaart toont snelwegen en hoofd-/secundaire wegen uit OpenStreetMap. De onderliggende Belgische cache bevat 1.364.891 segmenten, inclusief andere weg-/padklassen. Een segment is geen afzonderlijke weg. Dit netwerk is een contextlaag, geen maat voor gereden kilometers.

## 4. Eerst controleren: wat kunnen we op de kaart zien?

Figuur: `02_kaartdekking.png`.

De bruikbare geografische dekking gaat van **84.7% in 2017** naar **94.2% in 2024**. Statbel meldt een verbeterde geolokalisatiemethode vanaf 2022. Over alle jaren zijn er **35.881 registraties zonder coördinaten**, **2 met onmogelijke coördinaten** en **1 buiten de gebruikte landsgrensbuffer**. Geen daarvan is stilzwijgend hersteld. Meer kaartpunten is niet automatisch meer ongevallen.

## 5. Ruimtelijke concentraties

Figuur: `03_concentraties_2024.png`.

De kaart gebruikt **33.830 bruikbare locaties in 2024**. De tien 5 × 5 km-cellen met de meeste registraties bevatten **17.6%** van die locaties. Dit is een indicatie van concentratie. Zonder verkeersintensiteiten mag dit niet worden vertaald naar een rangschikking van gevaarlijkste wegen. Het kaartbestand verschilt in 2024 met -16 registraties van de algemene ongevalstelling; er is geen individuele koppeling gemaakt.

## 6. Een lokale blik

Figuur: `04_brussel_detail.png`.

Toon hoe punten zich in een stratenpatroon situeren. Dit is een rechthoekig venster rond Brussel, geen gewestvergelijking. Er is geen automatische toewijzing aan wegen en geen uitspraak over schuld of infrastructuurkwaliteit.

## 7. Volume en ernst verschillen per gewest

Figuur: `06_gewesten_volume_ernst.png`. Exacte waarden: `tables/gewesten_2024.csv`.

Het linker paneel telt ongevallen, het rechter paneel geeft het aandeel zwaargewonden en doden binnen de geregistreerde gewonden/doden. Een gewest kan een ander beeld geven op volume dan op ernst. De percentages zijn geen kans op letsel per rit of per inwoner.

## 8. Wanneer gebeuren de registraties?

Figuur: `07_weekdag_uur.png`; optioneel `10_maandpatroon.png`.

In 2024 ligt de hoogste uur-weekdagcel op **dinsdag om 17 uur**, met gemiddeld **11.40 ongevallen per betreffende kalenderdag**. De heatmap sluit 700 ongevallen met een onbruikbaar uur uit. Correctie voor aantal kalenderdagen is wel uitgevoerd; correctie voor verkeersintensiteit niet.

## 9. Wie draagt de geregistreerde letsellast?

Figuur: `08_weggebruikers.png`. Exacte waarden: `tables/weggebruikers_2024.csv`.

Vergelijk aantallen gewonden/doden met het aandeel ernstig letsel binnen dezelfde groep. In deze groepering heeft **Motorfiets** het hoogste geregistreerde ernstaandeel (**16.8%**). Dat kan samenhangen met kwetsbaarheid, omstandigheden en registratieverschillen; deze beschrijvende analyse isoleert die verklaringen niet. Laat de denominatoren in de bijbehorende tabel zien als er vragen komen.

## 10. Voertuigmix en conclusie

Figuur: `09_voertuigmix.png`.

Het SUV-aandeel in de voertuigbron stijgt van **8.3% naar 16.9%**. Dat beschrijft de betrokken voertuigpopulatie en is geen bewijs dat SUV's vaker botsen per voertuig of per kilometer. 85 voertuigen zonder bronjaar vallen buiten de jaarvergelijking.

**Afsluiting:** de datasets geven bruikbare prioriteiten voor vervolgonderzoek naar locatie, tijd en letsellast. Voor onderbouwde risicorangschikkingen ontbreken blootstellingsmaten, een gevalideerde ongeval-wegkoppeling en een model dat rekening houdt met verschillen tussen groepen. Eerst die informatie toevoegen, dan pas causale of beleidsmatige effectclaims toetsen.

## Bronvermelding en reproduceerbaarheid

Broncijfers: aangeleverde Statbel-data 2017–2024. Wegen: © OpenStreetMap contributors / Geofabrik, 01-01-2025, ODbL. Landsgrens: © EuroGeographics / Eurostat-GISCO 2024. De figuren bevatten deze bronvermeldingen; behoud ze in de presentatie.

Alle berekeningen staan in de twee uitgevoerde notebooks; ruwe bronhashes staan in `../pipeline/source_manifest.json`, geografische referentiehashes in `reference_data/sources.json`, en controle-uitkomsten in `validation.json`.

## Extra onderzoek: paradoxen en extremen

`03_paradoxen_en_extremen.ipynb` is uitgevoerd en bevat vier aanvullende figuren. In de kaartbron van 2024 hebben gemeentewegen 16.704 registraties, gewestwegen 16.368 en autosnelwegen 2.715. In de afzonderlijke slachtofferbron bedraagt het aandeel zwaargewonden of doden onder gewonden en doden respectievelijk 8,15%, 7,60% en 7,45%. Deze grootheden beantwoorden verschillende vragen. De gegevens laten geen conclusie toe over risico per gereden kilometer.

Bij betrokken voertuigtypen is het aandeel regels in een ernstige-ongevalsklasse in 2024 bijvoorbeeld 7,15% voor SUV's en 12,52% voor vrachtwagens/bussen. Dat is een conditionele verhouding binnen de voertuigbron. Een individueel ongevalsrisico per voertuigtype is hiermee niet te berekenen. De notebook bevat een jaarreeks om uitschieters op stabiliteit te controleren.

Een ranglijst van specifieke straten is bewust niet opgesteld: de kaartbron bevat geen straatnamen en een ongeval kan dicht bij meerdere wegen liggen. Daarvoor zijn gevalideerde wegtoewijzing en verkeersintensiteiten nodig. Exacte tabellen staan in `tables/wegtype_kaart_2024.csv`, `tables/wegtype_ernst_2024.csv` en `tables/voertuigtype_ernst_2024.csv`.

## Wegen en botsingstypeclusters (aanvullend onderzoek)

Het volledig uitgevoerde `04_wegen_en_botsingstype_hotspots.ipynb` maakt een voorlopige ranglijst van benoemde wegen door bruikbare kaartpunten van 2024 aan de dichtstbijzijnde OSM-rijweg binnen 30 meter toe te wijzen. Dit is een onderzoeksselectie: bij kruispunten, ventwegen en parallelle wegen kan de toewijzing onjuist zijn. Aantallen zijn geen risico per kilometer of rit.

De hoogste kandidaat in deze methode is **R1 in Antwerpen: 122 toegewezen kaartregistraties**. Daarna volgen Boomsesteenweg in Antwerpen (67) en Chaussée de Mons / Bergense Steenweg in Anderlecht (56). De volledige lijst inclusief afstand en ernstige klasse staat in `tables/kandidaat_wegen_2024.csv`; controleer de topkandidaten handmatig vóór een publieke ranglijst.

Van de gegeocodeerde kaartregistraties vallen 15.921 op gemeentewegen, 15.457 op gewestwegen en 2.438 op autosnelwegen. De corresponderende aandelen in een ernstige ongevalsklasse zijn 8,01%, 7,34% en 7,34%. Deze waarden zijn gebaseerd op dezelfde kaartbron en sluiten ongevalspunten zonder bruikbare coördinaten uit.

Bij vaste cellen van 500 × 500 meter en vergelijking met hetzelfde wegtype landelijk blijven na correctie over alle geteste typen twee opvallende typeclusters over. In één cel in **Elsene** gaat het bij 10 van 23 ongevallen op gemeentewegen om een voetganger, tegenover 12,6% op gemeentewegen landelijk (aangepaste q ≈ 0,035). De bronregels tonen 19 van de 23 buiten een kruispunt, maar dit bewijst geen oorzaak. De andere cel heeft 16 van 24 flank-/zijdelingse botsingen op een gewestweg, tegenover 32,6% op gewestwegen landelijk (q ≈ 0,047). Zie `tables/botsingstype_clusters_2024.csv` en `tables/voorbeeld_cluster_bronregels.csv`.

Vervolg: bevestig weg en locatie op een gedetailleerde kaart, bestudeer verkeersintensiteit, kruispuntontwerp, snelheden en politiegegevens. Pas daarna kan een hypothese over oorzaak worden getoetst.

## Verdieping ernst

`05_ernst_verdieping.ipynb` is volledig uitgevoerd. In de kaartbron daalt het aandeel ongevallen met doden, dodelijk gewonden of zwaargewonden van 10,45% (2017) naar 8,87% (2024). Dit gaat om het aandeel **onder geregistreerde letselongevallen**.

In 2024 hebben ongevallen met één bestuurder zonder hindernis (inclusief val) het hoogste ernstaandeel onder de grotere botsingstypen: 14,47% bij 2.288 ongevallen. Botsingen tegen een hindernis buiten de rijbaan: 13,46% bij 4.070 ongevallen. Aanrijdingen langs achteren: 5,70% bij 4.260 ongevallen. De lijst met alle typen staat in `tables/ernst_per_botsingstype_2024.csv`.

Onverlichte nacht: 14,51% ernstige ongevalsklassen bij 1.027 ongevallen, tegenover 8,55% bij 24.749 ongevallen overdag. Binnen autosnelwegen, gewestwegen en gemeentewegen blijft het aandeel bij onverlichte nacht hoger, maar dat is een samenhang en bewijst geen effect van verlichting. Zie `tables/ernst_licht_binnen_wegtype.csv` en `tables/botsingstype_mix_dag_nacht.csv`.

De 500-m-cel met de meeste ernstige ongevallen (minimaal 20 ongevallen in de cel) ligt in Antwerpen: 4 van 29 ongevallen in een ernstige klasse. Van de 29 gaat het bij 12 om een voetganger en 21 gebeurden buiten een kruispunt. De lokale bronregels staan in `tables/ernstigste_cel_bronregels_2024.csv`. Een controle ter plaatse van oversteekpunten, verkeer en snelheden is nodig voordat een oorzaak wordt genoemd.

Figuren 18–21 staan in `figures/` en in het uitgevoerde notebook.

## Belgische geografische heatmaps

`06_geografische_heatmaps.ipynb` is volledig uitgevoerd. Vier GeoPandas-heatmaps voor 2024 gebruiken dezelfde vaste 2 × 2 km-cellen: alle gegeocodeerde letselongevallen, ernstige ongevallen, ongevallen met een voetganger en het aandeel ernstige ongevallen in cellen met minimaal 20 registraties. De exacte rasterwaarden zijn beschikbaar als CSV en GeoParquet in `tables/heatmap_raster_2km_2024.*`; de figuren 22–25 staan als PNG en SVG in `figures/`.

De kaarten omvatten 33.830 bruikbare locaties. De kaart met aantallen toont concentraties van registraties; de aandeelkaart gebruikt een minimumaantal om extreme percentages door heel kleine cellen te beperken. Zonder verkeersvolumes is geen van beide een ongevalskans per rit. De geografische dekking is 94,2% van de kaartbron in 2024.
