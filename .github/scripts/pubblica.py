"""Crea i file della repo (index.pb, index.json, index.min.json, repo.json, apk/, jar/, icon/).

Uso: python pubblica.py <cartella keiyoushi> <cartella ramo repo> <fingerprint> <owner/nome>
"""

import gzip
import json
import shutil
import sys
from pathlib import Path

K = Path(sys.argv[1]).resolve()
OUT = Path(sys.argv[2]).resolve()
FINGERPRINT = sys.argv[3]
REPO = sys.argv[4]
BASE = f"https://raw.githubusercontent.com/{REPO}/repo"

sys.path.insert(0, str(K / ".github" / "scripts"))
import index_pb2  # noqa: E402
from google.protobuf import json_format  # noqa: E402

ICON = "res/mipmap-xhdpi/ic_launcher.png"

for d in ("apk", "jar", "icon"):
    shutil.rmtree(OUT / d, ignore_errors=True)
    (OUT / d).mkdir(parents=True)

estensioni_pb = []
estensioni_v1 = []

for info_file in sorted(K.glob("src/*/*/build/keiyoushi-source-info.json")):
    info = json.loads(info_file.read_text(encoding="utf-8"))
    build = info_file.parent
    apk = next((build / "outputs/apk/release").glob("*.apk"))
    jar = next((build / "outputs/jar/release").glob("*.jar"))
    shutil.copy2(apk, OUT / "apk" / apk.name)
    shutil.copy2(jar, OUT / "jar" / jar.name)

    pkg = info["packageName"]
    candidati = [build.parent / ICON]
    if info.get("theme"):
        candidati.append(K / "lib-multisrc" / info["theme"] / ICON)
    candidati.append(K / "core/src/main" / ICON)
    icona = next((c for c in candidati if c.exists()), None)
    if icona:
        shutil.copy2(icona, OUT / "icon" / f"{pkg}.png")

    estensioni_pb.append(index_pb2.Extension(
        name=info["name"],
        packageName=pkg,
        resources=index_pb2.Resources(
            apkUrl=f"{BASE}/apk/{apk.name}",
            jarUrl=f"{BASE}/jar/{jar.name}",
            iconUrl=f"{BASE}/icon/{pkg}.png",
        ),
        extensionLib=info["extensionLib"],
        versionCode=info["versionCode"],
        versionName=info["versionName"],
        contentWarning=info["contentWarning"],
        sources=[
            index_pb2.Source(
                id=int(s["id"]),
                name=s["name"],
                language=s["lang"],
                homeUrl=s["baseUrl"],
                mirrorUrls=s.get("mirrorUrls", []),
            )
            for s in info["sources"]
        ],
    ))

    lingue = {s["lang"] for s in info["sources"]}
    estensioni_v1.append({
        "name": f"Tachiyomi: {info['name']}",
        "pkg": pkg,
        "apk": apk.name,
        "lang": lingue.pop() if len(lingue) == 1 else "all",
        "code": info["versionCode"],
        "version": info["versionName"],
        "nsfw": 1 if info["contentWarning"] == 3 else 0,
        "sources": [
            {"name": s["name"], "lang": s["lang"], "id": str(s["id"]), "baseUrl": s["baseUrl"]}
            for s in info["sources"]
        ],
    })
    print(f"+ {info['name']} ({pkg}) {info['versionName']}")

if not estensioni_pb:
    sys.exit("::error::nessuna estensione compilata trovata")

estensioni_pb.sort(key=lambda e: e.packageName)
estensioni_v1.sort(key=lambda e: e["pkg"])

index = index_pb2.Index(
    name="La mia repo",
    badgeLabel="MIA",
    signingKey=FINGERPRINT,
    contact=index_pb2.Contact(website=f"https://github.com/{REPO}"),
    extensionList=index_pb2.ExtensionList(extensions=estensioni_pb),
)

(OUT / "index.pb").write_bytes(gzip.compress(index.SerializeToString(deterministic=True), mtime=0))
(OUT / "index.json").write_text(
    json_format.MessageToJson(index, preserving_proto_field_name=True), encoding="utf-8"
)
(OUT / "index.min.json").write_text(json.dumps(estensioni_v1, separators=(",", ":")), encoding="utf-8")
(OUT / "repo.json").write_text(json.dumps({
    "index_v2": f"{BASE}/index.pb",
    "meta": {
        "name": "La mia repo",
        "website": f"https://github.com/{REPO}",
        "signingKeyFingerprint": FINGERPRINT,
    },
}, indent=2), encoding="utf-8")
(OUT / "README.md").write_text(
    "# Ramo generato automaticamente\n\n"
    f"Link da aggiungere in Tachimanga:\n\n`{BASE}/index.pb`\n\n"
    f"(alternativa: `{BASE}/index.min.json`)\n",
    encoding="utf-8",
)
