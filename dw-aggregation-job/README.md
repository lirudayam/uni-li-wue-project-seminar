# Aggregation Job

Ziel des Aggregation Job ist es, aus Performanz- und Ressourcengründen zeitabhängige Daten inder Vergangenheit zu aggregieren.
Dabei sind das aggregation_delay und die aggregation_interval Parameter, die definieren, ab wann eine Aggregation vorgenommen werden soll und wie granular diese vorzunehmen ist:

* aggregation_delay: gesamtsystemgeltend
* aggregation_interval: Kafka-topic-spezifisch

## Deployment

cf push

## Coding Style

* Orientierung: funktional
* Style guide: standardjs (https://github.com/standard/standard)
* Kommentierierung erfolgt funktionsweise und nach Bedarf
* Keine JavaDoc-ähnliche Kommentierung notwendig
