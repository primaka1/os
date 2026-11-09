#!/usr/bin/env python3
"""Napravi _data/materijali.json: popis svih HTML materijala s temom, oznakama i datumom.

Tema se čita iz samog HTML-a (<meta name="tema">, pa <title>, pa <h1>).
Oznake su teme lekcija pročitane iz HTML-a (popis lekcija u skripti, naslovi odjeljaka),
a mogu se i ručno zadati: <meta name="oznake" content="Potencije, Vektori">.
Datum = kad je datoteka prvi put dodana u repozitorij (git povijest).
"""
import html, json, os, re, subprocess, sys
from datetime import date

PREDMETI = {"hrvatski": "Hrvatski jezik", "matematika": "Matematika", "engleski": "Engleski jezik",
            "povijest": "Povijest", "geografija": "Geografija", "biologija": "Biologija", "kemija": "Kemija",
            "fizika": "Fizika", "tehnicka": "Tehnička kultura", "informatika": "Informatika",
            "vjeronauk": "Vjeronauk", "priroda": "Priroda"}

KORIJEN = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

# Naslovi koji nisu teme lekcija (izbornici, pauze, testovi...) – ne postaju oznake
OPCENITO = re.compile(r"""(?ix)^(
    bok|bravo|mini\ pauza|pauza|po[cč]etna|izbornik|odaberi.*|kako\ u[cč]iti.*|upute.*|
    (probni\ |mje[sš]oviti\ |zavr[sš]ni\ |napredni\ )*(test|kviz|ispit).*|kviz|kartice.*|kalkulator|
    pravil[ao]|pravila\ koja.*|pravilo\ u.*|razred|\d+\ .*|rezultat.*|generalna\ proba|pitanja.*|iz\ [zž]ivota|vje[zž]ba|vo[dđ]ena\ vje[zž]ba|
    tablica.*|klikni.*|moja\ gara[zž]a|veliki\ zavr[sš]ni\ krug|teorija.*|provjeri.*|pripremi.*|
    poredaj.*|spoji.*|to[cč]no\ ili\ neto[cč]no|to[cč]no|neto[cč]no|gotovo.*|nabroji.*|ponavljanje|lekcije?|sadr[zž]aj|kraj|
    bonus|odgovori.*|razumij.*|kako\ .*|pregled.*|dopuni.*|pove[zž]i.*|primjena\ znanja|razvrstavanje.*|
    (hrvatski|matematika|engleski|povijest|geografija|biologija|kemija|fizika|informatika|vjeronauk|priroda|tehni[cč]ka)(\ \d+.*)?|
    \d+\.?\ razred|priprema.*|u[cč]enje.*|prilago[dđ]eno.*|
    \d+\.?
)$""")
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

def kratko(t):
    """'🔟 Potencije – znanstveni zapis' -> 'Potencije'"""
    t = bez_emojija(t)
    t = re.sub(r"^\d+\.\s*", "", t)
    t = re.split(r"\s+[–—-]\s+|:\s|[!?]", t)[0]
    t = re.sub(r"[^\w)]+$", "", t).strip()
    return t[:1].upper() + t[1:] if t else t

def dodaj(lista, t):
    t = kratko(t)
    if 2 < len(t) <= 45 and not OPCENITO.match(t) and t.lower() not in [x.lower() for x in lista]:
        lista.append(t)

def teme_lekcija(s, vidljivo, svi, tema):
    """Teme lekcija iz samog HTML-a: naslovi lekcija u podacima skripte i naslovi odjeljaka (h2)."""
    teme = []
    # 1) lekcije zapisane u skripti, npr. {title:'Franačka', ...}
    for x in re.findall(r"""\b(?:title|naslov|lekcija|tema|topic)\s*:\s*(?:"([^"]{3,60})"|'([^']{3,60})')""", s):
        dodaj(teme, x[0] or x[1])
    # 2) kratki ključ t:'...' – samo ako ih ima barem tri (popis lekcija)
    kratki = []
    for x in re.findall(r"""[{,]\s*t\s*:\s*(?:"([^"]{3,60})"|'([^']{3,60})')""", s):
        if re.match(r"(\d+\.\s*)?[A-ZČĆŽŠĐ]", x[0] or x[1]):
            dodaj(kratki, x[0] or x[1])
    if len(kratki) >= 3:
        for k in kratki:
            dodaj(teme, k)
    # 3) naslovi odjeljaka na stranici
    for h in svi("h2"):
        dodaj(teme, h)
    # 4) ako nema više lekcija, tema materijala je jedina lekcija
    if not teme:
        for dio in re.split(r"\s+[–—-]\s+", bez_emojija(tema)):
            dodaj(teme, dio)
    return teme[:12]

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
        oznake = teme_lekcija(s, vidljivo, svi, tema)
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
