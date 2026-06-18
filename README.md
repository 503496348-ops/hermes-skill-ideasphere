# 灵感象限-Ideasphere

**自媒体视频一站式剪辑技能包**

> **版本**：v1.1.0
> **作者**：AtomCollide-智械工坊团队
> **最后更新**：2026-06-19

---

## 概览

灵感象限是 Hermes Agent 的视频编辑技能包，输入本地素材，自动完成完整的视频处理流水线。

```
去静音剪辑 → 语音转字幕 → LLM纠错 → 字幕翻译 → 双语字幕 → 字幕烧录 → 平台适配渲染 → 多平台导出
```

**参考 KrillinAI（10.3K⭐）的优秀设计，实现了：**
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

# 3. 一键处理（含翻译 + 平台适配）
python3 scripts/pipeline.py --all \
  --input "/path/to/videos" \
  --output "/path/to/output" \
  --target-lang "English" \
  --bilingual \
  --platform douyin
```

## 核心流程

| 步骤 | 功能 | 工具 |
|------|------|------|
| 1 | 去静音剪辑 | auto-editor |
| 2 | 视频拼接 | ffmpeg |
| 3 | 语音转字幕 | Faster Whisper + LLM 纠错 |
| 4 | 字幕翻译（可选） | LLM 上下文感知翻译 |
| 5 | 字幕烧录 | ffmpeg |
| 6 | 平台适配渲染（可选） | ffmpeg + 平台预设 |

## 支持的平台

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
└── scripts/
    ├── pipeline.py            # 工作流编排
    ├── video_clip.py          # 视频剪辑（去静音）
    ├── video_to_text.py       # 语音转字幕
    ├── translate_subtitle.py  # 字幕翻译（上下文感知 + 双语）
    ├── burn_subtitle.py       # 烧录字幕
    ├── platform_render.py     # 平台适配渲染
    ├── ffmpeg_tools.py        # FFmpeg 工具箱
    └── manifest.py            # 流水线状态管理
```

## 详细文档

详见 [SKILL.md](SKILL.md) 获取完整使用说明。

## 技术参考

本项目参考了以下优秀开源项目的理念：
- [KrillinAI](https://github.com/krillinai/KrillinAI) — 上下文感知翻译策略、平台适配渲染、流水线状态管理

---

**© 2026 AtomCollide-智械工坊团队** | GitHub: [hermes-skill-ideasphere](https://github.com/503496348-ops/hermes-skill-ideasphere)
