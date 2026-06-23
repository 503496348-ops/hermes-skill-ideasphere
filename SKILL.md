---
name: 灵感象限-Ideasphere
description: 灵感象限-Ideasphere：自媒体视频一站式剪辑技能包。输入本地素材或在线URL，自动完成在线视频下载→去静音剪辑→Faster Whisper语音转字幕→LLM纠错→字幕翻译(支持双语)→字幕烧录→TTS语音配音→平台适配渲染→多平台导出。支持断点续跑、阶段恢复，输出抖音/B站/YouTube-ready成品。
version: "1.3.0"
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
    updated: 2026-06-23
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
      - 视频处理
      - 视频优化
scripts:
  pipeline: scripts/pipeline.py
---

# 灵感象限-Ideasphere

**自媒体视频一站式剪辑技能包**

## When to Use

- 用户需要批量处理视频
- 用户需要生成字幕
- 用户需要翻译字幕
- 用户需要双语字幕
- 用户需要视频配音
- 用户需要平台适配渲染
- 用户需要下载在线视频
- **视频处理和优化**（NEW）

## Quick Start

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

## Video Processing (NEW)

融合自 huggingface/diffusers 的视频处理能力。

```python
from modules.video_processor import VideoProcessor, VideoQuality

processor = VideoProcessor()

# 获取视频信息
info = processor.get_video_info("/path/to/video.mp4")
print(f"分辨率: {info.width}x{info.height}")
print(f"时长: {info.duration}s")

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

# 从帧创建视频
result = processor.create_video_from_frames(
    frames,
    "/path/to/output.mp4",
    fps=30.0,
)
```

**质量预设**:
- LOW: 480x360, 500kbps
- MEDIUM: 720x480, 1Mbps
- HIGH: 1280x720, 2Mbps
- ULTRA: 1920x1080, 4Mbps
