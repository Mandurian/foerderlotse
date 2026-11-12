# Förderlotse

Findet für Privatpersonen passende Förderprogramme von Bund und EU und hilft beim Antrag.

## Was hier liegt

| Datei | Zweck |
| --- | --- |
| `index.html` | Die App, lädt `data/programme.json` |
| `manifest.webmanifest`, `sw.js`, `icons/` | Installierbare Web-App (PWA), offline nutzbar |
| `scripts/build_data.py` | Lädt die Förderdatenbank und baut `data/programme.json` |
| `.github/workflows/daten.yml` | Startet das Skript jeden Montag automatisch |
| `data/eu-privat.json` | Von Hand gepflegte EU-Programme für Privatpersonen |
| `data/antragshilfe.json` | Eigene Antragshilfe: Schritte, Unterlagen, Stolperfallen |
| `data/kurzbeschreibungen.json` | Eigene Kurzbeschreibungen je Programm, Schlüssel = Teil der Programm-URL |
| `data/programme.json` | Ergebnis: alle passenden Programme (wird erzeugt) |
| `data/meta.json` | Stand, Anzahl, Quelle (wird erzeugt) |

## Einrichten (einmalig, kostenlos)

1. Auf github.com ein neues **öffentliches** Repository `foerderlotse` anlegen. Öffentlich muss es sein, damit Actions und Pages nichts kosten.
2. Alle Dateien aus diesem Ordner hochladen („Add file“ → „Upload files“). Den Ordner `.github` mit hochladen, er ist auf manchen Rechnern versteckt.
3. **Settings → Actions → General → Workflow permissions:** „Read and write permissions“ wählen und speichern.
4. **Actions → Förderdaten aktualisieren → Run workflow** klicken. Nach ein bis zwei Minuten liegen `data/programme.json` und `data/meta.json` im Repository.
5. **Settings → Pages:** Source „Deploy from a branch“, Branch `main`, Ordner `/ (root)`. Die App ist dann unter `https://<dein-name>.github.io/foerderlotse/` erreichbar.

Danach läuft das Update jeden Montag von selbst.

## Daten und Lizenz

Die Programmdaten stammen aus der Förderdatenbank des Bundes, aufbereitet von
[CorrelAid / Civic Data Lab](https://fdb.cdl.correlaid.org/id/dataset/foerderdatenbank-programme),
Lizenz **CC BY-ND 4.0**. Die App zeigt die Texte deshalb unverändert und nennt bei jedem Programm die Quelle.
Die Dateien `eu-privat.json` und `antragshilfe.json` sind eigene Texte.

Gefiltert wird auf: Förderberechtigte `privatperson`, Fördergeber `bund` oder `eu`, noch aktiv (`absent` = false).
Mit `python scripts/build_data.py --mit-laendern` kommen Landesprogramme dazu.

## Antragshilfe pflegen

Jeder Eintrag in `data/antragshilfe.json` wird über `url_enthaelt` an Programme gehängt:
Enthält der Link des Programms einen dieser Teile (bei der Förderdatenbank der Dateiname der Seite),
bekommt das Programm diese Antragshilfe. Die `stichworte` eines Eintrags helfen der App beim Abgleich.
`meta.json` zeigt nach jedem Lauf, wie viele Programme eine Antragshilfe haben.

## Lokal testen

```
python scripts/build_data.py
```

Braucht nur Python 3, keine Zusatzpakete.

Keine Rechtsberatung. Verbindlich sind immer die Angaben des Förderträgers.
