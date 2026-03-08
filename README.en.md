**English** | [中文](README.md)

# FFmpeg Static Build Repo

This repository builds a pinned FFmpeg revision into static libraries for reuse in prpr/Phira-related projects (for example, the main repo can extract to `prpr-avc/static-lib/<target>`).

## Highlights

- Multi-target builds (targets use Rust-style triples)
- Per-target `./configure` flags, compiler setup, and optimizations
- CI matrix builds for each target
- Unified `{target}.tar.gz` artifacts uploaded to Release

## Quick Start

1. Set the revision in `FFMPEG_REV`
2. Adjust common options in `config/ffmpeg.toml`
3. Configure targets in `config/targets.toml`
4. Build locally:

```bash
python3 scripts/build-ffmpeg.py <target>
```

Artifacts are written to `dist/<target>.tar.gz`.

## Artifact Layout

Default layout is a flat list of static libraries (`package_layout = "flat"`):

- `libavcodec.a`
- `libavformat.a`
- `libavutil.a`
- `libswresample.a`
- `libswscale.a`

If you need `<target>/lib*.a`, set `package_layout` to `target-dir` in `config/ffmpeg.toml`.

Some platforms (for example Windows MSVC) output `.lib`. You can override the default list by setting `package_libs` per target in `config/targets.toml`.

## CI and Releases

- Only targets with `enabled = true` in `config/targets.toml` enter the matrix
- Pushing any tag triggers builds and uploads `{target}.tar.gz` to the Release

## Requirements

- Python 3.11+ (for TOML support)
- Linux targets need `gcc/g++`, `make`, `pkg-config`, `nasm`, `yasm`, `libvorbis-dev`
- macOS targets need `brew install pkg-config libvorbis`
- macOS/iOS targets require Xcode (Command Line Tools) with `xcrun` available
- iOS targets disable `libvorbis` by default (built-in Vorbis decoder only); enable it only if you provide an iOS libvorbis build
- iOS targets use Xcode SDK paths by default; update `IOS_SDK` / `IOS_SIM_SDK` if needed
- HarmonyOS targets require the OpenHarmony SDK; set `OHOS_SDK` if needed
