# 灵感象限-Ideasphere

**自媒体视频一站式剪辑技能包**

> **版本**：v1.2.0
> **作者**：AtomCollide-智械工坊团队
> **最后更新**：2026-06-20

---

## 概览

灵感象限是 Hermes Agent 的视频编辑技能包，输入本地素材或在线 URL，自动完成完整的视频处理流水线。

```
在线下载(可选) → 去静音剪辑 → 语音转字幕 → LLM纠错 → 字幕翻译 → 双语字幕 → 字幕烧录 → TTS配音 → 平台适配渲染 → 多平台导出
```

**参考 KrillinAI（10.3K⭐）的优秀设计，实现了：**
- 🌐 在线视频下载（YouTube/B站/TikTok/抖音 等 1000+ 平台）
- 🎙️ TTS 语音配音（Edge TTS 300+ 免费音色，支持语速自动对齐）
- 🌍 上下文感知字幕翻译（翻译时提供前后3句上下文）
- 📝 双语字幕输出（原文+译文）
- 📱 平台适配渲染（抖音9:16 / YouTube16:9 / 小红书3:4）
- 🔄 流水线 Manifest 断点续跑
- 🤖 OpenAI API 规范兼容（MiniMax / OpenAI / DeepSeek / 通义千问）

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

# 3c. 生成配音视频
python3 scripts/tts_dubbing.py --srt translated.srt --video original.mp4 --output ./tts_output
```

## 核心流程

| 步骤 | 功能 | 工具 |
|------|------|------|
| 0 | 在线视频下载（可选） | yt-dlp |
| 1 | 去静音剪辑 | auto-editor |
| 2 | 视频拼接 | ffmpeg |
| 3 | 语音转字幕 | Faster Whisper + LLM 纠错 |
| 4 | 字幕翻译（可选） | LLM 上下文感知翻译 |
| 5 | 字幕烧录 | ffmpeg |
| 6 | TTS 配音（可选） | Edge TTS / OpenAI TTS |
| 7 | 平台适配渲染（可选） | ffmpeg + 平台预设 |

## 新增功能 (v1.2.0)

### 🎙️ TTS 语音配音 (`tts_dubbing.py`)

将翻译后的字幕合成为自然语音，支持配音视频生成。

```bash
# Edge TTS 合成（免费，300+ 音色）
python3 scripts/tts_dubbing.py --srt translated.srt --output ./tts_output

# 指定中文男声
python3 scripts/tts_dubbing.py --srt translated.srt --voice zh-CN-YunxiNeural --output ./tts_output

# 生成配音视频（替换原始音频）
python3 scripts/tts_dubbing.py --srt translated.srt --video original.mp4 --output ./tts_output

# 混合模式（保留原始音频作为背景音）
python3 scripts/tts_dubbing.py --srt translated.srt --video original.mp4 --output ./tts_output --mix-original

# 列出可用音色
python3 scripts/tts_dubbing.py --list-voices --lang zh

# 安装依赖
python3 scripts/tts_dubbing.py --install-deps
```

**特性：**
- Edge TTS：免费，支持中/英/日/韩/法/德/西/葡/俄/阿拉伯等语言
- 语速自动对齐：TTS 时长自动匹配字幕时间轴
- 双语字幕支持：自动提取译文行进行合成
- 配音视频生成：替换或混合原始音频轨

### 🌐 在线视频下载 (`video_download.py`)

从 1000+ 平台下载视频和字幕，支持代理和批量下载。

```bash
# 下载 YouTube 视频（含字幕）
python3 scripts/video_download.py "https://www.youtube.com/watch?v=xxx" -o ./downloads

# 下载 B站视频
python3 scripts/video_download.py "https://www.bilibili.com/video/BVxxx" -o ./downloads

# 指定画质
python3 scripts/video_download.py "https://..." -o ./downloads --max-height 720

# 仅下载字幕
python3 scripts/video_download.py "https://..." -o ./downloads --subs-only

# 使用代理
python3 scripts/video_download.py "https://..." -o ./downloads --proxy "http://127.0.0.1:7890"

# 批量下载
python3 scripts/video_download.py --batch urls.txt -o ./downloads

# 获取视频信息（不下载）
python3 scripts/video_download.py "https://..." --info

# 安装依赖
python3 scripts/video_download.py --install-deps
```

**支持平台：**
YouTube / B站 / TikTok / 抖音 / Twitter / Instagram / 微博 / 小红书 / 快手 等 1000+ 平台

## 支持的平台导出

| 平台 | 尺寸 | 比例 |
|------|------|------|
| 抖音/快手 | 1080×1920 | 9:16 |
| 微信视频号 | 1080×1920 | 9:16 |
| 小红书 | 1080×1440 | 3:4 |
| YouTube | 1920×1080 | 16:9 |
| B站 | 1920×1080 | 16:9 |

## 支持的 LLM

所有兼容 OpenAI API 规范的 LLM 均可使用：

- MiniMax（默认）
- OpenAI（GPT-4o-mini 等）
- DeepSeek
- 通义千问
- 本地部署的开源模型

## 文件结构

```
hermes-skill-ideasphere/
├── SKILL.md                   # 技能定义
├── README.md                  # 使用说明
├── _meta.json                 # 元数据
├── templates/
│   └── pipeline_params.md     # 流水线参数模板
├── references/
│   └── dependencies.md        # 依赖说明
└── scripts/
    ├── pipeline.py            # 工作流编排
    ├── stage_pipeline.py      # 阶段式流水线引擎
    ├── video_clip.py          # 视频剪辑（去静音）
    ├── video_to_text.py       # 语音转字幕
    ├── translate_subtitle.py  # 字幕翻译（上下文感知 + 双语）
    ├── burn_subtitle.py       # 烧录字幕
    ├── platform_render.py     # 平台适配渲染
    ├── ffmpeg_tools.py        # FFmpeg 工具箱
    ├── manifest.py            # 流水线状态管理
    ├── video_download.py      # 🆕 在线视频下载（yt-dlp）
    └── tts_dubbing.py         # 🆕 TTS 语音配音（Edge TTS）
```

## 详细文档

详见 [SKILL.md](SKILL.md) 获取完整使用说明。

## 技术参考

本项目参考了以下优秀开源项目的理念：
- [KrillinAI](https://github.com/krillinai/KrillinAI) — 上下文感知翻译策略、平台适配渲染、流水线状态管理、TTS 配音、在线视频下载

---

**© 2026 AtomCollide-智械工坊团队** | GitHub: [hermes-skill-ideasphere](https://github.com/503496348-ops/hermes-skill-ideasphere)

---

## 🚀 加入AtomCollide-AI智能体实验室

**元素碰撞-AtomCollide-AI 智能体实验室** 是一个专注于AI领域的开源组织，汇聚了众多优秀学习者。

### 核心价值

**找工作：更省力，也更精准**
- 一线大厂内推通道（字节、阿里、腾讯等）
- 全链路求职赋能包（面试题库、简历优化、晋升指导）
- 线下技术沙龙 & 人脉网络

**学AI测试：真正落地，拒绝空谈**
- 从0到1实战落地体系（Skills、MCP、RAG、AI IDE等）
- 独家自研资料与工具矩阵
- 前沿技术同步与提效方案

### 加入社群

- [知识库入口](https://vcnvmnln7wit.feishu.cn/wiki/WpK2wAcV8i6P8tke8X9cLcmDnSh)
- [AI探索交流群](https://applink.feishu.cn/client/chat/chatter/add_by_link?link_token=074vd565-6084-455c-ac52-9703e89a0697)

---

*AtomCollide-智械工坊团队出品*

