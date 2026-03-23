#!/usr/bin/env python3
import json
import sys
from pathlib import Path

import tomllib


def load_toml(path: Path) -> dict:
    try:
        with path.open("rb") as handle:
            return tomllib.load(handle)
    except FileNotFoundError:
        print(f"targets config not found: {path}", file=sys.stderr)
        raise
    except tomllib.TOMLDecodeError as exc:
        print(f"invalid targets config: {exc}", file=sys.stderr)
        raise


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    targets_path = root / "config" / "targets.toml"
    try:
        data = load_toml(targets_path)
    except (FileNotFoundError, tomllib.TOMLDecodeError):
        return 2

    targets = data.get("targets", [])
    include = []
    for target in targets:
        if not target.get("enabled", True):
            continue
        name = target.get("name")
        os_name = target.get("os")
        if not name or not os_name:
            print("each target must include name and os", file=sys.stderr)
            return 2
        include.append({"target": name, "os": os_name})

    if not include:
        print("no enabled targets found", file=sys.stderr)
        return 2

    print(json.dumps({"include": include}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
