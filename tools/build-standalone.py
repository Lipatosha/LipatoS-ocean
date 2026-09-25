#!/usr/bin/env python3
"""Build the independent Ocean + Scenic3D module from individually tracked sources.

Source packages are committed as normal files in upstream/ocean and
upstream/scenic3d. No external downloads or runtime module dependencies.
Preserve Ocean's `ocean` id (world settings, Region behaviors and flags).
Preserve Scenic3D's `scenic3d` document flags and public game.scenic3d API.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
OCEAN = ROOT / "upstream" / "ocean"
SCENIC = ROOT / "upstream" / "scenic3d"
OUTPUT = ROOT / "dist" / "ocean"
VERSION = "2.0.0"
REQUIRED_OCEAN = [
    "scripts/ocean.mjs",
    "scripts/settings.mjs",
    "scripts/ocean-controller.mjs",
    "scripts/travel-ocean/travel-scene-controller.mjs",
    "lib/three.module.js",
    "assets/model/viking_ship/scene.gltf",
    "assets/model/caravel_ship/scene.gltf",
    "assets/model/ship_aa/scene.bin",
    "assets/sky/citrus_orchard_road_puresky_2k.hdr",
    "lang/en.json",
    "THIRD_PARTY_LICENSES.md",
]
REQUIRED_SCENIC = [
    "scripts/scenic3d.mjs",
    "lib/three.module.js",
    "lib/GLTFLoader.js",
    "lib/BufferGeometryUtils.js",
    "lang/en.json",
    "THIRD_PARTY_LICENSES.md",
]
RU_FILES = [
    "ru-runtime.mjs", "ship-strings.mjs", "ship-catalog-strings.mjs",
    "ship-family-strings.mjs", "message-strings.mjs",
]


def assert_source(root: pathlib.Path, paths: list[str], label: str) -> None:
    missing = [name for name in paths if not (root / name).is_file()]
    if missing:
        raise SystemExit(f"Неполный исходник {label}: {', '.join(missing)}")


def rewrite_text_sources(root: pathlib.Path) -> None:
    for path in root.rglob("*"):
        if path.suffix not in {".mjs", ".js", ".hbs", ".json", ".css", ".md"}:
            continue
        if path.name == "module.json":
            continue
        raw = path.read_text("utf-8")
        patched = raw.replace(
            "modules/scenic3d/", "modules/ocean/vendor/scenic3d/"
        )
        if patched != raw:
            path.write_text(patched, "utf-8")


def prepare_scenic_settings() -> None:
    """Keep scenic flags/Hooks but store its settings under the installed ocean id."""
    entry = OUTPUT / "vendor/scenic3d/scripts/scenic3d.mjs"
    source = entry.read_text("utf-8")
    needle = 'const MODULE_ID = "scenic3d";'
    if source.count(needle) != 1:
        raise SystemExit("Cannot locate Scenic3D settings namespace safely")
    adapter = """
// The 3D engine is bundled into Ocean. Keep its public API, flags and hooks
// under scenic3d, but register settings in the actually installed package.
const scenicSettings = {
  key: key => `scenic3d${String(key).charAt(0).toUpperCase()}${String(key).slice(1)}`,
  register: (key, options) => game.settings.register("ocean", scenicSettings.key(key), options),
  get: key => game.settings.get("ocean", scenicSettings.key(key)),
  set: (key, value) => game.settings.set("ocean", scenicSettings.key(key), value)
};
"""
    source = source.replace(needle, needle + adapter)
    changes = {
        "game.settings.register(MODULE_ID, ": "scenicSettings.register(",
        "game.settings?.get?.(MODULE_ID, ": "scenicSettings.get(",
        "game.settings.set(MODULE_ID, ": "scenicSettings.set(",
    }
    expected = (3, 3, 2)
    for (old, new), count in zip(changes.items(), expected):
        if source.count(old) != count:
            raise SystemExit(f"Scenic3D setting references changed: {old}: {source.count(old)} != {count}")
        source = source.replace(old, new)
    entry.write_text(source, "utf-8")


def prepare_translations() -> None:
    ru = json.loads((ROOT / "lang/ru.json").read_text("utf-8"))
    scenic_ru = json.loads((ROOT / "lang/scenic-ru.json").read_text("utf-8"))
    scenic_en = json.loads((SCENIC / "lang/en.json").read_text("utf-8"))
    scenic_cn = json.loads((SCENIC / "lang/cn.json").read_text("utf-8"))
    if set(scenic_en) != set(scenic_ru):
        raise SystemExit(
            "Missing Scenic3D translations: " + repr(sorted(set(scenic_en) - set(scenic_ru)))
        )
    ru.update(scenic_ru)
    for language, strings in (("en", scenic_en), ("cn", scenic_cn)):
        target = OUTPUT / "lang" / f"{language}.json"
        originals = json.loads(target.read_text("utf-8"))
        originals.update(strings)
        target.write_text(json.dumps(originals, ensure_ascii=False, indent=2) + "\n", "utf-8")
    (OUTPUT / "lang/ru.json").write_text(
        json.dumps(ru, ensure_ascii=False, indent=2) + "\n", "utf-8"
    )
    for name in RU_FILES:
        shutil.copy2(ROOT / "scripts" / name, OUTPUT / "scripts" / name)
    runtime = OUTPUT / "scripts/ru-runtime.mjs"
    code = runtime.read_text("utf-8")
    before = 'const MODULE_ID = "lipatos-ocean";'
    if code.count(before) != 1:
        raise SystemExit("RU runtime still assumes the separate translation add-on")
    code = code.replace(before, 'const MODULE_ID = "ocean";')
    code = code.replace(
        "'[class*=\"ship-custom\"]',",
        "'[class*=\"ship-custom\"]', '[class*=\"scenic3d-\"]',"
    )
    runtime.write_text(code, "utf-8")
    print(f"Русификация: {len(ru)} ключей (Ocean + Scenic3D), динамические окна")


def write_manifest() -> None:
    src = json.loads((OCEAN / "module.json").read_text("utf-8"))
    src["id"] = "ocean"
    src["title"] = "LipatoS — Ocean"
    src["version"] = VERSION
    src["description"] = (
        "Полноценный русскоязычный модуль воды и морских путешествий "
        "для Foundry VTT 14 со встроенным движком 3D-кораблей Scenic3D."
    )
    src["url"] = "https://github.com/Lipatosha/LipatoS-ocean"
    src["manifest"] = src["url"] + "/releases/latest/download/module.json"
    src["download"] = src["url"] + "/releases/latest/download/lipatos-ocean.zip"
    src["authors"] = [{"name": "LipatoS"}, {"name": "Reslin"}]
    src.pop("protected", None)
    src.pop("relationships", None)
    src["esmodules"] = [
        "vendor/scenic3d/scripts/scenic3d.mjs",
        "scripts/ocean.mjs",
        "scripts/ru-runtime.mjs",
    ]
    src["languages"] = [
        {"lang": "ru", "name": "Русский", "path": "lang/ru.json"},
        {"lang": "en", "name": "English", "path": "lang/en.json"},
        {"lang": "cn", "name": "简体中文", "path": "lang/cn.json"},
    ]
    (OUTPUT / "module.json").write_text(
        json.dumps(src, ensure_ascii=False, indent=2) + "\n", "utf-8"
    )


def validate() -> None:
    total = sum(p.stat().st_size for p in OUTPUT.rglob("*") if p.is_file())
    files = sum(1 for p in OUTPUT.rglob("*") if p.is_file())
    if files < 380 or total < 450_000_000:
        raise SystemExit(f"Standalone package incomplete: {files} files, {total} bytes")
    manifest = json.loads((OUTPUT / "module.json").read_text("utf-8"))
    if manifest.get("relationships", {}).get("requires"):
        raise SystemExit("Standalone package unexpectedly contains dependencies")
    if not (OUTPUT / "vendor/scenic3d/scripts/scenic3d.mjs").is_file():
        raise SystemExit("Bundled 3D engine missing")
    for scene in ("viking_ship", "caravel_ship", "dutch_ship", "pirate_ship",
                  "empty_ship", "ship_aa", "ship_b", "ship_y"):
        if not (OUTPUT / f"assets/model/{scene}/scene.gltf").is_file():
            raise SystemExit(f"Ship missing: {scene}")
    print(f"Standalone package validated: {files} files, {total / 1048576:.1f} MiB")


def build() -> None:
    assert_source(OCEAN, REQUIRED_OCEAN, "Ocean")
    assert_source(SCENIC, REQUIRED_SCENIC, "Scenic3D")
    if OUTPUT.parent.exists():
        shutil.rmtree(OUTPUT.parent)
    shutil.copytree(OCEAN, OUTPUT, ignore=shutil.ignore_patterns("signature.json"))
    shutil.copytree(
        SCENIC, OUTPUT / "vendor/scenic3d",
        ignore=shutil.ignore_patterns("module.json", "signature.json")
    )
    rewrite_text_sources(OUTPUT)
    prepare_scenic_settings()
    prepare_translations()
    write_manifest()
    validate()


if __name__ == "__main__":
    build()
