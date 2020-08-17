# Grundarchitektur der Lösung

## Kontext und Problemstellung

Wir sollen im Rahmen des Projektes eine Data Analytics Lösung entwicklen, die gewisse KPIs und Regressionen auf Blockchain-Daten berechnet und Korrelationen entdecken könnte. Welche konzeptionelle Architektur würde sich dabei am besten anbieten?

## Betrachtete Optionen

### Datenbeschaffung

* direkter Zugriff auf Blockchain-Daten via Full-Nodes
* vollständige Replikation von Blockchain-Daten in eine Datenbank
* teilweise Replikation von Blockchain-Daten in eine Datenbank
* Konsumierung von spezialisierten APIs

### Datenhaltung

* einfache Datenbank
* spezielles BW
* Data Warehouse Lösung

### Visualisierung

* komplett eigene Dashboardentwicklung
* Dashboardentwicklung mithilfe eines Tools

## Getroffene Entscheidungen

"Konsumierung von spezialisierten APIs", weil

* der Aufwand entsprechene Full-Nodes laufen zu lassen zu gross wäre
* die Kosten für eine (Teil-)Replikation unverhältnismässig wären
* einige KPIs mehr als eine reine Betrachtung von Transaktionsdaten auf Blockchainebene benötigen

"einfache Datenbank", weil

* ein BW-System unnötig komplex wäre
* BW oder DW teuer sind
* eine einfache Datenbank kostengünstig und leicht zu beschaffen wäre
* Daten schon aggregiert abgelegt werden und keine Cubes etc. benötigt werden

"Dashboardentwicklung mithilfe eines Tools", weil

* der Aufwand sonst zu gross wäre
* eine Eigenentwicklung hierbei nicht mehr zeitgemäss ist

Zusätzlich war die Benutzung eines Data Streams erwünscht, weil

* Datenbeschaffung und -haltung unabhängig agieren sollen
* das eine Anforderung der Projektauftraggeber war
