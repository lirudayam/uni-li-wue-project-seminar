# Technische Architektur

## Kontext und Problemstellung

Wir sollen die konzeptionelle Architektur in Verbindung mit der Komponentenauswahl in eine technische Architektur überführen. Dabei sind die Entscheidungen zu Komponeten basierend auf Nutzwertanalysen getroffen worden, dennoch gibt es Interpretationsspielraum, wie Komponenten interagieren sollen und Eigenentwicklungen aussehen sollen.

## Betrachtete Optionen

### Datenbeschaffung

* KPI-spezfisiche Beschaffung von Daten
* API-spezfisiche Beschaffung von Daten
* Blockchain-spezifische Beschaffung von Daten

### Datenhaltung

* Persistierung nach KPI, d.h. eigene Entitäten
* Persistierung nach API
* Kombination von gewissen KPIs, um für einen Timestamp weniger Redundanz zu haben

### Technology Stack

* ABAP CDS Views
* native HANA Tabellen
* CAP CDS

## Getroffene Entscheidungen

"API-spezfisiche Beschaffung von Daten", weil

* Error-handling vereinfacht wäre
* einfache Austauschbarkeit eines einzelnen Fetchers
* diverse KPIs von der selben API stammen dürfen, Freiheit keine Restriktion hier zu haben

"Persistierung nach KPI, d.h. eigene Entitäten", weil

* eine Zusammenführung von Daten zu einem INSERT sehr instabil wäre
* so verschiedene Joins gebaut werden können
* bewusste Inkaufnahme von einer Entwicklungsabhängigkeit des Data Warehouse von Fetchern, jedoch Laufzeitunabhängigkeit und mehr Robustheit

"CAP CDS", weil

* performanter als ABAP CDS Views
* einfacher umzusetzten, kein ABAP Stack benötigt oder HANA Client
* CAP schon mature genug ist, produktiv eingesetzt werden zu können
* weniger manueller Integrationsaufwand
* viel einfaches Datenmodell- und Servicedeployment
