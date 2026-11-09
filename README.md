# OŠ – digitalni sadržaji

Digitalni sadržaji za učenje i testove za 6., 7. i 8. razred osnovne škole.

Stranica: https://primaka1.github.io/os/

## Kako dodati novi materijal

1. Otvori mapu razreda i predmeta, npr. `7-razred/matematika/`.
2. **Add file → Upload files** i dodaj HTML datoteku.
3. Nakon 1–2 minute materijal se sam pojavi na stranici, s:
   - **temom** – pročitanom iz samog HTML-a (`<title>`, a ako ga nema, prvi `<h1>`),
   - **oznakama** – temama lekcija pročitanima iz HTML-a (npr. Potencije, Postotak, Vektori…): iz popisa lekcija u skripti i iz naslova odjeljaka (`<h2>`),
   - **datumom** kad je datoteka dodana u repozitorij.

Naziv datoteke nije bitan za prikaz.

### Ručno zadavanje teme ili oznaka (neobavezno)

Ako automatika pogodi krivo, u `<head>` HTML-a dodaj:

```html
<meta name="tema" content="Proporcionalne veličine i postoci">
<meta name="oznake" content="Potencije, Postotak, Vektori">
```

## Struktura

```
index.html                     početna stranica (razred → predmet → materijali)
_includes/kartica.html         izgled jedne kartice materijala
6-razred/, 7-razred/, 8-razred/   materijali po predmetima
.github/scripts/materijali.py  računa temu, oznake (teme lekcija) i datum
.github/workflows/stranica.yml na svaki push složi popis i objavi stranicu
```

Popis se sprema u `_data/materijali.json` samo tijekom izgradnje stranice – ne treba ga ručno uređivati.
