"""Verify the packwiz hash chain and optionally download external dependencies."""

import argparse
import hashlib
import io
import json
from pathlib import Path
import tomllib
from urllib.parse import unquote, urlparse
from urllib.request import Request, urlopen
import zipfile


ROOT = Path(__file__).resolve().parents[1]
PAGES = "https://encraft-mc.github.io/enpack/"


def verify_hash(data, definition, description):
    algorithm = definition["hash-format"]
    if algorithm not in {"sha256", "sha512"}:
        raise ValueError(f"{description}: insecure or unsupported hash {algorithm}")
    if hashlib.new(algorithm, data).hexdigest() != definition["hash"]:
        raise ValueError(f"{description}: hash mismatch; run packwiz refresh")


def verify_pack(pack_dir, download):
    pack = tomllib.loads((pack_dir / "pack.toml").read_text("utf-8"))
    index_bytes = (pack_dir / pack["index"]["file"]).read_bytes()
    verify_hash(index_bytes, pack["index"], "index")
    index = tomllib.loads(index_bytes.decode("utf-8"))
    files = index["files"]
    paths = [entry["file"] for entry in files]
    if len(paths) != len(set(paths)):
        raise ValueError("duplicate index entries")
    actual = {path.relative_to(pack_dir).as_posix() for path in pack_dir.rglob("*.pw.toml")}
    if set(paths) != actual:
        raise ValueError("index must contain every mod metadata file exactly once")
    destinations = set()
    for entry in files:
        path = (pack_dir / entry["file"]).resolve()
        if not path.is_relative_to(pack_dir.resolve()) or not entry.get("metafile"):
            raise ValueError(f"invalid metadata path: {entry['file']}")
        raw = path.read_bytes()
        verify_hash(raw, {**entry, "hash-format": index["hash-format"]}, entry["file"])
        mod = tomllib.loads(raw.decode("utf-8"))
        if mod["side"] != "client" or mod.get("option", {}).get("optional", False):
            raise ValueError(f"{path.name}: mods must be required client dependencies")
        destination = (path.parent / mod["filename"]).resolve()
        if not destination.is_relative_to(pack_dir.resolve()) or destination in destinations:
            raise ValueError(f"invalid or duplicate destination: {mod['filename']}")
        destinations.add(destination)
        url = mod["download"]["url"]
        if urlparse(url).scheme != "https":
            raise ValueError(f"{path.name}: download must use HTTPS")
        data = None
        if url.startswith(PAGES):
            artifact = (ROOT / unquote(url.removeprefix(PAGES))).resolve()
            if not artifact.is_relative_to(ROOT):
                raise ValueError(f"{path.name}: artifact path escapes repository")
            data = artifact.read_bytes()
        elif download:
            with urlopen(Request(url, headers={"User-Agent": "Encraft-MC/enpack-check"}), timeout=60) as response:
                data = response.read()
        if data is not None:
            verify_hash(data, mod["download"], mod["filename"])
            with zipfile.ZipFile(io.BytesIO(data)) as jar:
                metadata = json.loads(jar.read("fabric.mod.json"))
                print(f"Verified {metadata['id']} {metadata['version']}: {mod['filename']}")
    print(f"Verified {pack['name']} {pack['version']}: {len(files)} required client mods")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--download", action="store_true", help="also verify external JAR downloads")
    args = parser.parse_args()
    verify_pack(ROOT / "enroyale", args.download)
