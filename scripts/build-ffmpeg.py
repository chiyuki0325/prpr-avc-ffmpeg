#!/usr/bin/env python3
import argparse
import os
import re
import shutil
import subprocess
import tarfile
from pathlib import Path

import tomllib


def load_toml(path: Path) -> dict:
    try:
        with path.open("rb") as handle:
            return tomllib.load(handle)
    except FileNotFoundError:
        raise SystemExit(f"config not found: {path}")
    except tomllib.TOMLDecodeError as exc:
        raise SystemExit(f"invalid toml in {path}: {exc}")


def run(cmd: list[str], cwd: Path | None = None, env: dict | None = None) -> None:
    print(f"Running: {' '.join(cmd)}")
    subprocess.run(cmd, cwd=cwd, env=env, check=True)


VAR_PATTERN = re.compile(r"\$\{([^}]+)\}|\$([A-Za-z_][A-Za-z0-9_]*)")


def expand_vars(value: str, env: dict[str, str]) -> str:
    def repl(match: re.Match[str]) -> str:
        key = match.group(1) or match.group(2)
        return env.get(key, match.group(0))

    return VAR_PATTERN.sub(repl, value)


def expand_list(items: list[str], env: dict[str, str]) -> list[str]:
    return [expand_vars(item, env) for item in items]


def resolve_source_dir(root: Path, ffmpeg_cfg: dict) -> Path:
    source_dir = root / str(ffmpeg_cfg.get("source_dir", "FFmpeg"))
    if not source_dir.exists():
        raise SystemExit(
            f"FFmpeg source not found: {source_dir}. "
            "Initialize the FFmpeg submodule before building locally."
        )
    if not (source_dir / "configure").exists():
        raise SystemExit(
            f"FFmpeg source is not initialized in {source_dir}. "
            "Run `git submodule update --init FFmpeg` before building locally."
        )
    return source_dir


def prepare_source_dir(source_dir: Path, dest_dir: Path) -> Path:
    if dest_dir.exists():
        shutil.rmtree(dest_dir)
    shutil.copytree(source_dir, dest_dir, ignore=shutil.ignore_patterns(".git"))
    return dest_dir


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build FFmpeg static libs for a target"
    )
    parser.add_argument("target", help="target name defined in config/targets.toml")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    ffmpeg_cfg = load_toml(root / "config" / "ffmpeg.toml")
    targets_cfg = load_toml(root / "config" / "targets.toml")

    target_name = args.target
    target_cfg = None
    for item in targets_cfg.get("targets", []):
        if item.get("name") == target_name:
            target_cfg = item
            break
    if not target_cfg:
        available = [t.get("name") for t in targets_cfg.get("targets", [])]
        raise SystemExit(f"target not found: {target_name}. available: {available}")

    source_root = resolve_source_dir(root, ffmpeg_cfg)
    print(f"Using FFmpeg source from {source_root}")

    build_root = root / "build" / target_name
    src_dir = build_root / "src"
    source_dir = prepare_source_dir(source_root, src_dir)

    install_dir = build_root / "install"
    install_dir.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    raw_env = target_cfg.get("env") or {}
    for key, value in raw_env.items():
        env[key] = str(value)
    for key, value in raw_env.items():
        env[key] = expand_vars(str(value), env)

    common_flags = expand_list(ffmpeg_cfg.get("configure_common", []), env)
    target_flags = expand_list(target_cfg.get("configure", []), env)
    extra_flags = expand_list(target_cfg.get("extra_configure", []), env)
    configure_flags = (
        common_flags + target_flags + extra_flags + [f"--prefix={install_dir}"]
    )

    extra_cflags = expand_vars(target_cfg.get("extra_cflags", ""), env)
    extra_ldflags = expand_vars(target_cfg.get("extra_ldflags", ""), env)
    if extra_cflags:
        env["CFLAGS"] = f"{env.get('CFLAGS', '')} {extra_cflags}".strip()
    if extra_ldflags:
        env["LDFLAGS"] = f"{env.get('LDFLAGS', '')} {extra_ldflags}".strip()

    run(["./configure", *configure_flags], cwd=source_dir, env=env)

    jobs = int(ffmpeg_cfg.get("make_jobs", 0) or 0)
    if jobs <= 0:
        jobs = os.cpu_count() or 4
    run(["make", f"-j{jobs}"], cwd=source_dir, env=env)
    run(["make", "install"], cwd=source_dir, env=env)

    package_libs = target_cfg.get("package_libs") or ffmpeg_cfg.get("package_libs", [])
    if not package_libs:
        raise SystemExit("package_libs is empty")

    dist_dir = root / "dist"
    dist_dir.mkdir(parents=True, exist_ok=True)
    tar_output = dist_dir / f"{target_name}.tar.gz"
    if tar_output.exists():
        tar_output.unlink()

    layout = ffmpeg_cfg.get("package_layout", "flat")
    with tarfile.open(tar_output, "w:gz") as tar:
        for lib_name in package_libs:
            lib_path = install_dir / "lib" / lib_name
            if not lib_path.exists():
                raise SystemExit(f"missing library: {lib_path}")
            if layout == "flat":
                arcname = lib_name
            elif layout == "target-dir":
                arcname = f"{target_name}/{lib_name}"
            else:
                raise SystemExit(f"unknown package_layout: {layout}")
            tar.add(lib_path, arcname=arcname)

    print(f"Packaged {tar_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
