
# Project Seminar: Data Analytics on Blockchain

## Projekt an der Uni Würzburg vom Team der Uni Liechtenstein

Jeder ab dem Focus Day geschriebene Code sollten immer zu diesem GitHub Repository gepushed werden. Es wird kein Branching-/Deployment Konzept genutzt, sondern jeglicher Code wird zu Beginn in den *master* branch deployed, so lange bis es eine stabile Version gibt.

### Programming Guidelines

Coding Guidelines sind in jedem Modul in diesem Repo eigenständig notiert und dokumentiert. Aus Gründen der Commit-History, sollte jeder Commit eine eindeutige Message haben und jeder selbst sollte commiten.

Neuste Änderungen sollten nur im dev-Branch erfolgen. Nach erfolgreichem Versionabschluss wird ein Pull-Request von dev auf den master eröffnet und nach Approval gemerged.

## Architektur

### Gesamt

![High-Level Architektur](img/Technische_Architektur.svg)

### Data Fetcher

![Data Fetcher Architektur](img/Data_Fetcher_Structure.svg)

## Repo-Struktur

- data-fetcher: alle Data-Fetchers inklusive Hilfsklassen
- dw-kafka-processor: Modul, um Kafka auszulesen und ins Data Warehouse zu schreiben
- dw-sac-middleware: Modul, um mit der SAP Analytics Cloud zu kommunizieren
- dw-aggregation-job: Modul, ob historische Daten im Data Warehouse zu aggregieren
