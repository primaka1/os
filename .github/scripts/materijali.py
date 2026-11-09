#!/usr/bin/env python3
"""Napravi _data/materijali.json: popis svih HTML materijala s temom, oznakama i datumom.

Tema se čita iz samog HTML-a (<meta name="tema">, pa <title>, pa <h1>).
Oznake se računaju iz sadržaja HTML-a (naslovi, podnaslovi, gumbi...),
a mogu se i ručno zadati: <meta name="oznake" content="Test, Priprema">.
Datum = kad je datoteka prvi put dodana u repozitorij (git povijest).
"""
import html, json, os, re, subprocess, sys
from datetime import date

PREDMETI = {"hrvatski": "Hrvatski jezik", "matematika": "Matematika", "engleski": "Engleski jezik",
            "povijest": "Povijest", "geografija": "Geografija", "biologija": "Biologija", "kemija": "Kemija",
            "fizika": "Fizika", "tehnicka": "Tehnička kultura", "informatika": "Informatika",
            "vjeronauk": "Vjeronauk", "priroda": "Priroda"}

KORIJEN = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

# (oznaka, uzorak) – traži se u vidljivom tekstu HTML-a (bez skripti i stilova)
PRAVILA = [
    ("Test",        r"\btest\w*|\bispit"),
    ("Priprema",    r"priprem"),
    ("Kviz",        r"\bkviz"),
    ("Vježba",      r"vježb|vjezb|poredaj|\bspoji|točno ili netočno|primijeni"),
    ("Ponavljanje", r"ponavlj|ponovi|kartic|zapamti"),
    ("Lekcija",     r"lekcij|teorij|\buč[ie]|učenje|pregled|objašnjen|korak po korak"),
    ("Slušanje",    r"listen|slušaj|poslušaj"),
    ("Čitanje",     r"reading|čitanj|pročitaj"),
    ("Izlaganje",   r"izlaganj|prezentacij"),
    ("Interaktivno", r"kalkulator|grafikon|laboratorij|\blab\b|igr[aeu]|garaž"),
]

def ocisti(t):
    t = re.sub(r"<[^>]+>", " ", t)
    return re.sub(r"\s+", " ", html.unescape(t)).strip()

def bez_emojija(t):
    return re.sub(r"^[^\wČčĆćŽžŠšĐđ]+", "", t).strip()

def meta(s, ime):
    m = re.search(rf'(?is)<meta[^>]+name=["\']{ime}["\'][^>]*>', s)
    if m:
        c = re.search(r'(?is)content=["\']([^"\']*)["\']', m.group(0))
        if c and c.group(1).strip():
            return html.unescape(c.group(1)).strip()
    return None

def procitaj(putanja):
    s = open(putanja, encoding="utf-8", errors="ignore").read()
    vidljivo = re.sub(r"(?is)<(script|style|noscript)[^>]*>.*?</\1>", " ", s)
    def svi(tag):
        return [ocisti(x) for x in re.findall(rf"(?is)<{tag}[^>]*>(.*?)</{tag}>", vidljivo)]
    naslov = (svi("title") or [""])[0]
    h1 = [x for x in svi("h1") if x]
    tema = meta(s, "tema") or bez_emojija(naslov) or (bez_emojija(h1[0]) if h1 else "")
    if not tema:
        tema = os.path.splitext(os.path.basename(putanja))[0].replace("_", " ")
    podnaslov = ""
    if h1:
        r1 = set(re.findall(r"\w+", bez_emojija(h1[0]).lower()))
        rt = set(re.findall(r"\w+", tema.lower()))
        if r1 and len(r1 & rt) / len(r1) < 0.6:   # prikaži samo ako donosi nešto novo
            podnaslov = bez_emojija(h1[0])

    rucne = meta(s, "oznake")
    if rucne:
        oznake = [o.strip() for o in re.split(r"[,;]", rucne) if o.strip()]
    else:
        # 1) najvažniji dijelovi: naslov, opis, naslovi odjeljaka, gumbi
        kljucno = " ".join([naslov, meta(s, "description") or ""] + h1 + svi("h2") + svi("h3") + svi("button"))
        # 2) ako tu nema ničega, cijeli vidljivi tekst; 3) na kraju i tekst iz skripti
        oznake = []
        for tekst in (kljucno, ocisti(vidljivo), ocisti(s)):
            oznake = [ime for ime, uz in PRAVILA if re.search(uz, tekst.lower())]
            if oznake:
                break
        if not oznake:
            oznake = ["Lekcija"]
    return tema, podnaslov, oznake

def datum_dodavanja(rel):
    try:
        out = subprocess.run(["git", "log", "--diff-filter=A", "--follow", "--format=%as", "--", rel],
                             cwd=KORIJEN, capture_output=True, text=True, check=True).stdout.split()
        if out:
            return out[-1]
    except Exception:
        pass
    return date.today().isoformat()

def main():
    popis = []
    for mapa in sorted(os.listdir(KORIJEN)):
        m = re.fullmatch(r"(\d+)-razred", mapa)
        if not m:
            continue
        for korijen, _, datoteke in os.walk(os.path.join(KORIJEN, mapa)):
            for d in datoteke:
                if not d.lower().endswith((".html", ".htm")):
                    continue
                pun = os.path.join(korijen, d)
                rel = os.path.relpath(pun, KORIJEN).replace(os.sep, "/")
                dijelovi = rel.split("/")
                if len(dijelovi) < 3:
                    continue
                tema, podnaslov, oznake = procitaj(pun)
                popis.append({
                    "razred": m.group(1),
                    "predmet": dijelovi[1],
                    "predmet_naziv": PREDMETI.get(dijelovi[1], dijelovi[1].capitalize()),
                    "putanja": rel,
                    "datoteka": d,
                    "tema": tema,
                    "podnaslov": podnaslov,
                    "oznake": oznake,
                    "datum": datum_dodavanja(rel),
                })
    # ako dva materijala u istom predmetu imaju istu temu, razlikuj ih po nazivu datoteke
    from collections import Counter
    broj = Counter((x["razred"], x["predmet"], x["tema"].lower()) for x in popis)
    for x in popis:
        if broj[(x["razred"], x["predmet"], x["tema"].lower())] > 1:
            x["podnaslov"] = os.path.splitext(x["datoteka"])[0]
    popis.sort(key=lambda x: (x["datum"], x["putanja"]), reverse=True)
    os.makedirs(os.path.join(KORIJEN, "_data"), exist_ok=True)
    with open(os.path.join(KORIJEN, "_data", "materijali.json"), "w", encoding="utf-8") as f:
        json.dump(popis, f, ensure_ascii=False, indent=1)
    for x in popis:
        print(x["datum"], x["putanja"], "|", x["tema"], "|", ", ".join(x["oznake"]))

if __name__ == "__main__":
    sys.exit(main())
