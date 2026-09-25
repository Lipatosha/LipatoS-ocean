#!/usr/bin/env python3
"""Reconstruct large individual source assets from raw Git blob pieces.

All source is kept in Git as normal files. Files over the per-upload limit are
stored as .part0000, .part0001 etc; this script restores the *original bytes*
before the standalone build. No archives or external downloads are involved.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
INDEX = ROOT / "upstream" / "asset-index.json"


def main() -> None:
    if not INDEX.is_file():
        raise SystemExit("Missing upstream/asset-index.json; source import incomplete")
    entries = json.loads(INDEX.read_text("utf-8"))
    restored = 0
    size_total = 0

    for item in entries:
        relative = pathlib.PurePosixPath(item["path"])
        if not relative.parts or relative.parts[0] != "upstream" or ".." in relative.parts:
            raise SystemExit(f"Unsafe source path: {relative}")
        dest = ROOT.joinpath(*relative.parts)
        size = int(item["size"])
        expected = item["sha"]
        count = int(item["parts"])
        if size < 0 or count < 1:
            raise SystemExit(f"Invalid source index entry: {relative}")
        digest = hashlib.sha1()
        digest.update(b"blob " + str(size).encode() + b"\0")

        if count == 1:
            sources = [dest]
        else:
            sources = [pathlib.Path(str(dest) + f".part{i:04d}") for i in range(count)]
        for path in sources:
            if not path.is_file():
                raise SystemExit(f"Missing source file: {path.relative_to(ROOT)}")

        actual_size = 0
        if count > 1:
            dest.parent.mkdir(parents=True, exist_ok=True)
            with dest.open("wb") as output:
                for source in sources:
                    with source.open("rb") as handle:
                        while block := handle.read(1024 * 1024):
                            output.write(block)
                            digest.update(block)
                            actual_size += len(block)
        else:
            with dest.open("rb") as handle:
                while block := handle.read(1024 * 1024):
                    digest.update(block)
                    actual_size += len(block)

        if actual_size != size or digest.hexdigest() != expected:
            if count > 1:
                dest.unlink(missing_ok=True)
            raise SystemExit(f"SHA/size mismatch: {relative}, {actual_size} B")
        if count > 1:
            for source in sources:
                source.unlink()
        restored += 1
        size_total += size

    if restored < 380 or size_total < 450_000_000:
        raise SystemExit(f"Incomplete source: {restored} files, {size_total} bytes")
    print(f"Verified source: {restored} files, {size_total / 1048576:.2f} MiB")


if __name__ == "__main__":
    main()
