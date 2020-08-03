# Kafka Prozessor

Ziel des Kafka Prozessor ist es Daten aus Kafka zu konsumieren und dann via eines Streams in das Data Warehouse zu schreiben.
Dabei gibt es sowohl einen Slow Layer als auch einen Batch Layer. Wichtig ist die Verbindung zum Connectivity Service, mit welchem dann eine SOCKS5 Verbindung aufgebaut wird, welche wiederrum als Proxy für den Kafkazugriff dient.

Die csn.json Datei ist eine Metadatei resultierend aus dem srv-Modul. Dieses muss jederzeit upgedatet werden, bei jedem Rebuild vom Service.

![Gesamteinordnung des Kafkaprozessors](../img/DW_Architektur.svg)

## Deployment

cf push

## Coding Style

[![code style: prettier](https://img.shields.io/badge/code_style-prettier-ff69b4.svg?style=flat-square)](https://github.com/prettier/prettier)

* Orientierung: funktional
* Style guide: nur Prettier -> .prettierrc
* Kommentierierung erfolgt funktionsweise und nach Bedarf
* Keine JavaDoc-ähnliche Kommentierung notwendig
