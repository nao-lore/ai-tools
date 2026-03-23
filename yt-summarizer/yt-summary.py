#!/usr/bin/env python3
"""YouTube動画の字幕を取得してClaudeで要約するツール"""

import argparse
import re
import sys

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter
import anthropic


def extract_video_id(url_or_id: str) -> str:
    """URLまたはIDからvideo IDを抽出"""
    patterns = [
        r'(?:v=|/v/|youtu\.be/)([a-zA-Z0-9_-]{11})',
        r'^([a-zA-Z0-9_-]{11})$',
    ]
    for pattern in patterns:
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)
    print(f"エラー: 動画IDを認識できません: {url_or_id}", file=sys.stderr)
    sys.exit(1)


def get_transcript(video_id: str) -> str:
    """字幕テキストを取得（日本語優先、なければ英語、なければ自動生成）"""
    ytt_api = YouTubeTranscriptApi()
    transcript = ytt_api.fetch(video_id, languages=["ja", "en"])
    formatter = TextFormatter()
    return formatter.format_transcript(transcript)


def summarize(text: str, lang: str = "ja", detail: str = "normal") -> str:
    """Claudeで要約"""
    client = anthropic.Anthropic()

    if detail == "detailed":
        instruction = (
            "以下はYouTube動画の字幕テキストです。\n"
            "この動画の内容を詳細にまとめてください。\n"
            "- まず動画の概要を2-3文で\n"
            "- 主要なポイントを箇条書きで（各ポイントの説明付き）\n"
            "- 重要な具体例やデータがあれば含める\n"
            "- 結論やアクションアイテムがあればまとめる"
        )
    elif detail == "brief":
        instruction = (
            "以下はYouTube動画の字幕テキストです。\n"
            "3-5文で簡潔に要約してください。"
        )
    else:
        instruction = (
            "以下はYouTube動画の字幕テキストです。\n"
            "この動画の内容をわかりやすくまとめてください。\n"
            "- まず1文で概要\n"
            "- 主要なポイントを箇条書き\n"
            "- 重要な結論があればまとめる"
        )

    if lang == "en":
        instruction = instruction.replace("以下はYouTube動画の字幕テキストです。", "Below is a YouTube video transcript.")
        instruction = instruction.replace("この動画の内容をわかりやすくまとめてください。", "Summarize this video clearly.")
        instruction = instruction.replace("まず1文で概要", "One-sentence overview first")
        instruction = instruction.replace("主要なポイントを箇条書き", "Key points as bullet points")
        instruction = instruction.replace("重要な結論があればまとめる", "Include important conclusions")

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        messages=[
            {"role": "user", "content": f"{instruction}\n\n---\n{text}"}
        ],
    )
    return message.content[0].text


def main():
    parser = argparse.ArgumentParser(
        description="YouTube動画を要約するツール",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "使用例:\n"
            "  yt-summary https://www.youtube.com/watch?v=xxxxx\n"
            "  yt-summary xxxxx --detail detailed\n"
            "  yt-summary xxxxx --detail brief\n"
            "  yt-summary xxxxx --raw  # 字幕テキストのみ出力\n"
        ),
    )
    parser.add_argument("url", help="YouTube動画のURLまたはID")
    parser.add_argument("--detail", choices=["brief", "normal", "detailed"], default="normal",
                        help="要約の詳細度 (default: normal)")
    parser.add_argument("--lang", choices=["ja", "en"], default="ja",
                        help="要約の出力言語 (default: ja)")
    parser.add_argument("--raw", action="store_true",
                        help="要約せず字幕テキストのみ出力")
    args = parser.parse_args()

    video_id = extract_video_id(args.url)
    print(f"動画ID: {video_id}", file=sys.stderr)

    print("字幕を取得中...", file=sys.stderr)
    transcript = get_transcript(video_id)

    if args.raw:
        print(transcript)
        return

    char_count = len(transcript)
    print(f"字幕取得完了 ({char_count:,}文字)", file=sys.stderr)
    print("要約中...", file=sys.stderr)

    summary = summarize(transcript, lang=args.lang, detail=args.detail)
    print()
    print(summary)


if __name__ == "__main__":
    main()
