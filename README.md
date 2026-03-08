**中文** | [English](README.en.md)

# FFmpeg 静态库构建仓库

这个仓库用于构建固定版本的 FFmpeg 静态库，便于在 prpr/Phira 相关项目中复用（例如主仓库只需要解压到 `prpr-avc/static-lib/<target>`）。

## 功能概览

- 多 target 构建（target 采用 Rust 三元组命名）
- 按 target 定制 `./configure` 参数、编译器和优化选项
- CI 使用 matrix 构建各 target
- 产物统一打包为 `{target}.tar.gz` 并上传到 Release

## 快速开始

1. 设置版本：修改 `FFMPEG_REV`
2. 设置通用参数：修改 `config/ffmpeg.toml`
3. 配置 target：修改 `config/targets.toml`
4. 本地构建：

```bash
python3 scripts/build-ffmpeg.py <target>
```

产物生成在 `dist/<target>.tar.gz`。

## 产物结构

默认布局为单层静态库文件（`package_layout = "flat"`）：

- `libavcodec.a`
- `libavformat.a`
- `libavutil.a`
- `libswresample.a`
- `libswscale.a`

如需 `<target>/lib*.a` 结构，将 `config/ffmpeg.toml` 中的 `package_layout` 改为 `target-dir`。

部分平台（如 Windows MSVC）会产出 `.lib`。可以在 `config/targets.toml` 的对应 target 中设置 `package_libs` 覆盖默认列表。

## CI 与发布

- `config/targets.toml` 里 `enabled = true` 的 target 会进入 matrix
- 推送任意 tag 会触发构建并将 `{target}.tar.gz` 上传到 Release

## 环境要求

- Python 3.11+（用于读取 TOML 配置）
- Linux 相关 target 需要 `gcc/g++`、`make`、`pkg-config`、`nasm`、`yasm`、`libvorbis-dev`
- macOS 相关 target 需要 `brew install pkg-config libvorbis`
- macOS/iOS 相关 target 需要安装 Xcode（含 Command Line Tools），并保证 `xcrun` 可用
- iOS 相关 target 默认禁用 `libvorbis`（仅启用内置 Vorbis 解码），如需启用需自行准备 iOS 版 libvorbis 并调整配置
- iOS 相关 target 默认使用 Xcode 的 SDK 路径，如有自定义 Xcode 安装需修改 `IOS_SDK` / `IOS_SIM_SDK`
- HarmonyOS 相关 target 需要 OpenHarmony SDK，必要时通过 `OHOS_SDK` 指定路径
