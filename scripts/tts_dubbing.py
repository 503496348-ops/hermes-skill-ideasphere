#!/usr/bin/env python3
"""
TTS 配音模块（灵感象限-Ideasphere）
功能：将翻译后的 SRT 字幕合成为语音，并与原视频合并生成配音视频
参考 KrillinAI 的 Edge TTS + 阿里云 TTS 设计

支持:
  - Edge TTS（免费，无需 API Key，300+ 音色）
  - OpenAI TTS（付费，高质量）
  - 自动语速对齐（TTS 时长匹配字幕时间轴）
  - 配音视频生成（替换原始音频轨）

作者：AtomCollide-智械工坊团队
"""

import os
import re
import sys
import json
import argparse
import subprocess
import tempfile
import asyncio
import struct
import wave
from pathlib import Path

# ── Edge TTS 音色推荐表 ──────────────────────────────────────────────────────
EDGE_TTS_VOICES = {
    "zh": "zh-CN-XiaoxiaoNeural",       # 中文女声（自然）
    "zh-male": "zh-CN-YunxiNeural",      # 中文男声
    "en": "en-US-JennyNeural",           # 英文女声
    "en-male": "en-US-GuyNeural",        # 英文男声
    "ja": "ja-JP-NanamiNeural",          # 日文女声
    "ja-male": "ja-JP-KeitaNeural",      # 日文男声
    "ko": "ko-KR-SunHiNeural",           # 韩文女声
    "ko-male": "ko-KR-InJoonNeural",     # 韩文男声
    "fr": "fr-FR-DeniseNeural",          # 法语女声
    "de": "de-DE-KatjaNeural",           # 德语女声
    "es": "es-ES-ElviraNeural",          # 西班牙语女声
    "pt": "pt-BR-FranciscaNeural",       # 葡萄牙语女声
    "ru": "ru-RU-SvetlanaNeural",        # 俄语女声
    "ar": "ar-SA-ZariyahNeural",         # 阿拉伯语女声
}

# 语言代码映射
LANG_CODE_MAP = {
    "中文": "zh", "zh": "zh", "chinese": "zh",
    "英文": "en", "en": "en", "english": "en",
    "日语": "ja", "ja": "ja", "japanese": "ja",
    "韩语": "ko", "ko": "ko", "korean": "ko",
    "法语": "fr", "fr": "fr", "french": "fr",
    "德语": "de", "de": "de", "german": "de",
    "西班牙语": "es", "es": "es", "spanish": "es",
    "葡萄牙语": "pt", "pt": "pt", "portuguese": "pt",
    "俄语": "ru", "ru": "ru", "russian": "ru",
    "阿拉伯语": "ar", "ar": "ar", "arabic": "ar",
}


# ── SRT 解析 ──────────────────────────────────────────────────────────────────

def parse_srt(srt_path):
    """解析 SRT 文件，返回字幕块列表"""
    blocks = []
    with open(srt_path, "r", encoding="utf-8") as f:
        content = f.read()

    pattern = re.compile(
        r"(\d+)\s*\n"
        r"(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})\s*\n"
        r"((?:(?!\n\d+\n\d{2}:\d{2}).+\n?)+)",
        re.MULTILINE,
    )
    for m in pattern.finditer(content):
        text = m.group(4).strip()
        # 双语字幕取最后一行（译文）
        lines = text.split("\n")
        translated_text = lines[-1].strip() if len(lines) > 1 else lines[0].strip()
        blocks.append({
            "index": int(m.group(1)),
            "start": m.group(2),
            "end": m.group(3),
            "text": text,
            "translated_text": translated_text,
            "start_sec": srt_time_to_seconds(m.group(2)),
            "end_sec": srt_time_to_seconds(m.group(3)),
        })
    return blocks


def srt_time_to_seconds(srt_time):
    """SRT 时间格式转秒数"""
    h, m, rest = srt_time.split(":")
    s, ms = rest.split(",")
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000


def seconds_to_srt_time(seconds):
    """秒数转 SRT 时间格式"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def get_audio_duration(audio_path):
    """获取音频文件时长（秒）"""
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", audio_path],
            capture_output=True, text=True
        )
        return float(result.stdout.strip())
    except Exception:
        return 0.0


# ── Edge TTS 合成 ─────────────────────────────────────────────────────────────

async def _edge_tts_synthesize(text, voice, output_path):
    """使用 edge-tts 合成单条语音"""
    try:
        import edge_tts
    except ImportError:
        raise ImportError("edge-tts not installed. Run: pip3 install edge-tts")

    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)


def edge_tts_synthesize(text, voice, output_path):
    """同步包装：Edge TTS 合成"""
    asyncio.run(_edge_tts_synthesize(text, voice, output_path))


def edge_tts_synthesize_with_speed(text, voice, output_path, target_duration=None):
    """Edge TTS 合成并调整语速以匹配目标时长"""
    edge_tts_synthesize(text, voice, output_path)

    if target_duration and target_duration > 0:
        actual_duration = get_audio_duration(output_path)
        if actual_duration > 0 and abs(actual_duration - target_duration) > 0.3:
            # 计算速度因子
            speed_factor = actual_duration / target_duration
            # 限制速度范围 (0.5x ~ 2.0x)
            speed_factor = max(0.5, min(2.0, speed_factor))

            if abs(speed_factor - 1.0) > 0.05:
                # 使用 atempo 调整速度
                temp_path = output_path + ".temp.wav"
                cmd = [
                    "ffmpeg", "-y", "-i", output_path,
                    "-filter:a", f"atempo={speed_factor}",
                    temp_path
                ]
                subprocess.run(cmd, capture_output=True)
                if os.path.exists(temp_path):
                    os.replace(temp_path, output_path)


# ── OpenAI TTS 合成 ───────────────────────────────────────────────────────────

def openai_tts_synthesize(text, voice, output_path, api_key=None, model="tts-1",
                          base_url="https://api.openai.com/v1"):
    """使用 OpenAI TTS API 合成语音"""
    import requests

    if not api_key:
        api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OpenAI API Key required for OpenAI TTS")

    url = f"{base_url}/audio/speech"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "input": text,
        "voice": voice or "alloy",
        "response_format": "wav",
    }

    resp = requests.post(url, headers=headers, json=payload, timeout=60)
    if resp.status_code != 200:
        raise RuntimeError(f"OpenAI TTS failed: {resp.status_code} {resp.text[:200]}")

    with open(output_path, "wb") as f:
        f.write(resp.content)


# ── 批量 TTS 合成 ─────────────────────────────────────────────────────────────

def synthesize_subtitles(srt_path, output_dir, provider="edge", voice=None,
                         lang="zh", api_key=None, speed_match=True):
    """
    批量合成 SRT 字幕为语音

    参数:
        srt_path: SRT 字幕文件路径
        output_dir: 输出目录
        provider: TTS 提供商 (edge / openai)
        voice: 音色名称（None 则自动选择）
        lang: 语言代码
        api_key: API Key（OpenAI TTS 需要）
        speed_match: 是否自动调整语速匹配字幕时长

    返回:
        dict: {
            "audio_dir": 音频片段目录,
            "final_audio": 合并后的完整音频路径,
            "segments": [{index, start, end, audio_path, duration}, ...]
        }
    """
    os.makedirs(output_dir, exist_ok=True)
    audio_dir = os.path.join(output_dir, "tts_segments")
    os.makedirs(audio_dir, exist_ok=True)

    # 解析 SRT
    blocks = parse_srt(srt_path)
    if not blocks:
        print("❌ SRT 文件为空或无法解析")
        return None

    print(f"🎙️ TTS 配音: {len(blocks)} 条字幕")
    print(f"   提供商: {provider}")
    print(f"   语言: {lang}")

    # 确定音色
    if not voice:
        if provider == "edge":
            voice = EDGE_TTS_VOICES.get(lang, EDGE_TTS_VOICES.get("zh"))
        elif provider == "openai":
            voice = "alloy"
    print(f"   音色: {voice}")

    # 合成每条字幕
    segments = []
    for i, block in enumerate(blocks):
        text = block["translated_text"]
        if not text.strip():
            continue

        seg_path = os.path.join(audio_dir, f"seg_{block['index']:04d}.wav")
        target_duration = block["end_sec"] - block["start_sec"]

        try:
            if provider == "edge":
                if speed_match:
                    edge_tts_synthesize_with_speed(text, voice, seg_path, target_duration)
                else:
                    edge_tts_synthesize(text, voice, seg_path)
            elif provider == "openai":
                openai_tts_synthesize(text, voice, seg_path, api_key=api_key)
                if speed_match:
                    # OpenAI TTS 也需要速度匹配
                    actual = get_audio_duration(seg_path)
                    if actual > 0 and abs(actual - target_duration) > 0.3:
                        factor = max(0.5, min(2.0, actual / target_duration))
                        if abs(factor - 1.0) > 0.05:
                            temp = seg_path + ".temp.wav"
                            subprocess.run([
                                "ffmpeg", "-y", "-i", seg_path,
                                "-filter:a", f"atempo={factor}", temp
                            ], capture_output=True)
                            if os.path.exists(temp):
                                os.replace(temp, seg_path)

            duration = get_audio_duration(seg_path)
            segments.append({
                "index": block["index"],
                "start": block["start_sec"],
                "end": block["end_sec"],
                "text": text,
                "audio_path": seg_path,
                "duration": duration,
            })

            if (i + 1) % 10 == 0 or i + 1 == len(blocks):
                print(f"  📊 进度: {i + 1}/{len(blocks)}")

        except Exception as e:
            print(f"  ⚠️ 合成失败 #{block['index']}: {e}")
            continue

    if not segments:
        print("❌ 没有成功合成任何语音")
        return None

    # 合并所有音频段到完整时间轴
    final_audio = merge_tts_segments(segments, output_dir, blocks)

    result = {
        "audio_dir": audio_dir,
        "final_audio": final_audio,
        "segments": segments,
        "total_segments": len(segments),
    }

    # 保存元数据
    meta_path = os.path.join(output_dir, "tts_meta.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=str)

    print(f"✅ TTS 合成完成: {len(segments)} 段")
    print(f"   完整音频: {final_audio}")
    return result


def merge_tts_segments(segments, output_dir, blocks):
    """
    将 TTS 片段按时间轴合并为完整音频

    使用 FFmpeg 的 adelay + amix 实现精确定位
    """
    final_path = os.path.join(output_dir, "tts_full_audio.wav")

    if not segments:
        return final_path

    # 计算总时长（取最后一个字幕的结束时间 + 缓冲）
    total_duration = blocks[-1]["end_sec"] + 1.0

    # 构建 FFmpeg 复杂滤镜
    inputs = []
    filter_parts = []
    mix_inputs = []

    for i, seg in enumerate(segments):
        inputs.extend(["-i", seg["audio_path"]])
        delay_ms = int(seg["start"] * 1000)
        filter_parts.append(f"[{i}:a]adelay={delay_ms}|{delay_ms}[d{i}]")
        mix_inputs.append(f"[d{i}]")

    # amix 混合所有延迟后的音频
    mix_str = "".join(mix_inputs)
    filter_parts.append(
        f"{mix_str}amix=inputs={len(segments)}:duration=longest:dropout_transition=0[out]"
    )
    filter_complex = ";".join(filter_parts)

    cmd = ["ffmpeg", "-y"] + inputs + [
        "-filter_complex", filter_complex,
        "-map", "[out]",
        "-ar", "44100",
        "-ac", "1",
        final_path
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        # 降级方案：简单的 concat
        print("  ⚠️ 复杂合并失败，使用简单拼接...")
        return simple_concat_segments(segments, output_dir, total_duration)

    return final_path


def simple_concat_segments(segments, output_dir, total_duration):
    """降级方案：生成静音底板 + 按时间覆盖"""
    final_path = os.path.join(output_dir, "tts_full_audio.wav")

    # 生成静音底板
    silence_path = os.path.join(output_dir, "silence.wav")
    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi",
        "-i", f"anullsrc=r=44100:cl=mono:d={total_duration}",
        silence_path
    ], capture_output=True)

    if not os.path.exists(silence_path):
        return final_path

    # 逐段覆盖
    current = silence_path
    for i, seg in enumerate(segments):
        out = os.path.join(output_dir, f"mixed_{i}.wav")
        cmd = [
            "ffmpeg", "-y",
            "-i", current,
            "-i", seg["audio_path"],
            "-filter_complex",
            f"[0:a][1:a]amix=inputs=2:duration=first:dropout_transition=0[out]",
            "-map", "[out]",
            out
        ]
        subprocess.run(cmd, capture_output=True)
        if os.path.exists(out):
            current = out

    if current != silence_path:
        os.replace(current, final_path)

    # 清理临时文件
    for f in os.listdir(output_dir):
        if f.startswith("mixed_") and f.endswith(".wav"):
            os.remove(os.path.join(output_dir, f))
    if os.path.exists(silence_path):
        os.remove(silence_path)

    return final_path


# ── 配音视频生成 ───────────────────────────────────────────────────────────────

def generate_dubbed_video(video_path, tts_audio_path, output_path, keep_original=False,
                          original_volume=0.15):
    """
    生成配音视频：将 TTS 音频替换（或混合）原始视频的音频轨

    参数:
        video_path: 原始视频路径
        tts_audio_path: TTS 合成音频路径
        output_path: 输出视频路径
        keep_original: 是否保留原始音频（混合模式）
        original_volume: 保留原始音频时的音量比例 (0.0-1.0)
    """
    if not os.path.exists(video_path):
        print(f"❌ 视频不存在: {video_path}")
        return None
    if not os.path.exists(tts_audio_path):
        print(f"❌ TTS 音频不存在: {tts_audio_path}")
        return None

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    if keep_original:
        # 混合模式：原始音频 + TTS 音频
        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-i", tts_audio_path,
            "-filter_complex",
            f"[0:a]volume={original_volume}[orig];"
            f"[1:a]volume=1.0[tts];"
            f"[orig][tts]amix=inputs=2:duration=first:dropout_transition=0[aout]",
            "-map", "0:v",
            "-map", "[aout]",
            "-c:v", "copy",
            "-shortest",
            output_path
        ]
    else:
        # 替换模式：完全使用 TTS 音频
        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-i", tts_audio_path,
            "-map", "0:v",
            "-map", "1:a",
            "-c:v", "copy",
            "-shortest",
            output_path
        ]

    print(f"🎬 生成配音视频: {os.path.basename(output_path)}")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"❌ 生成失败: {result.stderr[:200]}")
        return None

    if os.path.exists(output_path):
        size_mb = os.path.getsize(output_path) / 1024 / 1024
        print(f"✅ 配音视频: {os.path.basename(output_path)} ({size_mb:.1f}MB)")
        return output_path

    return None


# ── 列出可用音色 ───────────────────────────────────────────────────────────────

async def _list_edge_voices(lang=None):
    """列出 Edge TTS 可用音色"""
    try:
        import edge_tts
    except ImportError:
        print("❌ edge-tts 未安装: pip3 install edge-tts")
        return []

    voices = await edge_tts.list_voices()
    if lang:
        lang_prefix = lang.lower()[:2]
        voices = [v for v in voices if v["Locale"].lower().startswith(lang_prefix)]
    return voices


def list_voices(provider="edge", lang=None):
    """列出可用音色"""
    if provider == "edge":
        voices = asyncio.run(_list_edge_voices(lang))
        print(f"\n🎙️ Edge TTS 可用音色 ({len(voices)} 个):")
        print("-" * 70)
        print(f"{'音色名称':<35} {'语言':<10} {'性别':<6}")
        print("-" * 70)
        for v in voices:
            gender = v.get("Gender", "?")
            locale = v.get("Locale", "?")
            name = v.get("ShortName", "?")
            print(f"{name:<35} {locale:<10} {gender:<6}")
        print("-" * 70)
        return voices
    elif provider == "openai":
        print("\n🎙️ OpenAI TTS 可用音色:")
        for v in ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]:
            print(f"  - {v}")
        return ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
    return []


# ── 推荐音色 ───────────────────────────────────────────────────────────────────

def recommend_voice(lang, gender=None):
    """根据语言和性别推荐音色"""
    lang_code = LANG_CODE_MAP.get(lang.lower(), lang.lower()[:2])

    if gender and gender.lower() in ("male", "男"):
        key = f"{lang_code}-male"
    else:
        key = lang_code

    voice = EDGE_TTS_VOICES.get(key) or EDGE_TTS_VOICES.get(lang_code, "zh-CN-XiaoxiaoNeural")
    return voice


# ── CLI 入口 ───────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="TTS 配音模块（灵感象限-Ideasphere）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 使用 Edge TTS 合成字幕语音
  python3 tts_dubbing.py --srt translated.srt --output ./tts_output

  # 指定中文男声
  python3 tts_dubbing.py --srt translated.srt --output ./tts_output --lang zh --voice zh-CN-YunxiNeural

  # 使用 OpenAI TTS
  python3 tts_dubbing.py --srt translated.srt --output ./tts_output --provider openai --voice nova

  # 生成配音视频（替换原始音频）
  python3 tts_dubbing.py --srt translated.srt --video original.mp4 --output ./tts_output

  # 生成配音视频（保留原始音频混合）
  python3 tts_dubbing.py --srt translated.srt --video original.mp4 --output ./tts_output --mix-original

  # 列出可用音色
  python3 tts_dubbing.py --list-voices --lang zh
        """
    )
    parser.add_argument("--srt", help="输入 SRT 字幕文件路径")
    parser.add_argument("--video", help="原始视频路径（生成配音视频时需要）")
    parser.add_argument("--output", "-o", default="./tts_output", help="输出目录")
    parser.add_argument("--provider", choices=["edge", "openai"], default="edge",
                        help="TTS 提供商 (默认: edge)")
    parser.add_argument("--voice", help="音色名称（不指定则自动选择）")
    parser.add_argument("--lang", default="zh", help="语言代码 (默认: zh)")
    parser.add_argument("--api-key", help="API Key（OpenAI TTS 需要）")
    parser.add_argument("--no-speed-match", action="store_true",
                        help="不调整语速匹配字幕时长")
    parser.add_argument("--mix-original", action="store_true",
                        help="保留原始音频（混合模式）")
    parser.add_argument("--original-volume", type=float, default=0.15,
                        help="混合模式下原始音频音量 (0.0-1.0, 默认 0.15)")
    parser.add_argument("--list-voices", action="store_true", help="列出可用音色")
    parser.add_argument("--install-deps", action="store_true", help="安装依赖")

    args = parser.parse_args()

    # 安装依赖
    if args.install_deps:
        print("📦 安装 TTS 依赖...")
        subprocess.run([sys.executable, "-m", "pip", "install", "edge-tts",
                        "--break-system-packages"])
        print("✅ 依赖安装完成")
        return

    # 列出音色
    if args.list_voices:
        list_voices(args.provider, args.lang)
        return

    # 主流程
    if not args.srt:
        parser.error("--srt 参数是必需的")

    if not os.path.exists(args.srt):
        print(f"❌ SRT 文件不存在: {args.srt}")
        sys.exit(1)

    # TTS 合成
    result = synthesize_subtitles(
        srt_path=args.srt,
        output_dir=args.output,
        provider=args.provider,
        voice=args.voice,
        lang=args.lang,
        api_key=args.api_key,
        speed_match=not args.no_speed_match,
    )

    if not result:
        sys.exit(1)

    # 生成配音视频
    if args.video:
        dubbed_path = os.path.join(args.output, "dubbed_video.mp4")
        generate_dubbed_video(
            video_path=args.video,
            tts_audio_path=result["final_audio"],
            output_path=dubbed_path,
            keep_original=args.mix_original,
            original_volume=args.original_volume,
        )

    print("\n🎉 TTS 配音完成！")


if __name__ == "__main__":
    main()
