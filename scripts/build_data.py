#!/usr/bin/env python3
"""Baut data/programme.json für den Förderlotsen.

Ablauf:
  1. Lädt den wöchentlichen Export der Förderdatenbank von CorrelAid (CSV).
  2. Behält nur Programme für Privatpersonen, die noch aktiv sind
     und vom Bund oder der EU kommen (mit --mit-laendern auch Landesprogramme).
  3. Hängt die eigenen Einträge aus data/eu-privat.json an.
  4. Verknüpft die eigene Antragshilfe aus data/antragshilfe.json.
  5. Schreibt data/programme.json und data/meta.json.

Lizenz der Förderdatenbank-Daten: CC BY-ND 4.0 (Quelle: CorrelAid / Civic Data Lab).
Die Programmtexte werden deshalb nicht umformuliert, nur HTML wird in Text umgewandelt.

Nur Python-Standardbibliothek, keine Installation nötig.
Aufruf:  python scripts/build_data.py            (lädt aus dem Netz)
         python scripts/build_data.py --csv x.csv (nutzt eine lokale Datei)
"""
import argparse
import csv
import html
import io
import json
import re
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

QUELLE_CSV = "https://fdb.cdl.correlaid.org/data/programme.csv"
QUELLE_INFO = "https://fdb.cdl.correlaid.org/id/dataset/foerderdatenbank-programme"
ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
MAX_BYTES = 2_000_000  # Warnschwelle für die Größe von programme.json

ART = {"zuschuss": "Zuschuss", "darlehen": "Kredit", "buergschaft": "Bürgschaft",
       "garantie": "Garantie", "beteiligung": "Beteiligung", "sonstige": "Sonstige"}
GEBER = {"bund": "Bund", "eu": "EU", "land": "Land"}

csv.field_size_limit(sys.maxsize)


def liste(zelle):
    """Zellen mit mehreren Werten sind als JSON-Array gespeichert."""
    if not zelle:
        return []
    try:
        wert = json.loads(zelle)
        return wert if isinstance(wert, list) else [wert]
    except json.JSONDecodeError:
        return [zelle]


def text(zelle):
    """HTML in einfachen Text umwandeln, Wortlaut unverändert lassen."""
    if not zelle:
        return ""
    s = re.sub(r"<\s*(br|/p|/li|/h\d)\s*/?>", "\n", zelle, flags=re.I)
    s = re.sub(r"<li[^>]*>", "• ", s, flags=re.I)
    s = re.sub(r"<[^>]+>", "", s)
    s = html.unescape(s)
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n\s*\n+", "\n", s)
    return s.strip()


def lade_csv(pfad):
    if pfad:
        return Path(pfad).read_text(encoding="utf-8")
    req = urllib.request.Request(QUELLE_CSV, headers={"User-Agent": "foerderlotse-datenpipeline"})
    with urllib.request.urlopen(req, timeout=180) as r:
        return r.read().decode("utf-8")


def filtere(zeilen, mit_laendern):
    geber_ok = {"bund", "eu"} | ({"land"} if mit_laendern else set())
    for z in zeilen:
        if z.get("absent", "").strip().lower() == "true":
            continue
        if "privatperson" not in liste(z.get("eligible_applicants")):
            continue
        geber = set(liste(z.get("funding_body")))
        if not geber & geber_ok:
            continue
        yield z


def programm(z):
    kurz = text(z.get("short_description")) or text(z.get("seo_description"))
    return {
        "id": z["id_hash"],
        "titel": text(z.get("title")),
        "kurz": kurz,
        "beschreibung": text(z.get("description")),
        "url": z["url"],
        "art": [ART.get(a, a) for a in liste(z.get("funding_type"))],
        "geber": [GEBER.get(g, g) for g in liste(z.get("funding_body"))],
        "gebiet": liste(z.get("funding_location")),
        "bereich": liste(z.get("funding_area")),
        "stichworte": liste(z.get("keywords_extracted")) or [],
        "traeger": liste(z.get("funding_organisation")),
        "unterlagen": text(z.get("required_documents")),
        "verfahren": text(z.get("procedure")),
        "fristen": text(z.get("deadlines")),
        "quelle": "fdb",
        "lizenz": z.get("license_info", "").strip(),
        "geaendert": z.get("last_updated") or None,
    }


def verknuepfe_antragshilfe(programme, hilfe):
    """Eigene Antragshilfe über den Link des Programms zuordnen.

    Jeder Eintrag in antragshilfe.json nennt in `url_enthaelt` Teile der Programm-URL
    (bei der Förderdatenbank der Dateiname, z. B. "beg-heizungsfoerderung-privat-wohngebaeude").
    Die URL ist stabiler als der Titel, der sich bei Richtlinienänderungen oft ändert.
    """
    for p in programme:
        url = p["url"].lower()
        for h in hilfe:
            if any(t.lower() in url for t in h.get("url_enthaelt", [])):
                p["antragshilfe"] = h["id"]
                break


def schluessel(titel):
    return re.sub(r"[^a-z0-9äöüß]+", "", titel.lower())


def ohne_dubletten(eigene, programme):
    """Eigene Einträge weglassen, sobald die Förderdatenbank das Programm selbst führt."""
    vorhanden = {schluessel(p["titel"]) for p in programme}
    return [e for e in eigene if schluessel(e["titel"]) not in vorhanden]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", help="lokale CSV statt Download")
    ap.add_argument("--mit-laendern", action="store_true", help="auch Landesprogramme aufnehmen")
    args = ap.parse_args()

    roh = lade_csv(args.csv)
    zeilen = list(csv.DictReader(io.StringIO(roh)))
    pflicht = {"id_hash", "url", "title", "eligible_applicants", "funding_body", "absent"}
    fehlt = pflicht - set(zeilen[0].keys() if zeilen else [])
    if fehlt:
        sys.exit(f"Fehler: Spalten fehlen im Export: {sorted(fehlt)}. Hat CorrelAid das Format geändert?")

    programme = [programm(z) for z in filtere(zeilen, args.mit_laendern)]

    eigene = json.loads((DATA / "eu-privat.json").read_text(encoding="utf-8"))
    for e in eigene:
        e.setdefault("quelle", "eigen")
        e.setdefault("beschreibung", "")
    eigene = ohne_dubletten(eigene, programme)
    programme += eigene

    hilfe = json.loads((DATA / "antragshilfe.json").read_text(encoding="utf-8"))
    verknuepfe_antragshilfe(programme, hilfe)
    programme.sort(key=lambda p: p["titel"].lower())

    ausgabe = json.dumps(programme, ensure_ascii=False, separators=(",", ":"))
    (DATA / "programme.json").write_text(ausgabe, encoding="utf-8")
    meta = {
        "stand": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "anzahl": len(programme),
        "aus_foerderdatenbank": len(programme) - len(eigene),
        "eigene_eintraege": len(eigene),
        "mit_antragshilfe": sum(1 for p in programme if "antragshilfe" in p),
        "zeilen_im_export": len(zeilen),
        "quelle": QUELLE_INFO,
        "lizenz": "CC BY-ND 4.0 (Förderdatenbank-Daten über CorrelAid / Civic Data Lab)",
    }
    (DATA / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    groesse = len(ausgabe.encode("utf-8"))
    print(f"{meta['anzahl']} Programme geschrieben ({groesse/1e6:.2f} MB), "
          f"davon {meta['mit_antragshilfe']} mit Antragshilfe. Export hatte {len(zeilen)} Zeilen.")
    if groesse > MAX_BYTES:
        print(f"Warnung: programme.json ist größer als {MAX_BYTES/1e6:.0f} MB.", file=sys.stderr)


if __name__ == "__main__":
    main()
