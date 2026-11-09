#!/usr/bin/env python3
"""Dorada izgrađene stranice (_site) prije objave – izvorne datoteke se ne mijenjaju.

1. U svaki materijal ubaci gumb „← Popis” koji vodi natrag na predmet,
   i zabilježi da je materijal otvoren (kvačica ✓ na popisu).
2. Napravi ikone za dodavanje stranice na početni zaslon mobitela.
"""
import os, re, struct, sys, zlib

SITE = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else "_site")

GUMB = """
<!-- os: gumb natrag -->
<a href="{natrag}#{cilj}" id="os-natrag" aria-label="Natrag na popis materijala"
   style="position:fixed;left:12px;bottom:calc(12px + env(safe-area-inset-bottom,0px));z-index:2147483647;
   display:inline-flex;align-items:center;gap:6px;background:#1a3d8f;color:#fff;
   font:600 15px/1 system-ui,-apple-system,sans-serif;padding:11px 15px;border-radius:999px;
   text-decoration:none;box-shadow:0 2px 10px rgba(0,0,0,.3);opacity:.92">&larr; Popis</a>
<script>
try {{
  var k = "os-otvoreno", o = JSON.parse(localStorage.getItem(k) || "[]"), p = decodeURIComponent(location.pathname);
  if (o.indexOf(p) < 0) {{ o.push(p); localStorage.setItem(k, JSON.stringify(o)); }}
}} catch (e) {{}}
</script>
"""

def ubaci_gumbe():
    broj = 0
    for mapa in sorted(os.listdir(SITE)):
        m = re.fullmatch(r"(\d+)-razred", mapa)
        if not m:
            continue
        for korijen, _, datoteke in os.walk(os.path.join(SITE, mapa)):
            for d in datoteke:
                if not d.lower().endswith((".html", ".htm")):
                    continue
                put = os.path.join(korijen, d)
                rel = os.path.relpath(put, SITE).split(os.sep)
                natrag = "../" * (len(rel) - 1)
                cilj = m.group(1) + "/" + rel[1] if len(rel) > 2 else m.group(1)
                s = open(put, encoding="utf-8", errors="surrogateescape").read()
                if "os: gumb natrag" in s:
                    continue
                g = GUMB.format(natrag=natrag, cilj=cilj)
                i = s.lower().rfind("</body>")
                s = s[:i] + g + s[i:] if i >= 0 else s + g
                open(put, "w", encoding="utf-8", errors="surrogateescape").write(s)
                broj += 1
    print("Gumb natrag ubačen u", broj, "materijala")

# ---------- ikone (čisti Python, bez dodatnih paketa) ----------
def png(sirina, piksel):
    redovi = bytearray()
    for y in range(sirina):
        redovi.append(0)
        for x in range(sirina):
            redovi.extend(piksel(x, y))
    def blok(tip, podaci):
        c = struct.pack(">I", len(podaci)) + tip + podaci
        return c + struct.pack(">I", zlib.crc32(tip + podaci) & 0xFFFFFFFF)
    return (b"\x89PNG\r\n\x1a\n" + blok(b"IHDR", struct.pack(">IIBBBBB", sirina, sirina, 8, 2, 0, 0, 0))
            + blok(b"IDAT", zlib.compress(bytes(redovi), 9)) + blok(b"IEND", b""))

def u_poligonu(x, y, tocke):
    unutra = False
    j = len(tocke) - 1
    for i in range(len(tocke)):
        xi, yi = tocke[i]; xj, yj = tocke[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            unutra = not unutra
        j = i
    return unutra

LIJEVO = [(0.19, 0.30), (0.485, 0.36), (0.485, 0.75), (0.19, 0.69)]
DESNO = [(1 - x, y) for x, y in LIJEVO]
PLAVA, BIJELA, SVIJETLA = (26, 61, 143), (255, 255, 255), (214, 224, 245)

def boja(u, v):
    if u_poligonu(u, v, LIJEVO):
        return BIJELA
    if u_poligonu(u, v, DESNO):
        return SVIJETLA
    return PLAVA

def ikona(sirina):
    n = 3  # zaglađivanje rubova
    def piksel(x, y):
        z = [0, 0, 0]
        for a in range(n):
            for b in range(n):
                c = boja((x + (a + .5) / n) / sirina, (y + (b + .5) / n) / sirina)
                for i in range(3):
                    z[i] += c[i]
        return bytes(int(v / (n * n)) for v in z)
    return png(sirina, piksel)

def napravi_ikone():
    for ime, vel in (("ikona-192.png", 192), ("ikona-512.png", 512), ("apple-touch-icon.png", 180)):
        open(os.path.join(SITE, ime), "wb").write(ikona(vel))
    print("Ikone napravljene")

if __name__ == "__main__":
    ubaci_gumbe()
    napravi_ikone()
