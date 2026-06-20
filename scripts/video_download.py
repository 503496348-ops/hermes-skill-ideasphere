#!/usr/bin/env python3
"""
在线视频下载模块（灵感象限-Ideasphere）
功能：从 YouTube / Bilibili / TikTok 等平台下载视频和字幕
参考 KrillinAI 的 download.go + youtube_subtitle_helper.go 设计

支持:
  - YouTube / Bilibili / TikTok / Twitter 等 1000+ 平台（via yt-dlp）
  - 自动下载最佳画质（或指定分辨率）
  - 自动提取字幕（自动生成 + 手动上传）
  - 下载进度显示
  - 代理支持
  - 批量下载

作者：AtomCollide-智械工坊团队
"""

import os
import re
import sys
import json
import argparse
import subprocess
import shutil
from pathlib import Path
from urllib.parse import urlparse

# ── 平台识别 ──────────────────────────────────────────────────────────────────

PLATFORM_PATTERNS = {
    "youtube": [r"youtube\.com", r"youtu\.be", r"youtube\.com/shorts"],
    "bilibili": [r"bilibili\.com", r"b23\.tv"],
    "tiktok": [r"tiktok\.com"],
    "douyin": [r"douyin\.com", r"iesdouyin\.com"],
    "twitter": [r"twitter\.com", r"x\.com"],
    "instagram": [r"instagram\.com"],
    "weibo": [r"weibo\.com", r"weibo\.cn"],
    "xiaohongshu": [r"xiaohongshu\.com", r"xhslink\.com"],
    "kuaishou": [r"kuaishou\.com", r"gifshow\.com"],
}

PLATFORM_LABELS = {
    "youtube": "YouTube",
    "bilibili": "B站",
    "tiktok": "TikTok",
    "douyin": "抖音",
    "twitter": "Twitter/X",
    "instagram": "Instagram",
    "weibo": "微博",
    "xiaohongshu": "小红书",
    "kuaishou": "快手",
}


def detect_platform(url):
    """检测 URL 所属平台"""
    url_lower = url.lower()
    for platform, patterns in PLATFORM_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, url_lower):
                return platform
    return "other"


def is_valid_url(url):
    """验证 URL 格式"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


# ── yt-dlp 工具函数 ────────────────────────────────────────────────────────────

def check_ytdlp():
    """检查 yt-dlp 是否安装"""
    if shutil.which("yt-dlp"):
        try:
            result = subprocess.run(
                ["yt-dlp", "--version"],
                capture_output=True, text=True
            )
            version = result.stdout.strip()
            return True, version
        except Exception:
            return True, "unknown"
    return False, None


def install_ytdlp():
    """安装 yt-dlp"""
    print("📦 安装 yt-dlp...")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "yt-dlp", "--break-system-packages", "-q"],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        print("✅ yt-dlp 安装完成")
        return True
    else:
        print(f"❌ 安装失败: {result.stderr[:200]}")
        return False


def get_video_info(url, proxy=None):
    """获取视频元信息（不下载）"""
    cmd = ["yt-dlp", "--dump-json", "--no-download", url]
    if proxy:
        cmd.extend(["--proxy", proxy])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            return json.loads(result.stdout)
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
        pass
    return None


# ── 单视频下载 ─────────────────────────────────────────────────────────────────

def download_video(url, output_dir, filename=None, quality="best",
                   max_height=None, proxy=None, download_subs=True,
                   sub_langs=None, embed_subs=True):
    """
    下载单个视频

    参数:
        url: 视频 URL
        output_dir: 输出目录
        filename: 输出文件名（None 则使用默认）
        quality: 画质 (best / good / medium / worst)
        max_height: 最大分辨率高度（如 1080, 720）
        proxy: 代理地址
        download_subs: 是否下载字幕
        sub_langs: 字幕语言列表 (如 ["zh", "en", "zh-Hans"])
        embed_subs: 是否将字幕嵌入视频

    返回:
        dict: {"video_path": ..., "subtitle_paths": [...], "info": {...}}
    """
    os.makedirs(output_dir, exist_ok=True)

    # 检查 yt-dlp
    installed, version = check_ytdlp()
    if not installed:
        print("❌ yt-dlp 未安装")
        if not install_ytdlp():
            return None

    # 检测平台
    platform = detect_platform(url)
    platform_label = PLATFORM_LABELS.get(platform, platform)
    print(f"🔍 检测到平台: {platform_label}")
    print(f"🔗 URL: {url[:80]}...")

    # 构建输出模板
    if filename:
        outtmpl = os.path.join(output_dir, filename)
    else:
        outtmpl = os.path.join(output_dir, "%(title)s.%(ext)s")

    # 构建命令
    cmd = [
        "yt-dlp",
        "--no-playlist",            # 不下载播放列表
        "--no-overwrites",          # 不覆盖已有文件
        "--encoding", "utf-8",
        "-o", outtmpl,
    ]

    # 画质设置
    if max_height:
        cmd.extend(["-f", f"bestvideo[height<={max_height}]+bestaudio/best[height<={max_height}]/best"])
    elif quality == "best":
        cmd.extend(["-f", "bestvideo+bestaudio/best"])
    elif quality == "good":
        cmd.extend(["-f", "bestvideo[height<=1080]+bestaudio/best[height<=1080]/best"])
    elif quality == "medium":
        cmd.extend(["-f", "bestvideo[height<=720]+bestaudio/best[height<=720]/best"])
    elif quality == "worst":
        cmd.extend(["-f", "worst"])

    # 代理
    if proxy:
        cmd.extend(["--proxy", proxy])

    # 字幕下载
    if download_subs:
        cmd.extend(["--write-sub", "--write-auto-sub"])
        if sub_langs:
            cmd.extend(["--sub-lang", ",".join(sub_langs)])
        else:
            # 根据平台设置默认字幕语言
            default_subs = {
                "youtube": "zh-Hans,zh,en",
                "bilibili": "zh",
                "tiktok": "zh,en",
                "douyin": "zh",
            }
            cmd.extend(["--sub-lang", default_subs.get(platform, "zh,en")])
        cmd.extend(["--sub-format", "srt"])
        if embed_subs:
            cmd.extend(["--embed-subs"])

    # 合并格式
    cmd.extend(["--merge-output-format", "mp4"])

    # 输出模板
    cmd.append(url)

    # 执行下载
    print(f"⬇️  开始下载...")
    print(f"   画质: {quality}" + (f" (≤{max_height}p)" if max_height else ""))

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    output_text = result.stdout + result.stderr

    # 解析输出文件
    video_path = None
    subtitle_paths = []

    # 从输出中提取文件名
    for line in output_text.split("\n"):
        if "[Merger]" in line or "Merging" in line or "has already been downloaded" in line:
            # 提取文件路径
            match = re.search(r'"([^"]+\.mp4)"', line)
            if match:
                video_path = match.group(1)
        if "[Download]" in line and ".srt" in line:
            match = re.search(r'Destination: (.+\.srt)', line)
            if match:
                subtitle_paths.append(match.group(1).strip())

    # 如果没从输出中找到，搜索目录
    if not video_path:
        for f in sorted(os.listdir(output_dir), reverse=True):
            if f.endswith((".mp4", ".mkv", ".webm")) and not f.startswith("."):
                video_path = os.path.join(output_dir, f)
                break

    # 搜索字幕文件
    if not subtitle_paths:
        for f in os.listdir(output_dir):
            if f.endswith(".srt") or f.endswith(".vtt"):
                subtitle_paths.append(os.path.join(output_dir, f))

    if video_path:
        size_mb = os.path.getsize(video_path) / 1024 / 1024
        print(f"✅ 下载完成: {os.path.basename(video_path)} ({size_mb:.1f}MB)")
        if subtitle_paths:
            print(f"📝 字幕文件: {len(subtitle_paths)} 个")
            for sp in subtitle_paths:
                print(f"   - {os.path.basename(sp)}")
    else:
        print(f"❌ 下载失败")
        if result.returncode != 0:
            print(f"   错误: {output_text[:300]}")
        return None

    return {
        "video_path": video_path,
        "subtitle_paths": subtitle_paths,
        "platform": platform,
        "url": url,
    }


# ── 批量下载 ───────────────────────────────────────────────────────────────────

def download_batch(urls, output_dir, **kwargs):
    """
    批量下载多个视频

    参数:
        urls: URL 列表
        output_dir: 输出目录
        **kwargs: 传递给 download_video 的参数

    返回:
        list[dict]: 每个视频的下载结果
    """
    results = []
    total = len(urls)

    print(f"\n📦 批量下载: {total} 个视频")
    print("=" * 50)

    for i, url in enumerate(urls, 1):
        print(f"\n[{i}/{total}] {url[:60]}...")
        # 创建子目录（使用序号）
        sub_dir = os.path.join(output_dir, f"{i:03d}")
        result = download_video(url, sub_dir, **kwargs)
        results.append({
            "index": i,
            "url": url,
            "result": result,
            "success": result is not None,
        })

    # 统计
    success_count = sum(1 for r in results if r["success"])
    print(f"\n{'=' * 50}")
    print(f"📊 批量下载完成: {success_count}/{total} 成功")

    return results


# ── 仅下载字幕 ─────────────────────────────────────────────────────────────────

def download_subtitles_only(url, output_dir, sub_langs=None, proxy=None):
    """
    仅下载字幕（不下载视频）

    参考 KrillinAI 的 youtube_subtitle_helper.go
    """
    os.makedirs(output_dir, exist_ok=True)

    installed, _ = check_ytdlp()
    if not installed:
        if not install_ytdlp():
            return None

    platform = detect_platform(url)
    print(f"📝 下载字幕: {PLATFORM_LABELS.get(platform, platform)}")

    cmd = [
        "yt-dlp",
        "--write-sub", "--write-auto-sub",
        "--skip-download",
        "--sub-format", "srt",
        "--encoding", "utf-8",
    ]

    if sub_langs:
        cmd.extend(["--sub-lang", ",".join(sub_langs)])
    else:
        cmd.extend(["--sub-lang", "zh-Hans,zh,en"])

    if proxy:
        cmd.extend(["--proxy", proxy])

    cmd.extend(["-o", os.path.join(output_dir, "%(title)s.%(ext)s")])
    cmd.append(url)

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

    # 收集字幕文件
    subtitle_paths = []
    for f in os.listdir(output_dir):
        if f.endswith(".srt") or f.endswith(".vtt"):
            subtitle_paths.append(os.path.join(output_dir, f))

    if subtitle_paths:
        print(f"✅ 字幕下载完成: {len(subtitle_paths)} 个")
        for sp in subtitle_paths:
            print(f"   - {os.path.basename(sp)}")
    else:
        print("⚠️ 未找到可用字幕（该视频可能没有字幕）")

    return subtitle_paths


# ── 视频信息获取 ───────────────────────────────────────────────────────────────

def get_video_metadata(url, proxy=None):
    """
    获取视频详细信息

    返回:
        dict: {
            "title": 标题,
            "duration": 时长(秒),
            "uploader": 上传者,
            "view_count": 播放量,
            "description": 描述,
            "platform": 平台,
            "subtitles": 可用字幕语言,
            "formats": 可用格式,
        }
    """
    info = get_video_info(url, proxy)
    if not info:
        return None

    platform = detect_platform(url)

    return {
        "title": info.get("title", "Unknown"),
        "duration": info.get("duration", 0),
        "uploader": info.get("uploader", "Unknown"),
        "view_count": info.get("view_count", 0),
        "description": (info.get("description", "") or "")[:500],
        "platform": platform,
        "platform_label": PLATFORM_LABELS.get(platform, platform),
        "subtitles": list(info.get("subtitles", {}).keys()),
        "auto_subtitles": list(info.get("automatic_captions", {}).keys()),
        "width": info.get("width", 0),
        "height": info.get("height", 0),
        "fps": info.get("fps", 0),
        "filesize_approx": info.get("filesize_approx", 0),
    }


# ── 支持的平台列表 ─────────────────────────────────────────────────────────────

def list_supported_sites():
    """列出支持的平台"""
    installed, version = check_ytdlp()
    if not installed:
        print("❌ yt-dlp 未安装")
        return

    print(f"\n🌐 支持的平台 (yt-dlp {version}):")
    print("=" * 50)

    # 列出主要平台
    for platform, label in PLATFORM_LABELS.items():
        patterns = PLATFORM_PATTERNS[platform]
        print(f"  ✅ {label:<15} {patterns[0]}")

    print(f"\n  ... 以及 1000+ 其他平台（由 yt-dlp 支持）")
    print(f"\n完整列表: yt-dlp --list-extractors")


# ── CLI 入口 ───────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="在线视频下载模块（灵感象限-Ideasphere）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 下载 YouTube 视频（含字幕）
  python3 video_download.py "https://www.youtube.com/watch?v=xxx" -o ./downloads

  # 下载 B站视频
  python3 video_download.py "https://www.bilibili.com/video/BVxxx" -o ./downloads

  # 指定画质
  python3 video_download.py "https://..." -o ./downloads --quality medium

  # 限制最大分辨率
  python3 video_download.py "https://..." -o ./downloads --max-height 720

  # 仅下载字幕
  python3 video_download.py "https://..." -o ./downloads --subs-only

  # 使用代理
  python3 video_download.py "https://..." -o ./downloads --proxy "http://127.0.0.1:7890"

  # 批量下载（从文件读取 URL）
  python3 video_download.py --batch urls.txt -o ./downloads

  # 获取视频信息（不下载）
  python3 video_download.py "https://..." --info

  # 列出支持的平台
  python3 video_download.py --list-sites

  # 安装依赖
  python3 video_download.py --install-deps
        """
    )
    parser.add_argument("url", nargs="?", help="视频 URL")
    parser.add_argument("--batch", help="批量下载：URL 列表文件（每行一个 URL）")
    parser.add_argument("--output", "-o", default="./downloads", help="输出目录")
    parser.add_argument("--quality", choices=["best", "good", "medium", "worst"],
                        default="best", help="画质 (默认: best)")
    parser.add_argument("--max-height", type=int, help="最大分辨率高度 (如 720, 1080)")
    parser.add_argument("--proxy", help="代理地址 (如 http://127.0.0.1:7890)")
    parser.add_argument("--filename", "-f", help="输出文件名")
    parser.add_argument("--no-subs", action="store_true", help="不下载字幕")
    parser.add_argument("--subs-only", action="store_true", help="仅下载字幕")
    parser.add_argument("--sub-langs", help="字幕语言 (逗号分隔, 如 zh,en)")
    parser.add_argument("--info", action="store_true", help="获取视频信息（不下载）")
    parser.add_argument("--list-sites", action="store_true", help="列出支持的平台")
    parser.add_argument("--install-deps", action="store_true", help="安装依赖")
    parser.add_argument("--json", action="store_true", help="JSON 格式输出")

    args = parser.parse_args()

    # 安装依赖
    if args.install_deps:
        install_ytdlp()
        return

    # 列出支持平台
    if args.list_sites:
        list_supported_sites()
        return

    # 获取视频信息
    if args.info:
        if not args.url:
            parser.error("需要提供 URL")
        metadata = get_video_metadata(args.url, args.proxy)
        if metadata:
            if args.json:
                print(json.dumps(metadata, ensure_ascii=False, indent=2))
            else:
                print(f"\n📹 视频信息:")
                print(f"  标题: {metadata['title']}")
                print(f"  平台: {metadata['platform_label']}")
                print(f"  时长: {metadata['duration']}秒")
                print(f"  上传者: {metadata['uploader']}")
                print(f"  播放量: {metadata['view_count']:,}")
                if metadata['subtitles']:
                    print(f"  字幕: {', '.join(metadata['subtitles'][:10])}")
                if metadata['auto_subtitles']:
                    print(f"  自动字幕: {', '.join(metadata['auto_subtitles'][:10])}")
                print(f"  分辨率: {metadata['width']}x{metadata['height']}")
                print(f"  描述: {metadata['description'][:100]}...")
        else:
            print("❌ 无法获取视频信息")
        return

    # 批量下载
    if args.batch:
        if not os.path.exists(args.batch):
            print(f"❌ 文件不存在: {args.batch}")
            sys.exit(1)

        with open(args.batch, "r", encoding="utf-8") as f:
            urls = [line.strip() for line in f if line.strip() and not line.startswith("#")]

        if not urls:
            print("❌ 未找到有效 URL")
            sys.exit(1)

        sub_langs = args.sub_langs.split(",") if args.sub_langs else None
        download_batch(
            urls, args.output,
            quality=args.quality,
            max_height=args.max_height,
            proxy=args.proxy,
            download_subs=not args.no_subs,
            sub_langs=sub_langs,
        )
        return

    # 单视频下载
    if not args.url:
        parser.error("需要提供视频 URL")

    sub_langs = args.sub_langs.split(",") if args.sub_langs else None

    if args.subs_only:
        download_subtitles_only(args.url, args.output, sub_langs, args.proxy)
    else:
        result = download_video(
            url=args.url,
            output_dir=args.output,
            filename=args.filename,
            quality=args.quality,
            max_height=args.max_height,
            proxy=args.proxy,
            download_subs=not args.no_subs,
            sub_langs=sub_langs,
        )
        if args.json and result:
            print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
