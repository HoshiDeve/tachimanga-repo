"""Legge siti.txt e crea i moduli delle estensioni dentro il sorgente keiyoushi (cartella k/).

Uso: python genera.py <siti.txt> <cartella keiyoushi> <versionCode>
Scrive in <cartella keiyoushi>/moduli.txt la lista dei moduli Gradle da compilare.
"""

import re
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

SITI = Path(sys.argv[1])
K = Path(sys.argv[2]).resolve()
VERSION_CODE = int(sys.argv[3])
PKG_PREFIX = "repo"  # evita conflitti con le estensioni ufficiali di keiyoushi

errori: list[str] = []
moduli: list[str] = []


def slugify(nome: str) -> str:
    s = re.sub(r"[^a-z0-9]", "", nome.lower())
    if not s:
        raise ValueError(f"nome non valido: {nome!r}")
    return s if s[0].isalpha() else "s" + s


def classe_tema(tema: str) -> str:
    cartella = K / "lib-multisrc" / tema / "src"
    if not cartella.exists():
        temi = sorted(p.name for p in (K / "lib-multisrc").iterdir() if p.is_dir())
        raise ValueError(f"tema '{tema}' non esiste. Temi disponibili: {', '.join(temi)}")
    pattern = re.compile(rf"^abstract class ({re.escape(tema)})\b", re.IGNORECASE | re.MULTILINE)
    for f in cartella.rglob("*.kt"):
        m = pattern.search(f.read_text(encoding="utf-8"))
        if m:
            return m.group(1)
    raise ValueError(f"non trovo la classe principale del tema '{tema}'")


def indovina_tema(dominio: str) -> str:
    req = urllib.request.Request(dominio, headers={
        "User-Agent": "Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 Chrome/130 Mobile Safari/537.36",
    })
    try:
        html = urllib.request.urlopen(req, timeout=20).read(400_000).decode("utf-8", "ignore").lower()
    except Exception as e:  # noqa: BLE001
        raise ValueError(f"non riesco ad aprire {dominio} per riconoscere il tema ({e}). Scrivi il tema a mano.")
    if "wp-manga" in html or "madara" in html:
        return "madara"
    if "ts_reader" in html or "mangathemesia" in html or "themesia" in html:
        return "mangathemesia"
    if "pizzareader" in html:
        return "pizzareader"
    if "foolslide" in html:
        return "foolslide"
    raise ValueError(f"non riesco a riconoscere il tema di {dominio}. Scrivi il tema a mano.")


def kts_header(nome: str, pkg: str, nsfw: bool, tema: str | None, extra_version: int = 0) -> str:
    cw = "NSFW" if nsfw else "SAFE"
    tema_line = f'    theme = "{tema}"\n' if tema else ""
    return (
        "import io.github.keiyoushi.gradle.api.ContentWarning\n\n"
        "plugins {\n    alias(kei.plugins.extension)\n}\n\n"
        "keiyoushi {\n"
        f'    name = "{nome}"\n'
        f'    pkgName = "{pkg}"\n'
        f"{tema_line}"
        f"    versionCode = {VERSION_CODE + extra_version}\n"
        f"    contentWarning = ContentWarning.{cw}\n"
        '    libVersion = "1.6"\n'
    )


def crea_da_tema(nome, dominio, tema, lingua, nsfw):
    if tema == "auto":
        tema = indovina_tema(dominio)
        print(f"  tema riconosciuto: {tema}")
    classe = classe_tema(tema)
    slug = slugify(nome)
    mod = K / "src" / lingua / slug
    if mod.exists():
        shutil.rmtree(mod)
    pkg_dir = mod / "src" / "eu" / "kanade" / "tachiyomi" / "extension" / lingua / slug
    pkg_dir.mkdir(parents=True)
    nome_classe = "Sito" + slug.capitalize()
    (pkg_dir / f"{nome_classe}.kt").write_text(
        f"package eu.kanade.tachiyomi.extension.{lingua}.{slug}\n\n"
        f"import eu.kanade.tachiyomi.multisrc.{tema}.{classe}\n"
        "import keiyoushi.annotation.Source\n\n"
        "@Source\n"
        f"abstract class {nome_classe} : {classe}()\n",
        encoding="utf-8",
    )
    (mod / "build.gradle.kts").write_text(
        kts_header(nome, f"{lingua}.{PKG_PREFIX}{slug}", nsfw, tema)
        + "\n    source {\n"
        f'        lang = "{lingua}"\n'
        f'        baseUrl {{ custom("{dominio}") }}\n'
        "    }\n}\n",
        encoding="utf-8",
    )
    theme_res = K / "lib-multisrc" / tema / "res"
    if theme_res.exists():
        shutil.copytree(theme_res, mod / "res")
    return f":src:{lingua}:{slug}"


def crea_da_ext(nome, dominio, rif, nsfw_forzato):
    lingua, _, cartella = rif.partition("/")
    if not lingua or not cartella:
        raise ValueError(f"'ext:{rif}' non valido, usa il formato ext:lingua/nome (es. ext:it/mangaworld)")
    subprocess.run(["git", "-C", str(K), "sparse-checkout", "add", f"/src/{lingua}/{cartella}/"], check=True)
    mod = K / "src" / lingua / cartella
    kts = mod / "build.gradle.kts"
    if not kts.exists():
        raise ValueError(f"l'estensione keiyoushi src/{lingua}/{cartella} non esiste")
    testo = kts.read_text(encoding="utf-8")
    # nome visibile, pacchetto separato e versione sempre più alta
    testo = re.sub(r'(\n\s*)name\s*=\s*"[^"]*"', rf'\1name = "{nome}"\1pkgName = "{lingua}.{PKG_PREFIX}{cartella.lower()}"', testo, count=1)
    testo = re.sub(r"versionCode\s*=\s*(\d+)", lambda m: f"versionCode = {VERSION_CODE + int(m.group(1))}", testo, count=1)
    if nsfw_forzato:
        testo = re.sub(r"ContentWarning\.\w+", "ContentWarning.NSFW", testo, count=1)
    if dominio:
        nuovo = f'baseUrl {{ custom("{dominio}") }}'
        testo, n = re.subn(r'baseUrl\s*=\s*"[^"]*"', nuovo, testo, count=1)
        if n == 0:
            testo, n = re.subn(r"baseUrl\s*\{(?:[^{}]|\{[^{}]*\})*\}", nuovo, testo, count=1)
        if n == 0:
            raise ValueError(f"non trovo baseUrl in src/{lingua}/{cartella}/build.gradle.kts")
    kts.write_text(testo, encoding="utf-8")
    return f":src:{lingua}:{cartella}"


for numero, riga in enumerate(SITI.read_text(encoding="utf-8").splitlines(), 1):
    riga = riga.strip()
    if not riga or riga.startswith("#"):
        continue
    campi = [c.strip() for c in riga.split("|")]
    campi += [""] * (5 - len(campi))
    nome, dominio, tema, lingua, adulti = campi[:5]
    tema = (tema or "auto").lower()
    lingua = (lingua or "it").lower()
    nsfw = adulti.lower() in ("si", "sì", "yes", "18+", "x", "1", "true")
    dominio = dominio.rstrip("/")
    print(f"riga {numero}: {nome} -> {dominio} [{tema}]")
    try:
        if not nome:
            raise ValueError("manca il nome")
        if '"' in nome or "$" in nome or "\\" in nome:
            raise ValueError("il nome non può contenere \" $ o \\")
        if dominio and not re.match(r"^https?://[^\s\"$]+$", dominio):
            raise ValueError(f"dominio non valido: {dominio!r} (deve iniziare con https://)")
        if tema.startswith("ext:"):
            moduli.append(crea_da_ext(nome, dominio, tema[4:], nsfw))
        else:
            if not dominio:
                raise ValueError("manca il dominio")
            moduli.append(crea_da_tema(nome, dominio, tema, lingua, nsfw))
    except Exception as e:  # noqa: BLE001
        errori.append(f"riga {numero} ({nome}): {e}")

(K / "moduli.txt").write_text("\n".join(moduli) + "\n", encoding="utf-8")
print("\nModuli:", " ".join(moduli) or "(nessuno)")

if errori:
    print("\n::error::Alcune righe di siti.txt hanno problemi:")
    for e in errori:
        print(f"::error::{e}")
    sys.exit(1)
if not moduli:
    print("::error::siti.txt non contiene nessun sito")
    sys.exit(1)
