# Validatie

Beide notebooks zijn op 7 november 2026 volledig uitgevoerd met de projectlokale Python-kernel: 7 en 8 codecellen, zonder foutuitvoer. Alle 10 figuren zijn als PNG en SVG opgeslagen; de 10 notebookfiguren zijn ook in de uitgevoerde `.ipynb`-bestanden aanwezig. `validation.json` bevat pakketversies en hashes van de vier gold-inputs.

De Belgische wegenkaart, concentratiekaart, Brussels detailbeeld en de hoofdgrafieken zijn als afzonderlijke afbeeldingen gecontroleerd op omvang en leesbare labels. De CSV-controletabellen sluiten aan op de getoonde cijfers. De uitvoeringscode vergelijkt jaarlijkse ongevallentellingen met bronmaten en controleert de som van de kaartrastercellen.

De meegegeven drie GetYouStarted-notebooks uit `C:\Users\arthu\Documents\DS4B\DS4B_ALL_DATA\ACRM\0_Group_Assignment` zijn als inspiratie gelezen. Vooral het stapsgewijze inladen, korte controles na transformaties en GeoPandas-laagopbouw uit deel 2 en 3 zijn overgenomen. De inhoud en spoorwegdatasets uit die notebooks zijn niet gebruikt voor deze verkeersanalyse.

Een afzonderlijke HTML-weergave is niet gemaakt: in de lokale Jupyter-installatie ontbreekt het nbconvert-template `lab`. Open de uitgevoerde `.ipynb`-bestanden in Jupyter of VS Code; de figuren zijn daarnaast direct beschikbaar in `figures/`.
