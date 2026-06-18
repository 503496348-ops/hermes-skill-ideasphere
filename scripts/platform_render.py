#!/usr/bin/env python3
"""
平台适配渲染模块（灵感象限-Ideasphere）
功能：根据目标平台自动调整视频尺寸、字幕样式
参考 KrillinAI 的横向/竖向渲染策略

支持平台：
- 抖音/快手/视频号: 9:16 竖屏 (1080x1920)
- YouTube/B站: 16:9 横屏 (1920x1080)
- 小红书: 3:4 竖屏 (1080x1440)

作者：AtomCollide-智械工坊团队
"""

import os
import sys
import argparse
import subprocess
import json

# ── 平台预设 ──────────────────────────────────────────────────────────────────

PLATFORM_PRESETS = {
    "douyin": {
        "name": "抖音/快手",
        "width": 1080,
        "height": 1920,
        "aspect": "9:16",
        "subtitle_fontsize": 14,
        "subtitle_margin_v": 120,  # 字幕距底部距离
        "subtitle_style": "bold",
        "subtitle_outline": 2,
    },
    "wechat": {
        "name": "微信视频号",
        "width": 1080,
        "height": 1920,
        "aspect": "9:16",
        "subtitle_fontsize": 14,
        "subtitle_margin_v": 120,
        "subtitle_style": "bold",
        "subtitle_outline": 2,
    },
    "xiaohongshu": {
        "name": "小红书",
        "width": 1080,
        "height": 1440,
        "aspect": "3:4",
        "subtitle_fontsize": 14,
        "subtitle_margin_v": 100,
        "subtitle_style": "bold",
        "subtitle_outline": 2,
    },
    "youtube": {
        "name": "YouTube",
        "width": 1920,
        "height": 1080,
        "aspect": "16:9",
        "subtitle_fontsize": 18,
        "subtitle_margin_v": 60,
        "subtitle_style": "normal",
        "subtitle_outline": 1,
    },
    "bilibili": {
        "name": "B站",
        "width": 1920,
        "height": 1080,
        "aspect": "16:9",
        "subtitle_fontsize": 18,
        "subtitle_margin_v": 60,
        "subtitle_style": "normal",
        "subtitle_outline": 1,
    },
}


def get_video_info(video_path):
    """获取视频信息"""
    cmd = [
        "ffprobe", "-v", "quiet",
        "-print_format", "json",
        "-show_format", "-show_streams",
        video_path,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return json.loads(result.stdout)
    except Exception:
        return None


def get_video_dimensions(info):
    """从 ffprobe 信息中提取宽高"""
    if not info:
        return 0, 0
    for stream in info.get("streams", []):
        if stream.get("codec_type") == "video":
            return stream.get("width", 0), stream.get("height", 0)
    return 0, 0


def build_subtitle_filter(preset, subtitle_path, is_vertical=False):
    """
    构建字幕烧录的 ffmpeg filter
    竖屏模式下使用更大的字体和更粗的描边
    """
    fontsize = preset["subtitle_fontsize"]
    margin_v = preset["subtitle_margin_v"]
    outline = preset["subtitle_outline"]

    # 竖屏模式下字体适当放大
    if is_vertical:
        fontsize = int(fontsize * 1.2)

    # 使用 ASS 字幕样式
    style = (
        f"FontSize={fontsize},"
        f"PrimaryColour=&H00FFFFFF,"  # 白色
        f"OutlineColour=&H00000000,"  # 黑色描边
        f"Outline={outline},"
        f"Shadow=1,"
        f"MarginV={margin_v},"
        f"Alignment=2"  # 底部居中
    )

    return f"subtitles='{subtitle_path}':force_style='{style}'"


def render_for_platform(video_path, subtitle_path, output_path, platform,
                        custom_width=None, custom_height=None):
    """
    为指定平台渲染视频

    参数:
        video_path: 输入视频路径
        subtitle_path: SRT 字幕路径
        output_path: 输出路径
        platform: 平台名称（douyin/youtube/bilibili/wechat/xiaohongshu）
        custom_width: 自定义宽度（覆盖平台预设）
        custom_height: 自定义高度（覆盖平台预设）
    """
    if platform not in PLATFORM_PRESETS:
        print(f"❌ 不支持的平台: {platform}")
        print(f"支持的平台: {', '.join(PLATFORM_PRESETS.keys())}")
        return False

    preset = PLATFORM_PRESETS[platform]
    target_w = custom_width or preset["width"]
    target_h = custom_height or preset["height"]

    print(f"🎬 渲染: {preset['name']} ({target_w}x{target_h})")

    # 获取源视频信息
    info = get_video_info(video_path)
    src_w, src_h = get_video_dimensions(info)
    print(f"   源: {src_w}x{src_h} → 目标: {target_w}x{target_h}")

    is_vertical = target_h > target_w

    # 构建视频滤镜
    filters = []

    # 尺寸适配
    if is_vertical and src_w > src_h:
        # 横屏转竖屏：裁剪中间区域
        # 先缩放到目标高度，再裁剪宽度
        filters.append(
            f"scale=-1:{target_h},crop={target_w}:{target_h}"
        )
    elif not is_vertical and src_h > src_w:
        # 竖屏转横屏：缩放并加黑边
        filters.append(
            f"scale={target_w}:-1,pad={target_w}:{target_h}:(ow-iw)/2:(oh-ih)/2:black"
        )
    else:
        # 同比例，直接缩放
        filters.append(f"scale={target_w}:{target_h}:force_original_aspect_ratio=decrease")
        filters.append(f"pad={target_w}:{target_h}:(ow-iw)/2:(oh-ih)/2:black")

    # 字幕
    if subtitle_path and os.path.exists(subtitle_path):
        sub_filter = build_subtitle_filter(preset, subtitle_path, is_vertical)
        filters.append(sub_filter)

    vf = ",".join(filters)

    # ffmpeg 命令
    cmd = [
        "ffmpeg", "-i", video_path,
        "-vf", vf,
        "-c:v", "libx264", "-preset", "medium", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        "-y", output_path,
    ]

    print(f"   执行渲染...")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0 and os.path.exists(output_path):
        size_mb = os.path.getsize(output_path) / (1024 * 1024)
        print(f"   ✅ 完成: {os.path.basename(output_path)} ({size_mb:.1f}MB)")
        return True
    else:
        print(f"   ❌ 渲染失败")
        if result.stderr:
            print(f"   错误: {result.stderr[-200:]}")
        return False


def main():
    parser = argparse.ArgumentParser(description="平台适配渲染（灵感象限-Ideasphere）")
    parser.add_argument("--input", "-i", required=True, help="输入视频路径")
    parser.add_argument("--subtitle", "-s", default=None, help="SRT 字幕路径")
    parser.add_argument("--output", "-o", required=True, help="输出视频路径")
    parser.add_argument("--platform", "-p", default="douyin",
                        choices=list(PLATFORM_PRESETS.keys()),
                        help="目标平台")
    parser.add_argument("--width", type=int, default=None, help="自定义宽度")
    parser.add_argument("--height", type=int, default=None, help="自定义高度")
    parser.add_argument("--list-platforms", action="store_true", help="列出所有平台预设")

    args = parser.parse_args()

    if args.list_platforms:
        print("📱 支持的平台预设：\n")
        for key, preset in PLATFORM_PRESETS.items():
            print(f"  {key:15s}  {preset['name']:10s}  {preset['width']}x{preset['height']}  ({preset['aspect']})")
        return

    success = render_for_platform(
        args.input, args.subtitle, args.output,
        args.platform, args.width, args.height,
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
