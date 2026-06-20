---
name: 灵感象限-Ideasphere
description: 灵感象限-Ideasphere：自媒体视频一站式剪辑技能包。输入本地素材或在线URL，自动完成在线视频下载→去静音剪辑→Faster Whisper语音转字幕→LLM纠错→字幕翻译(支持双语)→字幕烧录→TTS语音配音→平台适配渲染→多平台导出。支持断点续跑、阶段恢复，输出抖音/B站/YouTube-ready成品。
version: "1.2.0"
requires_toolsets:
  - terminal
  - python
  - file
platforms:
  - local
triggers:
  - 视频剪辑流水线
  - 灵感象限
  - 批量处理视频
  - 视频去静音
  - 字幕生成
  - 字幕翻译
  - 双语字幕
  - 视频拼接
  - 口播剪辑
  - 平台适配渲染
  - TTS配音
  - 语音合成
  - 视频下载
  - 在线视频
  - YouTube下载
  - B站下载
metadata:
  hermes:
    author: AtomCollide-智械工坊团队
    created: 2026-05-04
    updated: 2026-06-19
    maturity: production
    category: media
    tags:
      - 视频剪辑
      - 字幕生成
      - 字幕翻译
      - 双语字幕
      - 批量处理
      - FFmpeg
      - Whisper
      - 灵感象限
      - 平台适配
      - TTS配音
      - Edge TTS
      - 视频下载
      - yt-dlp
scripts:
  pipeline: scripts/pipeline.py
  video_clip: scripts/video_clip.py
  video_to_text: scripts/video_to_text.py
  translate_subtitle: scripts/translate_subtitle.py
  burn_subtitle: scripts/burn_subtitle.py
  platform_render: scripts/platform_render.py
  ffmpeg_tools: scripts/ffmpeg_tools.py
  manifest: scripts/manifest.py
  video_download: scripts/video_download.py
  tts_dubbing: scripts/tts_dubbing.py
---

> **重要依赖**
> - ffmpeg + ffprobe（系统级）
> - auto-editor: `pip3 install auto-editor`
> - faster-whisper + requests: `pip3 install faster-whisper requests`
> - LLM API Key: 环境变量 `MINIMAX_API_KEY` / `OPENAI_API_KEY` / `DEEPSEEK_API_KEY` 或 `--api-key` 参数

# Video Pipeline Bundle — 灵感象限

视频一站式工作流技能包，整合剪辑、转写、翻译、烧录、渲染、拼接全流程。

**作者：AtomCollide-智械工坊团队**

## 文件结构

```
hermes-skill-ideasphere/
├── SKILL.md
├── README.md
└── scripts/
    ├── pipeline.py          # 工作流编排（含 manifest 断点续跑）
    ├── video_clip.py        # 视频剪辑（去静音）
    ├── video_to_text.py     # 语音转字幕
    ├── translate_subtitle.py # 字幕翻译（上下文感知 + 双语输出）
    ├── burn_subtitle.py     # 烧录字幕
    ├── platform_render.py   # 平台适配渲染（抖音/B站/YouTube 等）
    ├── ffmpeg_tools.py      # FFmpeg 工具箱
    └── manifest.py          # 流水线状态管理
```

## v1.2.0 更新内容

🆕 **在线视频下载** (`video_download.py`)
- 从 YouTube / B站 / TikTok / 抖音 等 1000+ 平台下载视频
- 自动下载字幕（自动生成 + 手动上传）
- 支持画质选择、代理、批量下载
- 平台自动识别 + 视频元信息获取

🆕 **TTS 语音配音** (`tts_dubbing.py`)
- Edge TTS 免费语音合成（300+ 音色，中/英/日/韩/法/德/西等）
- 语速自动对齐（TTS 时长匹配字幕时间轴）
- 配音视频生成（替换或混合原始音频）
- 支持双语字幕自动提取译文行

## v1.1.0 更新内容

🆕 **字幕翻译模块** (`translate_subtitle.py`)
- 上下文感知翻译：翻译每句时提供前后各3句作为上下文，确保语义连贯
- 支持双语字幕输出（原文+译文）
- 兼容任意 OpenAI API 规范的 LLM（MiniMax / OpenAI / DeepSeek / 通义千问）
- 翻译质量校验 + 自动重试机制
- 长句递归拆分策略

🆕 **平台适配渲染** (`platform_render.py`)
- 一键渲染适配各平台尺寸（抖音9:16 / YouTube16:9 / 小红书3:4）
- 竖屏模式自动优化字幕样式
- 横屏转竖屏智能裁剪

🆕 **流水线 Manifest** (`manifest.py`)
- 记录各阶段执行状态，支持断点续跑
- 失败阶段可单独重跑，不重复已完成的工作
- `ideasphere_manifest.json` 结构化输出

🆕 **LLM 多提供商支持**
- 统一使用 OpenAI API 规范
- 支持 MiniMax / OpenAI / DeepSeek / 通义千问等

## 依赖

- ffmpeg + ffprobe
- Python 3.8+
- auto-editor（视频剪辑）
- faster-whisper + requests（语音转写）
- LLM API Key（纠错 + 翻译）

## 安装与配置

### 1. 自动安装依赖

```bash
python3 scripts/pipeline.py --install-deps
```

**自动安装的内容：**
- `pip3 install auto-editor --break-system-packages`
- `pip3 install faster-whisper requests`

### 2. 配置 LLM API Key

**方式一：环境变量（推荐）**
```bash
export MINIMAX_API_KEY="your-api-key"
# 或
export OPENAI_API_KEY="your-api-key"
# 或
export DEEPSEEK_API_KEY="your-api-key"
```

**方式二：运行时传入**
```bash
python3 scripts/pipeline.py --all --input "/path/to/videos" --api-key "your-api-key"
```

### 3. 依赖检查

```bash
python3 scripts/pipeline.py --check-deps
```

## 核心功能

### 1. 视频剪辑 (video_clip.py)

去除视频中的静音片段，保留有效内容。

```bash
python3 scripts/video_clip.py \
  --input "/path/to/input.mp4" \
  --output "/path/to/output.mp4" \
  --threshold -40
```

### 2. 语音转写 (video_to_text.py)

用 Faster Whisper 识别语音，生成 SRT 字幕，然后用 LLM 词级别纠错。

```bash
python3 scripts/video_to_text.py \
  --input "/path/to/video.mp4" \
  --output "/path/to/subtitle.srt" \
  --model small \
  --api-key "your-api-key"
```

**参数：**
| 参数 | 说明 | 默认 |
|------|------|------|
| --model | Whisper 模型 (tiny/small/base) | small |
| --margin | 静音片段缓冲秒数 | 0.5 |
| --api-key | LLM API Key | 环境变量 |
| --provider | LLM 提供商 (minimax/openai/anthropic) | minimax |

### 3. 字幕翻译 (translate_subtitle.py) 🆕

上下文感知翻译，支持双语字幕输出。

```bash
# 翻译为英文
python3 scripts/translate_subtitle.py \
  --input "/path/to/subtitle.srt" \
  --target-lang "English" \
  --bilingual

# 翻译为中文（使用 DeepSeek）
python3 scripts/translate_subtitle.py \
  --input "/path/to/subtitle.srt" \
  --target-lang "中文" \
  --provider deepseek \
  --bilingual

# 批量翻译目录下所有 SRT
python3 scripts/translate_subtitle.py \
  --input "/path/to/subtitles/" \
  --target-lang "中文" \
  --bilingual
```

**参数：**
| 参数 | 说明 | 默认 |
|------|------|------|
| --target-lang | 目标语言 | 中文 |
| --bilingual | 生成双语字幕 | 否 |
| --provider | LLM 提供商 | minimax |
| --context-size | 上下文句子数 | 3 |

**输出文件：**
- `{name}_{lang}.srt` — 翻译后的字幕
- `{name}_bilingual_{lang}.srt` — 双语字幕（原文+译文）

### 4. 烧录字幕 (burn_subtitle.py)

将 SRT 字幕烧录进视频。

```bash
python3 scripts/burn_subtitle.py \
  --input "/path/to/video.mp4" \
  --subtitle "/path/to/subtitle.srt" \
  --output "/path/to/output.mp4"
```

### 5. 平台适配渲染 (platform_render.py) 🆕

为指定平台渲染适配尺寸的视频。

```bash
# 抖音/快手（9:16 竖屏）
python3 scripts/platform_render.py \
  --input "video.mp4" --subtitle "subtitle.srt" \
  --output "douyin_output.mp4" --platform douyin

# YouTube（16:9 横屏）
python3 scripts/platform_render.py \
  --input "video.mp4" --subtitle "subtitle.srt" \
  --output "youtube_output.mp4" --platform youtube

# 列出所有平台预设
python3 scripts/platform_render.py --list-platforms
```

**支持平台：**
| 平台 | 名称 | 尺寸 | 比例 |
|------|------|------|------|
| douyin | 抖音/快手 | 1080x1920 | 9:16 |
| wechat | 微信视频号 | 1080x1920 | 9:16 |
| xiaohongshu | 小红书 | 1080x1440 | 3:4 |
| youtube | YouTube | 1920x1080 | 16:9 |
| bilibili | B站 | 1920x1080 | 16:9 |

### 6. FFmpeg 工具箱 (ffmpeg_tools.py)

支持拼接、格式转换等操作。

```bash
# 拼接视频
python3 scripts/ffmpeg_tools.py concat \
  --inputs "1.mp4" "2.mp4" --output "merged.mp4"

# 格式转换
python3 scripts/ffmpeg_tools.py convert \
  --input "video.mov" --output "video.mp4"

# 查看视频信息
python3 scripts/ffmpeg_tools.py info --input "/path/to/videos"
```

### 7. 完整工作流 (pipeline.py)

一站式处理，支持断点续跑。

```bash
# 检查依赖
python3 scripts/pipeline.py --check-deps

# 安装依赖
python3 scripts/pipeline.py --install-deps

# 扫描目录
python3 scripts/pipeline.py --list --input "/path/to/videos"

# 执行单步
python3 scripts/pipeline.py --step 1 --input "/path/to/videos" --output "/path/to/output"

# 执行全量（含翻译）
python3 scripts/pipeline.py --all --input "/path/to/videos" --output "/path/to/output" \
  --target-lang "English" --bilingual --platform douyin

# 断点续跑（已完成的阶段自动跳过）
python3 scripts/pipeline.py --all --input "/path/to/videos" --output "/path/to/output"

# 查看流水线状态
python3 scripts/manifest.py --workdir "/path/to/output" --action summary

# 重置流水线状态
python3 scripts/manifest.py --workdir "/path/to/output" --action reset
```

## 步骤说明

| 步骤 | 功能 | 输入 | 输出 |
|------|------|------|------|
| 1 | 剪辑（去静音） | 原始视频 | 已剪辑视频 |
| 2 | 拼接 | 已剪辑视频 | 合并视频 |
| 3 | 转写（生成字幕） | 合并视频 | SRT 字幕 |
| 4 | 翻译（可选） | SRT 字幕 | 翻译字幕 + 双语字幕 |
| 5 | 烧录 | 合并视频 + 字幕 | 已烧录视频 |
| 6 | 平台渲染（可选） | 已烧录视频 | 平台适配视频 |

## 输出目录结构

```
输出目录/
├── ideasphere_manifest.json   # 流水线状态（断点续跑）
├── 1_已剪辑/                  # 步骤1产出
├── 2_已拼接/                  # 步骤2产出
├── 3_文字稿/                  # 步骤3产出（SRT + TXT）
├── 4_已翻译/                  # 步骤4产出（翻译字幕 + 双语字幕）
├── 5_已烧录/                  # 步骤5产出
└── 6_平台导出/                # 步骤6产出
    ├── douyin_xxx.mp4
    └── youtube_xxx.mp4
```

## ⚠️ 安全注意事项

### 1. 消息通知（可选，默认关闭）

脚本支持发送进度通知到 Feishu，但：
- **默认不发送消息**（`--notify false` 即可禁用）
- 如需启用，请设置 `OPENCLAW_TARGET` 环境变量为可信目标

### 2. API Key 安全

- 使用环境变量而非硬编码
- 建议使用受限权限的 API Key

## 常见问题

**Q: 提示 "auto-editor 未安装"**
A: 运行 `python3 scripts/pipeline.py --install-deps`

**Q: 提示 "MINIMAX_API_KEY 未设置"**
A: 设置环境变量 `export MINIMAX_API_KEY='your-key'`，或使用 `--api-key` 参数

**Q: 显存不够怎么办？**
A: 使用 `--model tiny` 参数，tiny 模型只需要 ~1GB 内存

**Q: ffmpeg 未安装？**
A: Ubuntu/Debian: `sudo apt install ffmpeg` | macOS: `brew install ffmpeg`

**Q: 如何断点续跑？**
A: 直接重新执行 `--all`，已完成的阶段会自动跳过（基于 `ideasphere_manifest.json`）

**Q: 如何生成双语字幕？**
A: 翻译步骤使用 `--bilingual` 参数，会同时生成单语翻译字幕和双语字幕

**Q: 竖屏视频字幕太小？**
A: 使用 `platform_render.py` 的平台预设，竖屏模式会自动放大字幕

## When to Use

- 批量处理多个口播/访谈视频，需要自动去除静音片段
- 已有本地素材，需要快速生成带字幕的成片
- 需要将视频翻译为其他语言并生成双语字幕
- 需要将视频导出为抖音/视频号/YouTube 适配格式
- 需要对字幕内容做 LLM 级别的智能纠错（过滤语气词、修正错别字）
- 多段视频需要拼接合并为一个完整成品
- 需要分步执行（先剪辑确认，再转写，再烧录）而非一键全量处理

## Pitfalls

- **FFmpeg 路径**：部分系统需要完整路径（`/usr/bin/ffmpeg`），确保 `which ffmpeg` 有输出
- **Whisper 模型大小**：`base` 模型需要 ~3GB 内存，内存不足时用 `--model small` 或 `--model tiny`
- **字幕时间戳漂移**：Whisper 在长音频中可能有时间偏移，建议音频超过 30 分钟时分段处理
- **输出路径覆盖**：默认会覆盖已有文件，先确认输出目录没有同名文件
- **auto-editor 阈值**：`--threshold` 默认 -40dB，录音环境嘈杂时可能需要调高（如 -35）
- **翻译质量**：建议使用 --bilingual 保留原文对照，翻译结果可在 SRT 文件中手动微调
- **竖屏裁剪**：横屏转竖屏时会裁剪两侧内容，确保主体居中

## Verification

```bash
# 1. 依赖检查
python3 scripts/pipeline.py --check-deps

# 2. 扫描可用素材（不执行，只列出）
python3 scripts/pipeline.py --list --input "/path/to/test/videos"

# 3. 执行完整流程测试（--notify false 关闭通知）
python3 scripts/pipeline.py --all \
  --input "/path/to/test/videos" \
  --output "/path/to/output" \
  --notify false

# 4. 检查流水线状态
python3 scripts/manifest.py --workdir "/path/to/output"

# 5. 测试字幕翻译
python3 scripts/translate_subtitle.py \
  --input "/path/to/test.srt" \
  --target-lang "English" --bilingual

# 6. 测试平台渲染
python3 scripts/platform_render.py --list-platforms
```
