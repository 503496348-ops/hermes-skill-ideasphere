#!/usr/bin/env python3
"""
视频一站式工作流 — 灵感象限-Ideasphere
流程：剪辑 → 拼接 → 转写 → 翻译（可选）→ 烧录 → 平台渲染（可选）
每一步的产出都保留，支持断点续跑（manifest）

作者：AtomCollide-智械工坊团队

依赖检查:
- ffmpeg: 系统视频处理工具
- auto-editor: pip3 install auto-editor --break-system-packages
- faster-whisper: pip3 install faster-whisper requests
- LLM API Key: 环境变量或 --api-key 参数
"""

import os
import argparse
import subprocess
import glob
import shutil
import sys

# 导入 manifest 模块（同目录）
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from manifest import PipelineManifest
    HAS_MANIFEST = True
except ImportError:
    HAS_MANIFEST = False

TARGET = None
ENABLE_NOTIFY = False
VIDEO_EXTS = ['.mp4', '.mov', '.avi', '.mkv', '.flv', '.wmv', '.m4v', '.webm']


def check_deps():
    """检查依赖是否已安装"""
    print("\n" + "="*40)
    print("🔍 检查依赖...")
    print("="*40)

    deps_status = {}

    # 检查 ffmpeg
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg:
        try:
            result = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True)
            version = result.stdout.split("\n")[0] if result.stdout else "unknown"
            print(f"✅ ffmpeg: 已安装 ({version})")
            deps_status["ffmpeg"] = True
        except Exception:
            print("✅ ffmpeg: 已安装")
            deps_status["ffmpeg"] = True
    else:
        print("❌ ffmpeg: 未安装")
        deps_status["ffmpeg"] = False

    # 检查 ffprobe
    ffprobe = shutil.which("ffprobe")
    if ffprobe:
        print("✅ ffprobe: 已安装")
        deps_status["ffprobe"] = True
    else:
        print("❌ ffprobe: 未安装")
        deps_status["ffprobe"] = False

    # 检查 auto-editor
    try:
        result = subprocess.run(["auto-editor", "--version"], capture_output=True, text=True)
        version = result.stdout.strip() or result.stderr.strip() or "unknown"
        print(f"✅ auto-editor: 已安装 ({version})")
        deps_status["auto-editor"] = True
    except Exception:
        print("❌ auto-editor: 未安装")
        deps_status["auto-editor"] = False

    # 检查 faster-whisper
    try:
        import importlib.util
        if importlib.util.find_spec("faster_whisper") is None:
            raise ImportError
        print("✅ faster-whisper: 已安装")
        deps_status["faster-whisper"] = True
    except ImportError:
        print("❌ faster-whisper: 未安装")
        deps_status["faster-whisper"] = False

    # 检查 requests
    try:
        import importlib.util
        if importlib.util.find_spec("requests") is None:
            raise ImportError
        print("✅ requests: 已安装")
        deps_status["requests"] = True
    except ImportError:
        print("❌ requests: 未安装")
        deps_status["requests"] = False

    # 检查 LLM API Key（任一提供商即可）
    has_any_key = False
    for env in ["MINIMAX_API_KEY", "OPENAI_API_KEY", "DEEPSEEK_API_KEY"]:
        if os.environ.get(env):
            print(f"✅ {env}: 已设置")
            has_any_key = True
    if not has_any_key:
        print("❌ LLM API Key: 未设置（需要 MINIMAX_API_KEY / OPENAI_API_KEY / DEEPSEEK_API_KEY 之一）")
    deps_status["LLM_API_KEY"] = has_any_key

    print("="*40)

    # 总结
    all_ok = all(deps_status.values())
    if all_ok:
        print("✅ 所有依赖都已满足！")
    else:
        missing = [k for k, v in deps_status.items() if not v]
        print(f"❌ 缺少依赖: {', '.join(missing)}")
        print("\n请运行以下命令查看安装指南:")
        print("  python3 pipeline.py --install-deps")
        print("\n或手动安装:")
        if not deps_status.get("ffmpeg") or not deps_status.get("ffprobe"):
            print("  Ubuntu/Debian: sudo apt install ffmpeg")
            print("  macOS: brew install ffmpeg")
        if not deps_status.get("auto-editor"):
            print("  pip3 install auto-editor --break-system-packages")
        if not deps_status.get("faster-whisper") or not deps_status.get("requests"):
            print("  pip3 install faster-whisper requests")
        if not deps_status.get("LLM_API_KEY"):
            print("  export MINIMAX_API_KEY='your-api-key'")

    print("="*40)
    return all_ok


def install_deps():
    """自动安装依赖 - 仅显示命令，不自动执行（安全原因）"""
    print("\n" + "="*40)
    print("📦 依赖安装指南")
    print("="*40)
    print("\n请手动执行以下命令安装依赖：\n")

    # 检测系统
    system = ""
    if shutil.which("apt-get"):
        system = "Ubuntu/Debian"
    elif shutil.which("brew"):
        system = "macOS"
    elif shutil.which("yum"):
        system = "CentOS/RHEL"

    print("="*40)
    print(f"检测到系统: {system or '未知'}")
    print("="*40)

    print("\n【系统级依赖】")
    if system == "Ubuntu/Debian":
        print("  sudo apt-get update")
        print("  sudo apt-get install -y ffmpeg")
    elif system == "macOS":
        print("  brew install ffmpeg")
    elif system == "CentOS/RHEL":
        print("  sudo yum install -y ffmpeg")
    else:
        print("  # 请根据您的系统安装 ffmpeg")
        print("  # Ubuntu: sudo apt install ffmpeg")
        print("  # macOS: brew install ffmpeg")
        print("  # Windows: 下载 ffmpeg.exe")

    print("\n【Python 依赖】")
    print("  pip3 install auto-editor")
    print("  pip3 install faster-whisper requests")

    print("\n【可选：GPU 加速】")
    print("  # CUDA 支持（需要 NVIDIA GPU）")
    print("  pip3 install faster-whisper[cuda]")

    print("\n【环境变量】")
    print("  # 方式一: 环境变量")
    print("  export MINIMAX_API_KEY='your-api-key'")
    print("")
    print("  # 方式二: 运行时传入")
    print("  python3 pipeline.py --all -i /path ... --api-key 'your-key'")

    print("\n获取 API Key: https://platform.minimaxi.com/")
    print("="*40)
    return False


ENABLE_NOTIFY = True  # 默认启用通知


def send(msg):
    """发送消息（仅在启用通知且设置了目标时发送）"""
    print(msg)
    if not ENABLE_NOTIFY or not TARGET:
        return
    subprocess.run([
        "openclaw", "send",
        "--message", msg,
        "--channel", "feishu",
        "--target", TARGET
    ], capture_output=True)


def scan_directory(directory):
    videos = []
    if not os.path.exists(directory):
        return videos
    for f in os.listdir(directory):
        ext = os.path.splitext(f)[1].lower()
        if ext in VIDEO_EXTS:
            full_path = os.path.join(directory, f)
            videos.append({"name": f, "path": full_path, "size": os.path.getsize(full_path)})
    return sorted(videos, key=lambda x: x["name"])


def format_size(bytes_size):
    mb = bytes_size / 1024 / 1024
    return f"{mb:.1f}MB"


def run_step1_edit(input_dir, output_dir, manifest=None):
    """步骤1: 剪辑每个子视频"""
    if manifest and manifest.should_skip("clip"):
        send("⏭️ 步骤1: 已完成，跳过")
        return manifest.get_stage_output("clip", "dir") or output_dir

    if manifest:
        manifest.stage_start("clip", {"input": input_dir})

    send("\n" + "="*30)
    send("📹 步骤1: 视频剪辑（去除静音片段）")
    send("="*30)

    videos = scan_directory(input_dir)
    send(f"输入: {input_dir}")
    send(f"找到 {len(videos)} 个视频")

    script_dir = os.path.dirname(os.path.abspath(__file__))
    cmd = f'python3 "{script_dir}/video_clip.py" --input "{input_dir}" --output "{output_dir}" --target "" '
    send("▶️ 开始剪辑...")

    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(result.stdout)
    print(result.stderr)

    edited = scan_directory(output_dir)
    send(f"✅ 剪辑完成！产出 {len(edited)} 个文件:")
    for v in edited:
        send(f"  📄 {v['name']} ({format_size(v['size'])})")

    if manifest:
        manifest.stage_complete("clip", {"dir": output_dir, "count": len(edited)})

    send("\n💡 下一步：执行步骤2（拼接视频)")
    return output_dir


def run_step2_concat(input_dir, output_file, manifest=None):
    """步骤2: 拼接视频"""
    if manifest and manifest.should_skip("concat"):
        send("⏭️ 步骤2: 已完成，跳过")
        return manifest.get_stage_output("concat", "file") or output_file

    if manifest:
        manifest.stage_start("concat", {"input": input_dir})

    send("\n" + "="*30)
    send("🔗 步骤2: 拼接视频")
    send("="*30)

    videos = scan_directory(input_dir)
    send(f"输入: {input_dir}")
    send(f"找到 {len(videos)} 个视频待拼接")

    list_file = "/tmp/concat_list.txt"
    with open(list_file, "w") as f:
        for v in videos:
            f.write(f"file '{v['path']}'\n")

    send("▶️ 开始拼接...")
    cmd = f'ffmpeg -f concat -safe 0 -i "{list_file}" -c copy -y "{output_file}"'
    subprocess.run(cmd, shell=True, capture_output=True, text=True)

    os.remove(list_file)

    if os.path.exists(output_file):
        size = os.path.getsize(output_file)
        send("✅ 拼接完成！")
        send(f"  📄 {os.path.basename(output_file)} ({format_size(size)})")
    else:
        send("❌ 拼接失败")

    if manifest:
        manifest.stage_complete("concat", {"file": output_file})

    send("\n💡 下一步：执行步骤3（转写字幕）")
    return output_file


def run_step3_transcribe(video_path, output_dir, manifest=None):
    """步骤3: 转写（生成字幕）"""
    if manifest and manifest.should_skip("transcribe"):
        send("⏭️ 步骤3: 已完成，跳过")
        return manifest.get_stage_output("transcribe", "dir") or output_dir

    if manifest:
        manifest.stage_start("transcribe", {"video": video_path})

    send("\n" + "="*30)
    send("📝 步骤3: 视频转写（生成字幕）")
    send("="*30)

    video_name = os.path.basename(video_path)
    send(f"输入: {video_name}")

    script_dir = os.path.dirname(os.path.abspath(__file__))
    cmd = f'python3 "{script_dir}/video_to_text.py" --input "{os.path.dirname(video_path)}" --output "{output_dir}" --model small --target "" '
    send("▶️ 开始转写...")

    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(result.stdout)

    subtitles = glob.glob(os.path.join(output_dir, "*.srt"))
    if subtitles:
        send(f"✅ 转写完成！产出 {len(subtitles)} 个字幕文件")
        for s in subtitles:
            send(f"  📄 {os.path.basename(s)}")

    if manifest:
        manifest.stage_complete("transcribe", {"dir": output_dir, "count": len(subtitles)})

    send("\n💡 下一步：执行步骤4（翻译字幕或烧录字幕）")
    return output_dir


def run_step4_translate(subtitle_dir, output_dir, target_lang, bilingual=False,
                        api_key=None, provider=None, manifest=None):
    """步骤4: 翻译字幕（上下文感知）"""
    if manifest and manifest.should_skip("translate"):
        send("⏭️ 步骤4(翻译): 已完成，跳过")
        return manifest.get_stage_output("translate", "dir") or output_dir

    if manifest:
        manifest.stage_start("translate", {"subtitle_dir": subtitle_dir, "target_lang": target_lang})

    send("\n" + "="*30)
    send(f"🌍 步骤4: 字幕翻译 → {target_lang}")
    send("="*30)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    cmd_parts = [
        'python3', f'"{script_dir}/translate_subtitle.py"',
        '--input', f'"{subtitle_dir}"',
        '--output', f'"{output_dir}"',
        '--target-lang', f'"{target_lang}"',
    ]
    if bilingual:
        cmd_parts.append('--bilingual')
    if api_key:
        cmd_parts.extend(['--api-key', f'"{api_key}"'])
    if provider:
        cmd_parts.extend(['--provider', provider])

    cmd = ' '.join(cmd_parts)
    send("▶️ 开始翻译...")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print(result.stderr)

    translated = glob.glob(os.path.join(output_dir, "*.srt"))
    send(f"✅ 翻译完成！产出 {len(translated)} 个字幕文件")

    if manifest:
        manifest.stage_complete("translate", {"dir": output_dir, "count": len(translated)})

    return output_dir


def run_step5_burn(video_dir, subtitle_dir, output_dir, manifest=None):
    """步骤5: 烧录字幕"""
    if manifest and manifest.should_skip("burn"):
        send("⏭️ 步骤5: 已完成，跳过")
        return

    if manifest:
        manifest.stage_start("burn", {"video_dir": video_dir, "subtitle_dir": subtitle_dir})

    send("\n" + "="*30)
    send("🔥 步骤5: 烧录字幕进视频")
    send("="*30)

    videos = scan_directory(video_dir)
    subtitles = glob.glob(os.path.join(subtitle_dir, "*.srt"))

    send(f"视频: {len(videos)} 个")
    send(f"字幕: {len(subtitles)} 个")

    send("▶️ 开始烧录...")

    burned_count = 0
    # 对拼接后的视频烧录字幕
    for v in videos:
        if "合并" in v["name"] or "已烧录" in v["name"]:
            continue

        base_name = os.path.splitext(v["name"])[0]
        for suffix in ["_已剪辑", "_已剪除冗余片段"]:
            if base_name.endswith(suffix):
                base_name = base_name[:-len(suffix)]

        subtitle_file = None
        for s in subtitles:
            if base_name in s or os.path.splitext(os.path.basename(s))[0] in v["name"]:
                subtitle_file = s
                break

        if not subtitle_file:
            send(f"⚠️ 找不到字幕: {v['name']}")
            continue

        output_name = v["name"].replace(".mp4", "_已烧录字幕.mp4")
        output_path = os.path.join(output_dir, output_name)

        cmd = f'ffmpeg -i "{v["path"]}" -vf "subtitles=\'{subtitle_file}\'" -c:a copy -y "{output_path}"'
        subprocess.run(cmd, shell=True, capture_output=True, text=True)

        if os.path.exists(output_path):
            send(f"✅ 完成: {output_name}")
            burned_count += 1

    # 也对合并后的视频烧录
    merged_videos = [v for v in videos if "合并" in v["name"]]
    for v in merged_videos:
        if subtitles:
            subtitle_file = subtitles[0]
            output_name = v["name"].replace(".mp4", "_已烧录字幕.mp4")
            output_path = os.path.join(output_dir, output_name)

            cmd = f'ffmpeg -i "{v["path"]}" -vf "subtitles=\'{subtitle_file}\'" -c:a copy -y "{output_path}"'
            subprocess.run(cmd, shell=True, capture_output=True, text=True)

            if os.path.exists(output_path):
                send(f"✅ 完成: {output_name}")
                burned_count += 1

    if manifest:
        manifest.stage_complete("burn", {"count": burned_count})

    send("\n" + "="*30)
    send("🎉 全部流程完成！")
    send("="*30)
    send("💡 每一步的产出都已保留，可以查看")


def run_step6_render(input_dir, output_dir, platform, subtitle_dir=None, manifest=None):
    """步骤6: 平台适配渲染（可选）"""
    if manifest and manifest.should_skip("export"):
        send("⏭️ 步骤6: 已完成，跳过")
        return

    if manifest:
        manifest.stage_start("export", {"platform": platform})

    send("\n" + "="*30)
    send(f"📱 步骤6: 平台适配渲染 ({platform})")
    send("="*30)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(output_dir, exist_ok=True)

    videos = scan_directory(input_dir)
    subtitles = glob.glob(os.path.join(subtitle_dir, "*.srt")) if subtitle_dir else []

    exported_count = 0
    for v in videos:
        if "已烧录" not in v["name"] and "合并" not in v["name"]:
            continue

        base_name = os.path.splitext(v["name"])[0]
        subtitle_file = None
        for s in subtitles:
            if base_name[:10] in os.path.basename(s):
                subtitle_file = s
                break

        output_name = f"{platform}_{v['name']}"
        output_path = os.path.join(output_dir, output_name)

        cmd_parts = [
            'python3', f'"{script_dir}/platform_render.py"',
            '--input', f'"{v["path"]}"',
            '--output', f'"{output_path}"',
            '--platform', platform,
        ]
        if subtitle_file:
            cmd_parts.extend(['--subtitle', f'"{subtitle_file}"'])

        cmd = ' '.join(cmd_parts)
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        print(result.stdout)

        if os.path.exists(output_path):
            exported_count += 1

    if manifest:
        manifest.stage_complete("export", {"platform": platform, "count": exported_count})

    send(f"✅ 平台渲染完成！导出 {exported_count} 个视频")


def main():
    global TARGET

    parser = argparse.ArgumentParser(description="视频一站式工作流 — 灵感象限-Ideasphere")
    parser.add_argument("--input", "-i", help="输入目录（原始视频）")
    parser.add_argument("--output", "-o", default=None, help="输出目录")
    parser.add_argument("--target", "-t", default=None, help="通知目标")
    parser.add_argument("--step", "-s", type=int, choices=[1, 2, 3, 4, 5, 6], help="执行哪一步")
    parser.add_argument("--all", "-a", action="store_true", help="执行全量流程")
    parser.add_argument("--list", "-l", action="store_true", help="列出视频")
    parser.add_argument("--check-deps", action="store_true", help="检查依赖是否满足")
    parser.add_argument("--install-deps", action="store_true", help="显示依赖安装指南")
    parser.add_argument("--api-key", "-k", default=None, help="LLM API Key")
    parser.add_argument("--notify", "-n", default="true", help="是否发送通知 (true/false, 默认true)")

    # 新增：翻译参数
    parser.add_argument("--target-lang", default=None, help="目标语言（如: 中文, English）— 触发翻译步骤")
    parser.add_argument("--bilingual", "-b", action="store_true", help="生成双语字幕")
    parser.add_argument("--provider", "-p", default=None, help="LLM 提供商 (minimax/openai/deepseek)")

    # 新增：平台渲染参数
    parser.add_argument("--platform", default=None,
                        choices=["douyin", "wechat", "xiaohongshu", "youtube", "bilibili"],
                        help="目标平台 — 触发平台适配渲染")

    # 新增：manifest 参数
    parser.add_argument("--manifest-status", action="store_true", help="查看流水线状态")
    parser.add_argument("--reset", action="store_true", help="重置流水线状态")

    args = parser.parse_args()

    # 解析通知设置
    global ENABLE_NOTIFY
    ENABLE_NOTIFY = args.notify.lower() == "true" and args.target

    # 检查依赖或安装依赖
    if args.check_deps:
        check_deps()
        return

    if args.install_deps:
        install_deps()
        return

    if not args.input:
        parser.print_help()
        print("\n示例:")
        print("  python3 pipeline.py --check-deps          # 检查依赖")
        print("  python3 pipeline.py --install-deps        # 查看安装指南")
        print("  python3 pipeline.py --list -i /path/to/videos")
        print("  python3 pipeline.py --all -i /path/in -o /path/out")
        print("  python3 pipeline.py --all -i /path/in -o /path/out --target-lang English --bilingual")
        print("  python3 pipeline.py --all -i /path/in -o /path/out --platform douyin")
        return

    TARGET = args.target or os.environ.get("OPENCLAW_TARGET")

    # 设置通知开关
    notify_setting = args.notify.lower()
    if notify_setting == "false":
        print("ℹ️ 通知已禁用 (--notify false)")
    elif TARGET:
        print(f"ℹ️ 通知目标: {TARGET}")
    else:
        print("ℹ️ 未设置 --target，通知将仅显示在控制台")

    # 设置 API Key（支持多提供商）
    if args.api_key:
        os.environ["MINIMAX_API_KEY"] = args.api_key
    elif not any(os.environ.get(k) for k in ["MINIMAX_API_KEY", "OPENAI_API_KEY", "DEEPSEEK_API_KEY"]):
        print("⚠️ 警告: 未设置 LLM API Key，转写和翻译功能可能无法使用")
        print("   设置方式: export MINIMAX_API_KEY='your-key' 或使用 --api-key 参数")

    if args.list:
        videos = scan_directory(args.input)
        send(f"📁 {args.input}")
        send(f"找到 {len(videos)} 个视频:")
        for v in videos:
            send(f"  📄 {v['name']} ({format_size(v['size'])})")
        return

    if not args.output:
        args.output = args.input

    base_dir = args.output

    # 初始化 manifest
    manifest = None
    if HAS_MANIFEST:
        manifest = PipelineManifest(base_dir)
        if args.manifest_status:
            print(manifest.summary())
            return
        if args.reset:
            if os.path.exists(manifest.manifest_path):
                os.remove(manifest.manifest_path)
                print("✅ Manifest 已重置")
            return

    # 目录结构
    edited_dir = os.path.join(base_dir, "1_已剪辑")
    concat_dir = os.path.join(base_dir, "2_已拼接")
    subtitle_dir = os.path.join(base_dir, "3_文字稿")
    translated_dir = os.path.join(base_dir, "4_已翻译")
    final_dir = os.path.join(base_dir, "5_已烧录")
    export_dir = os.path.join(base_dir, "6_平台导出")

    # 创建目录
    dirs = [edited_dir, concat_dir, subtitle_dir, final_dir]
    if args.target_lang:
        dirs.append(translated_dir)
    if args.platform:
        dirs.append(export_dir)
    for d in dirs:
        os.makedirs(d, exist_ok=True)

    send("="*40)
    send("🎬 视频一站式工作流 — 灵感象限-Ideasphere")
    send("="*40)
    send(f"输入: {args.input}")
    send(f"输出: {base_dir}")
    send("")
    send("目录结构:")
    send(f"  1_已剪辑  → {os.path.basename(edited_dir)}")
    send(f"  2_已拼接  → {os.path.basename(concat_dir)}")
    send(f"  3_文字稿 → {os.path.basename(subtitle_dir)}")
    if args.target_lang:
        send(f"  4_已翻译 → {os.path.basename(translated_dir)}")
    send(f"  {'5' if args.target_lang else '4'}_已烧录 → {os.path.basename(final_dir)}")
    if args.platform:
        send(f"  6_平台导出 → {os.path.basename(export_dir)}")
    send("="*40)

    # 执行步骤
    if args.all or args.step == 1:
        edited_dir = run_step1_edit(args.input, edited_dir, manifest)

    if args.all or args.step == 2:
        concat_file = os.path.join(concat_dir, "合并视频.mp4")
        run_step2_concat(edited_dir, concat_file, manifest)

    if args.all or args.step == 3:
        concat_file = os.path.join(concat_dir, "合并视频.mp4")
        if os.path.exists(concat_file):
            run_step3_transcribe(concat_file, subtitle_dir, manifest)
        else:
            send("⚠️ 找不到拼接后的视频，跳过转写")

    # 步骤4: 翻译（可选，需要 --target-lang）
    if args.target_lang and (args.all or args.step == 4):
        api_key = args.api_key or os.environ.get("MINIMAX_API_KEY") or os.environ.get("OPENAI_API_KEY")
        run_step4_translate(subtitle_dir, translated_dir, args.target_lang,
                            args.bilingual, api_key, args.provider, manifest)
        # 翻译后的字幕目录用于烧录
        burn_subtitle_dir = translated_dir
    else:
        burn_subtitle_dir = subtitle_dir

    # 步骤5: 烧录
    burn_step = 5 if args.target_lang else 4
    if args.all or args.step == burn_step:
        run_step5_burn(concat_dir, burn_subtitle_dir, final_dir, manifest)

    # 步骤6: 平台渲染（可选，需要 --platform）
    if args.platform and (args.all or args.step == 6):
        run_step6_render(final_dir, export_dir, args.platform, burn_subtitle_dir, manifest)

    # 输出 manifest 摘要
    if manifest:
        send("\n" + manifest.summary())


if __name__ == "__main__":
    main()
