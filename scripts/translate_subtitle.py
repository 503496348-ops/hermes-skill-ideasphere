#!/usr/bin/env python3
"""
字幕翻译模块（灵感象限-Ideasphere）
功能：将 SRT 字幕翻译为目标语言，支持双语字幕输出
参考 KrillinAI 的上下文感知翻译策略：翻译时提供前后各3句作为上下文

作者：AtomCollide-智械工坊团队
"""

import os
import re
import sys
import json
import argparse
import time

# ── OpenAI-compatible LLM 客户端 ──────────────────────────────────────────────
# 统一使用 OpenAI API 规范，兼容 MiniMax / OpenAI / DeepSeek / 通义千问 等

DEFAULT_LLM_CONFIG = {
    "base_url": os.environ.get("LLM_BASE_URL", "https://api.minimaxi.com/anthropic"),
    "api_key_env": "MINIMAX_API_KEY",
    "model": os.environ.get("LLM_MODEL", "MiniMax-M2.5"),
}

# 简易 provider 快捷配置
PROVIDER_PRESETS = {
    "minimax": {
        "base_url": "https://api.minimaxi.com/anthropic",
        "api_key_env": "MINIMAX_API_KEY",
        "model": "MiniMax-M2.5",
    },
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "api_key_env": "OPENAI_API_KEY",
        "model": "gpt-4o-mini",
    },
    "deepseek": {
        "base_url": "https://api.deepseek.com/v1",
        "api_key_env": "DEEPSEEK_API_KEY",
        "model": "deepseek-chat",
    },
}

# ── SRT 解析 ──────────────────────────────────────────────────────────────────

def parse_srt(srt_path):
    """解析 SRT 文件，返回字幕块列表 [{index, start, end, text}]"""
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
        blocks.append({
            "index": int(m.group(1)),
            "start": m.group(2),
            "end": m.group(3),
            "text": m.group(4).strip(),
        })
    return blocks


def write_srt(blocks, path):
    """将字幕块列表写入 SRT 文件"""
    with open(path, "w", encoding="utf-8") as f:
        for b in blocks:
            f.write(f"{b['index']}\n{b['start']} --> {b['end']}\n{b['text']}\n\n")


def write_bilingual_srt(blocks, path):
    """写入双语字幕 SRT（原文 + 译文）"""
    with open(path, "w", encoding="utf-8") as f:
        for b in blocks:
            translated = b.get("translated", "")
            bilingual_text = b["text"]
            if translated and translated != b["text"]:
                bilingual_text = f"{b['text']}\n{translated}"
            f.write(f"{b['index']}\n{b['start']} --> {b['end']}\n{bilingual_text}\n\n")


# ── 上下文感知翻译（参考 KrillinAI 策略）──────────────────────────────────────

def build_translation_prompt(text, context_before, context_after, target_lang):
    """
    构建带上下文的翻译 prompt，参考 KrillinAI 的 SplitTextWithContextPrompt
    提供前后各3句上下文，确保翻译连贯
    """
    prompt = f"""You are a professional video subtitle translator. Translate the following text into {target_lang}.

IMPORTANT RULES:
1. Translate naturally and fluently — subtitles are meant to be read quickly
2. Keep proper nouns (names, brands, technical terms) in their original form unless there is a well-known translation
3. Maintain the tone and style of the original
4. Return ONLY the translated text, no explanations

CONTEXT (for reference only, do NOT translate these):"""

    if context_before:
        prompt += f"\n\nPrevious sentences:\n{context_before}"

    prompt += f"\n\nTEXT TO TRANSLATE:\n{text}"

    if context_after:
        prompt += f"\n\nFollowing sentences:\n{context_after}"

    prompt += f"\n\nTranslated {target_lang} text:"
    return prompt


def translate_with_retry(prompt, api_key, config, max_retries=3):
    """带重试的 LLM 翻译调用"""
    import requests

    url = f"{config['base_url']}/messages"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": config["model"],
        "max_tokens": 4096,
        "messages": [{"role": "user", "content": prompt}],
    }

    for attempt in range(max_retries):
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=120)
            result = resp.json()

            # 兼容 Anthropic 格式
            if "content" in result:
                for c in result["content"]:
                    if c.get("type") == "text":
                        return c["text"].strip()

            # 兼容 OpenAI 格式
            if "choices" in result and result["choices"]:
                return result["choices"][0]["message"]["content"].strip()

            # 其他格式
            if "text" in result:
                return result["text"].strip()

        except Exception as e:
            print(f"  ⚠️ 翻译请求失败 (尝试 {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)

    return None


def is_translation_valid(origin, translated):
    """检查翻译质量（参考 KrillinAI 的 isTranslationValid）"""
    if not translated or not translated.strip():
        return False
    # 翻译不能和原文完全相同（除非是数字/专有名词等）
    if origin.strip() == translated.strip():
        # 检查是否主要是数字或符号
        alpha_count = sum(1 for c in origin if c.isalpha())
        if alpha_count > 3:
            return False
    return True


def recursive_split_sentence(sentence, max_length=80, depth=0, max_depth=3):
    """
    递归拆分长句，确保每句不超过 max_length 字符
    参考 KrillinAI 的 recursiveSplitSentence 策略
    """
    if len(sentence) <= max_length or depth >= max_depth:
        return [sentence]

    # 尝试在标点符号处分割
    split_points = []
    for i, ch in enumerate(sentence):
        if ch in "。！？.!?,;；，、":
            split_points.append(i)

    if not split_points:
        # 没有标点，尝试在空格或中间位置分割
        mid = len(sentence) // 2
        return [sentence[:mid], sentence[mid:]]

    # 选择最接近中间的分割点
    mid = len(sentence) // 2
    best = min(split_points, key=lambda x: abs(x - mid))

    left = sentence[: best + 1].strip()
    right = sentence[best + 1 :].strip()

    parts = []
    if left:
        parts.extend(recursive_split_sentence(left, max_length, depth + 1, max_depth))
    if right:
        parts.extend(recursive_split_sentence(right, max_length, depth + 1, max_depth))
    return parts


# ── 批量翻译（带上下文）──────────────────────────────────────────────────────

def translate_srt_blocks(blocks, target_lang, api_key, config, context_size=3):
    """
    批量翻译 SRT 字幕块，每句翻译时提供前后各 context_size 句作为上下文
    """
    import requests  # noqa: F811

    total = len(blocks)
    print(f"🌍 开始翻译 {total} 条字幕 → {target_lang}")
    print(f"   上文窗口: {context_size} 句 | 翻译策略: 上下文感知")

    translated_count = 0
    failed_count = 0

    for i, block in enumerate(blocks):
        text = block["text"]
        if not text.strip():
            block["translated"] = ""
            continue

        # 构建上下文
        ctx_before = "\n".join(
            b["text"]
            for b in blocks[max(0, i - context_size) : i]
            if b["text"].strip()
        )
        ctx_after = "\n".join(
            b["text"]
            for b in blocks[i + 1 : i + 1 + context_size]
            if b["text"].strip()
        )

        prompt = build_translation_prompt(text, ctx_before, ctx_after, target_lang)
        translated = translate_with_retry(prompt, api_key, config)

        if translated and is_translation_valid(text, translated):
            block["translated"] = translated
            translated_count += 1
        else:
            # 翻译失败或质量不合格，保留原文
            block["translated"] = text
            failed_count += 1
            if translated:
                print(f"  ⚠️ 质量检查未通过 #{block['index']}: '{text[:30]}...'")

        # 进度
        if (i + 1) % 20 == 0 or i + 1 == total:
            print(f"  📊 进度: {i + 1}/{total} (✅{translated_count} ❌{failed_count})")

        # 简单限速，避免触发 API 频率限制
        time.sleep(0.3)

    print(f"\n✅ 翻译完成: {translated_count} 成功, {failed_count} 降级为原文")
    return blocks


# ── 主流程 ────────────────────────────────────────────────────────────────────

def get_llm_config(provider=None, base_url=None, api_key=None, model=None):
    """获取 LLM 配置，支持 provider 快捷方式或自定义参数"""
    if provider and provider in PROVIDER_PRESETS:
        config = PROVIDER_PRESETS[provider].copy()
    else:
        config = DEFAULT_LLM_CONFIG.copy()

    if base_url:
        config["base_url"] = base_url
    if model:
        config["model"] = model

    # 获取 API Key
    if not api_key:
        api_key = os.environ.get(config["api_key_env"])
    if not api_key:
        print(f"❌ 未找到 API Key，请设置环境变量 {config['api_key_env']} 或使用 --api-key 参数")
        return None, None

    return config, api_key


def main():
    parser = argparse.ArgumentParser(description="SRT 字幕翻译（灵感象限-Ideasphere）")
    parser.add_argument("--input", "-i", required=True, help="输入 SRT 文件路径")
    parser.add_argument("--output", "-o", default=None, help="输出目录（默认同输入目录）")
    parser.add_argument("--target-lang", "-t", default="中文", help="目标语言（如: 中文, English, 日本語）")
    parser.add_argument("--origin-lang", default=None, help="源语言（可选，默认自动检测）")
    parser.add_argument("--bilingual", "-b", action="store_true", help="同时生成双语字幕")
    parser.add_argument("--provider", "-p", default=None, choices=list(PROVIDER_PRESETS.keys()),
                        help="LLM 提供商快捷方式")
    parser.add_argument("--base-url", default=None, help="LLM API 基础 URL")
    parser.add_argument("--api-key", "-k", default=None, help="LLM API Key")
    parser.add_argument("--model", "-m", default=None, help="LLM 模型名称")
    parser.add_argument("--context-size", type=int, default=3, help="上下文句子数量（默认3）")

    args = parser.parse_args()

    # 解析输入
    srt_files = []
    if os.path.isdir(args.input):
        for f in sorted(os.listdir(args.input)):
            if f.endswith(".srt"):
                srt_files.append(os.path.join(args.input, f))
    elif os.path.isfile(args.input):
        srt_files.append(args.input)
    else:
        print(f"❌ 输入不存在: {args.input}")
        sys.exit(1)

    if not srt_files:
        print("❌ 未找到 SRT 文件")
        sys.exit(1)

    # 获取 LLM 配置
    config, api_key = get_llm_config(args.provider, args.base_url, args.api_key, args.model)
    if not config:
        sys.exit(1)

    # 输出目录
    output_dir = args.output or os.path.dirname(srt_files[0])
    os.makedirs(output_dir, exist_ok=True)

    # 语言名称映射
    lang_suffix_map = {
        "中文": "zh", "zh": "zh", "chinese": "zh",
        "english": "en", "en": "en", "英文": "en",
        "日本語": "ja", "ja": "ja", "日语": "ja", "japanese": "ja",
        "한국어": "ko", "ko": "ko", "韩语": "ko", "korean": "ko",
    }
    lang_code = lang_suffix_map.get(args.target_lang.lower(), args.target_lang[:2].lower())

    print(f"=" * 50)
    print(f"🌍 字幕翻译（灵感象限-Ideasphere）")
    print(f"=" * 50)
    print(f"输入: {len(srt_files)} 个 SRT 文件")
    print(f"目标语言: {args.target_lang} ({lang_code})")
    print(f"LLM: {config['model']} @ {config['base_url'][:40]}...")
    print(f"双语输出: {'是' if args.bilingual else '否'}")
    print(f"=" * 50)

    for srt_path in srt_files:
        basename = os.path.splitext(os.path.basename(srt_path))[0]
        print(f"\n📄 处理: {basename}.srt")

        # 解析 SRT
        blocks = parse_srt(srt_path)
        if not blocks:
            print(f"  ⚠️ 无法解析 SRT 文件，跳过")
            continue
        print(f"  📝 共 {len(blocks)} 条字幕")

        # 翻译
        blocks = translate_srt_blocks(
            blocks, args.target_lang, api_key, config, args.context_size
        )

        # 输出翻译后的 SRT
        translated_srt = os.path.join(output_dir, f"{basename}_{lang_code}.srt")
        write_srt(
            [{"index": b["index"], "start": b["start"], "end": b["end"],
              "text": b.get("translated", b["text"])} for b in blocks],
            translated_srt,
        )
        print(f"  ✅ 翻译字幕: {os.path.basename(translated_srt)}")

        # 输出双语 SRT
        if args.bilingual:
            bilingual_srt = os.path.join(output_dir, f"{basename}_bilingual_{lang_code}.srt")
            write_bilingual_srt(blocks, bilingual_srt)
            print(f"  ✅ 双语字幕: {os.path.basename(bilingual_srt)}")

    print(f"\n🎉 翻译全部完成！输出目录: {output_dir}")


if __name__ == "__main__":
    main()
