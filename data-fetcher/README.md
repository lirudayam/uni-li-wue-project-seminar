# Data Fetcher

Jeder Data Fetcher hat nach NFANF xy die Aufgabe, Daten einer bestimmten Datenquelle zu konsumieren. Dabei wird zumeist ein API Call durchgeführt und das Ergebnis in Kafka geschrieben.

Grundlegend gibt es dabei mehrere relevante Klassen, wie im UML-Klassendiagramm aufgezeigt sind:

* KafkaConnector (für die Verbindung zu Kafka)
* DWConfigs (Data Warehouse Konfiguration, z.B. FetchInterval etc.)
* ErrorTypes (globale Enum für Fehlertypen)

## Packaging

Beim Packaging werden die drei zuvor erwähnten Klassen in einen tmp Ordner gepackt. Zusätzlich dazu wird die setup.py reinkopiert und mit den entsprechenden Benamungen modifiziert. Desweiteren wird der eigentliche Data Fetcher Code mit reinkopiert. Es erfolgt ein Build und eine ZIP-Komprimierung.

## Deployment

Das fertige ZIP wird via scp auf die VM kopiert, dabei sind zweifach das Passwort einzugeben pro Fetcher (einmal für scp und einmal für ssh). Danach wird automatisch in das Package navigiert und ein Task gestartet. Dieser wird benamt nach dem Ordnernamen. Laufende Prozesse sind via ps aux | grep Fetcher zu sehen.

### Deployment Script

Das deploy.sh übernimmt alle Aufgaben aus dem Packaging und Deployment. 
Funktionsweise:

./deploy.sh < FetcherName > < ... >

Beispiel:
./deploy.sh Infura CoinMarketCap

## Coding Style

* Orientierung: Objektorientiert
* Style guide: PEP8
    * Ausnahmen:
        * E402 ist akzeptabel, wenn notwendig
        * E501 ist wichtig, darf aber in Tripelquotierung oder nach Zeilenumbruch ignoriert werden
        * W605 ist ignorierbar, wenn die RegEx stimmt
        * Methoden, die statisch sein können, aber semantisch einer Klasse zuordbar sind, gehören der Klasse weiterhin an
* Kommentierierung erfolgt funktionsweise und nach Bedarf
* Keine JavaDoc-ähnliche Kommentierung notwendig