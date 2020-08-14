# Speed und Batch Layer

## Kontext und Problemstellung

Im Rahmen der Lambdaarchitekturumsetzung sollte es einen Speed-Layer geben für nahe-real-time-Daten und einen Batch Layer für Daten, die nicht zwangsläufig real-time benötigt werden. Dabei sollten verschiedene Optionen evaluiert werden.

## Betrachtete Optionen

### Kafkakonsument

* separate Kafkakonsumenten
* ein Kafkakonsument

### Datenbankzugriff

* via direktem Datenbankzugriff
* via OData-Service

### Batch-Layer-Queueing

* periodisches Einfügen generell
* periodisches Einfügen pro KPI

## Getroffene Entscheidungen

"ein Kafkakonsument", weil

* der Resourcenbedarf minimiert werden kann dadurch
* die Logik sich sehr ähnelt und daher ggf. Coderedundanz bestehen könnte
* die Anzahl an Verbindungen von und zu Kafka limitiert sein sollen auf "von"-Seite

"via OData-Service", weil

* Verwendung von $batch aus OData
* einfachere Konsumierung als CDS External Service
* kein direkter DB-Zugriff erteilt werden muss und ein Service mit restriktiven Schreib- und Leserechten verwendet werden kann

"periodisches Einfügen generell", weil

* kein KPI-spezfisiches Zeitmanagement benötigt wird
* die Anzahl an Threads kleiner bleibt
