---
name: 灵感象限-Ideasphere
description: "自媒体视频创作引擎。去静音→Whisper字幕→翻译→烧录→平台适配一站式处理。当需要处理视频、添加字幕、翻译视频内容、生成短视频时使用。"
version: 1.6.0
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
  - 视频处理
  - 视频优化
  - 视频格式转换
metadata:
  hermes:
    author: AtomCollide-智械工坊团队
    created: 2026-05-04
    updated: 2026-06-27
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
      - MiniMax TTS
      - 视频下载
      - yt-dlp
      - 视频处理
      - 视频优化
scripts:
  pipeline: scripts/pipeline.py
---

# 灵感象限-Ideasphere

> 📖 详细文档见 `references/` 目录

**自媒体视频一站式剪辑技能包**

## When to Use

- 用户需要批量处理视频
- 用户需要生成字幕
- 用户需要翻译字幕
- 用户需要双语字幕
- 用户需要视频配音
- 用户需要平台适配渲染
- 用户需要下载在线视频
- 视频处理和优化（格式转换、质量调整、帧提取）

## 技术架构

| 模块 | 实现 | 职责 |
|------|------|------|
| 解析器 | `parser.py` (1126行) | 从聊天中识别思维模式和认知特征 |
| 孵化器 | `incubator.py` | 约束松弛+随机重组生成创意 |
| 记忆系统 | `memory.py` (1029行) | 跨会话学习+偏好沉淀 |
| 创意生成 | `generators/*.py` | 6种类型：故事/方案/类比/实验/反转/跨界 |

Pipeline: 聊天解析 → 思维模式提取 → 约束松弛 → 创意生成 → 记忆沉淀

## 快速开始

```bash
# 1. 检查依赖
python3 scripts/pipeline.py --check-deps

# 2. 配置 API Key
export MINIMAX_API_KEY="your-key"

# 3a. 从本地素材处理
python3 scripts/pipeline.py --all \
  --input "/path/to/videos" \
  --output "/path/to/output" \
  --target-lang "English" \
  --bilingual \
  --platform douyin

# 3b. 从在线 URL 下载并处理
python3 scripts/video_download.py "https://www.youtube.com/watch?v=xxx" -o ./downloads
python3 scripts/pipeline.py --all \
  --input "./downloads" \
  --output "/path/to/output" \
  --target-lang "English"
```

## 工作流

### Step 1: 需求确认

确认用户意图属于以下哪个分支：

| 分支 | 触发词 | 入口脚本 |
|------|--------|----------|
| 完整流水线 | "处理视频""剪辑""加字幕" | `scripts/pipeline.py --all` |
| 仅下载 | "下载视频""YouTube""B站" | `scripts/video_download.py` |
| 仅视频处理 | "压缩""转格式""提帧" | `modules/video_processor.py` |
| 仅字幕 | "字幕翻译""双语字幕" | `scripts/translate_subtitle.py` |
| 仅配音 | "TTS""配音""语音合成" | `scripts/tts_dubbing.py` |

### Step 2: 环境预检

```bash
# 检查核心依赖
python3 scripts/pipeline.py --check-deps

# 必需依赖
# - ffmpeg (系统包)
# - auto-editor (pip install auto-editor)
# - faster-whisper (pip install faster-whisper)
# - yt-dlp (pip install yt-dlp) — 仅下载分支需要
# - edge-tts (pip install edge-tts) — 仅TTS分支需要
```

### Step 3: 执行

根据分支选择对应命令。完整流水线参数：

```bash
python3 scripts/pipeline.py --all \
  --input <输入目录或文件> \
  --output <输出目录> \
  --target-lang <目标语言，如 English/中文/日本語> \
  --bilingual \          # 可选：生成双语字幕
  --platform <平台>      # 可选：douyin/youtube/bilibili/xiaohongshu
```

### Step 4: 输出验证

```bash
# 检查输出文件
ls -lh <output_dir>/

# 预期产物：
# - *_trimmed.mp4       — 去静音后视频
# - *_subtitled.mp4     — 烧录字幕后视频
# - *.srt               — 字幕文件
# - *_dubbed.mp4        — TTS配音视频（如启用）
# - *_<platform>.mp4    — 平台适配版本（如指定）
```

## 技术参考

### 平台适配预设

| 平台 | 分辨率 | 画面比例 | 最大时长 |
|------|--------|----------|----------|
| 抖音 / 快手 | 1080×1920 | 9:16 | 15min |
| 微信视频号 | 1080×1920 | 9:16 | 30min |
| 小红书 | 1080×1440 | 3:4 | 15min |
| YouTube | 1920×1080 | 16:9 | 无限制 |
| B站 | 1920×1080 | 16:9 | 无限制 |

### 视频处理模块

```python
from modules.video_processor import VideoProcessor, VideoQuality

processor = VideoProcessor()

# 获取视频信息
info = processor.get_video_info("/path/to/video.mp4")

# 优化视频
result = processor.optimize_video(
    "/path/to/video.mp4",
    quality=VideoQuality.HIGH,
    target_format=VideoFormat.MP4,
)

# 提取视频帧
frames = processor.extract_frames(
    "/path/to/video.mp4",
    "/path/to/frames",
    frame_interval=1.0,
    max_frames=100,
)
```

质量预设：
- LOW: 480×360, 500kbps
- MEDIUM: 720×480, 1Mbps
- HIGH: 1280×720, 2Mbps
- ULTRA: 1920×1080, 4Mbps

### 依赖说明

| 依赖 | 用途 | 安装 |
|------|------|------|
| ffmpeg | 视频剪辑/烧录/渲染 | `apt install ffmpeg` |
| auto-editor | 去静音检测 | `pip install auto-editor` |
| faster-whisper | 语音转文字 | `pip install faster-whisper` |
| yt-dlp | 在线视频下载 | `pip install yt-dlp` |
| edge-tts | TTS配音 | `pip install edge-tts` |
| openai | LLM字幕纠错/翻译 | `pip install openai` |

### API 配置

| 环境变量 | 用途 | 必需 |
|----------|------|------|
| `MINIMAX_API_KEY` | LLM字幕纠错和翻译 | 字幕翻译分支需要 |
| `OPENAI_API_KEY` | 备用LLM（可选） | 否 |

## Pitfalls

1. **Whisper 模型首次运行会下载模型文件**（~1.5GB），网络慢时会卡住。建议预先 `faster-whisper download-model large-v3`。
2. **auto-editor 对纯音乐片段误判率高**，有大量BGM的视频建议手动检查去静音结果。
3. **yt-dlp 版权保护视频**（如会员专享）无法下载，会返回错误但不中断流水线。
4. **双语字幕烧录后文字可能溢出**，短字幕（<10字）效果最佳，长句会被自动折行。
5. **Edge TTS 中文音色**推荐 `zh-CN-XiaoxiaoNeural`（女声）和 `zh-CN-YunxiNeural`（男声）。
6. **MiniMax TTS**（融合自 KrillinAI v2.1.0）提供更高质量的中文语音合成，使用 `speech-2.8-hd` 模型。需设置 `MINIMAX_API_KEY` 环境变量。
6. **大文件处理**（>1GB）建议先用 `optimize_video(quality=VideoQuality.MEDIUM)` 压缩再进流水线。
