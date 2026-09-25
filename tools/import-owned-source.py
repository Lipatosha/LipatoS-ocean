#!/usr/bin/env python3
"""One-time source import: place *unpacked individual files* into Git.

This does not create or upload archives, change module.json, or tag a release.
It copies source into upstream/ so the standalone migration can be reviewed
and built without deleting the currently installable localization release.
"""
from __future__ import annotations

import argparse
import pathlib
import zipfile

REPO = pathlib.Path(__file__).resolve().parents[1]
GITHUB_LIMIT = 100_000_000
SOURCES = {"ocean": "ocean", "scenic3d": "scenic3d"}


def import_source(archive: pathlib.Path, folder: str) -> tuple[int, int]:
    dest = REPO / "upstream" / folder
    files = 0
    total = 0
    if not archive.is_file():
        raise SystemExit(f"Не найден файл: {archive}")
    with zipfile.ZipFile(archive) as zipped:
        items = [item for item in zipped.infolist() if not item.is_dir()]
        expected = folder + "/"
        if not items or not all(item.filename.startswith(expected) for item in items):
            raise SystemExit(f"Ожидается корневая папка {expected} внутри {archive.name}")
        for item in items:
            path = pathlib.PurePosixPath(item.filename)
            relative = pathlib.PurePosixPath(*path.parts[1:])
            if ".." in relative.parts or not relative.parts:
                raise SystemExit(f"Опасный путь в исходнике: {item.filename}")
            if item.file_size >= GITHUB_LIMIT:
                raise SystemExit(f"GitHub не примет файл больше 100 МБ: {item.filename}")
            if relative.name == "signature.json":
                # Cryptographic signature of the original publisher's release
                # cannot honestly represent a modified / repackaged build.
                continue
            target = dest.joinpath(*relative.parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            with zipped.open(item, "r") as src, target.open("wb") as dst:
                while chunk := src.read(1024 * 1024):
                    dst.write(chunk)
            files += 1
            total += item.file_size
    return files, total


def main() -> None:
    parser = argparse.ArgumentParser(description="Импорт исходников Ocean/Scenic3D в Git без архивов.")
    parser.add_argument("--ocean", type=pathlib.Path, required=True)
    parser.add_argument("--scenic3d", type=pathlib.Path, required=True)
    parser.add_argument(
        "--confirm-scenic3d-rights", action="store_true",
        help="Подтверждаю право публиковать исходный код Scenic3D в этом репозитории.",
    )
    args = parser.parse_args()
    if not args.confirm_scenic3d_rights:
        parser.error(
            "Репозиторий публичный. Для публикации кода Scenic3D "
            "нужно указать --confirm-scenic3d-rights."
        )
    for name, archive in (("ocean", args.ocean), ("scenic3d", args.scenic3d)):
        count, size = import_source(archive, name)
        print(f"{name}: {count} файлов ({size / 1048576:.1f} МиБ), "
              f"путь upstream/{name}/")
    print("Готово. Содержимое распаковано отдельными файлами, архивы не добавлены.")
    print("git add upstream && git commit -m 'Import owned Ocean and Scenic3D source' && git push origin main")


if __name__ == "__main__":
    main()
