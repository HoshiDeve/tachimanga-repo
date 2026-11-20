# La mia repo per Tachimanga

Repo personale di estensioni, tipo keiyoushi, ma con solo i siti che scelgo io.

## Link da mettere in Tachimanga

```
https://raw.githubusercontent.com/HoshiDeve/tachimanga-repo/repo/index.pb
```

In Tachimanga: **Impostazioni → Sfoglia (Browse) → Repository estensioni → +** e incolla il link.
(Se non lo accetta, prova `.../repo/index.min.json`.)

## Aggiungere o cambiare un sito

1. Apri [`siti.txt`](siti.txt) su GitHub e premi la matita ✏️ (funziona anche da telefono).
2. Aggiungi una riga:  `Nome | https://dominio.com | auto`
3. Premi **Commit changes**.
4. Aspetta 3-5 minuti (scheda **Actions**: pallino verde = fatto).
5. In Tachimanga, nelle estensioni, aggiorna: compare il sito nuovo / l'aggiornamento.

Se un sito cambia solo dominio puoi anche cambiarlo direttamente dentro Tachimanga:
impostazioni dell'estensione → *Custom base URL*.

## Temi

Il tema è il "motore" del sito. `auto` riconosce da solo Madara, MangaThemesia, PizzaReader e FoolSlide.
Altri temi disponibili (presi da keiyoushi): madara, mangathemesia, pizzareader, foolslide,
mangareader, zeistmanga, heancms, keyoapp, wpcomics, iken, mmrcms, fmreader, mangabox, ...
L'elenco completo è in <https://github.com/keiyoushi/extensions-source/tree/main/lib-multisrc>.

Per un sito che keiyoushi ha già (con codice suo), usa `ext:lingua/nome`, es. `ext:it/mangaworld`:
prende quell'estensione e ci mette il tuo dominio. I nomi sono in
<https://github.com/keiyoushi/extensions-source/tree/main/src>.

## Come funziona

Ad ogni modifica di `siti.txt`, GitHub Actions scarica i temi aggiornati da keiyoushi, crea
un'estensione per ogni riga, la firma con la chiave della repo (salvata nei *Secrets*) e pubblica
tutto sul ramo `repo`. Le estensioni hanno un pacchetto diverso da quelle di keiyoushi, quindi
puoi tenere installate entrambe le repo (se però dai a un sito lo stesso nome che ha su keiyoushi, installalo da una sola delle due).

## Correzioni ai temi (`override/`)

I file dentro `override/` sostituiscono quelli di keiyoushi prima della compilazione.
Ora c'è `override/lib-multisrc/mangaworld/`: il tema MangaWorld aggiornato alla nuova grafica
del sito (novembre 2026), perché la versione di keiyoushi non trova più nulla.
