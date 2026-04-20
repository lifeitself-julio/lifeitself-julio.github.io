#!/usr/bin/env python3
"""
日記・断章テキストをClaude APIで分析してYAMLタグを出力するスクリプト

使い方:
    python tag_diary.py ~/path/to/file.txt

依存パッケージ:
    pip install anthropic pyyaml pydantic
"""

import sys
import argparse
from pathlib import Path
from typing import Literal

import yaml
import anthropic
from pydantic import BaseModel, field_validator


# --- 出力スキーマ定義 ---

class ZineCandidate(BaseModel):
    name: Literal["Memories", "Language", "Papa", "未分類"]
    confidence: Literal["高", "中", "低"]


class DiaryAnalysis(BaseModel):
    zine_candidate: ZineCandidate
    themes: list[str]
    has_quote: bool
    quotes: list[str]
    draft_status: Literal["断片", "下書き", "ほぼ完成"]
    publish: bool
    memo: str

    @field_validator("themes")
    @classmethod
    def limit_themes(cls, v: list[str]) -> list[str]:
        return v[:5]


# --- プロンプト ---

SYSTEM_PROMPT = """\
あなたはZINE編集者のアシスタントです。日記や断章テキストを分析し、
ZINEプロジェクトへの適性を評価します。

## ZINEシリーズの概要
- Memories: 記憶・過去・回想に関するテキスト（幼少期の場面、懐かしさ、失われたもの）
- Language: 言語・文章・書くこと自体についての考察（翻訳、母語、文体への意識）
- Papa: 父親・家族・世代間の関係性に関するテキスト（父の言動、継承、距離感）
- 未分類: 上記いずれにも明確に属さないもの

## 分析の観点
- テキストの主題・感情・文体を丁寧に読み取る
- テーマはそのテキストを象徴するキーワードを5つ以内で選ぶ
- 引用とは「」や"" で囲まれた言葉、または明らかに他者の言葉を引いている箇所
- 完成度: 「断片」=断片的で文章としてまとまっていない、「下書き」=粗削りだが骨格がある、「ほぼ完成」=推敲が行き届いている
- 公開推奨: 内容のデリカシー・完成度・読者への訴求力を総合判断（true=推奨、false=再検討）
- 編集メモ: どの章・他のテキストと接続できるか、編集上の気づきを簡潔に記述
""".strip()


# --- 分析処理 ---

def analyze_file(file_path: Path) -> dict:
    text = file_path.read_text(encoding="utf-8")

    if not text.strip():
        print(f"Error: File is empty: {file_path}", file=sys.stderr)
        sys.exit(1)

    client = anthropic.Anthropic()

    response = client.messages.parse(
        model="claude-opus-4-7",
        max_tokens=1024,
        system=[
            {
                "type": "text",
                "text": SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[
            {
                "role": "user",
                "content": (
                    f"以下のテキストを分析してください。\n\n"
                    f"ファイル名: {file_path.name}\n\n"
                    f"---\n{text}\n---"
                ),
            }
        ],
        output_format=DiaryAnalysis,
    )

    result = response.parsed_output
    if result is None:
        print("Error: Claude returned an unexpected response format.", file=sys.stderr)
        sys.exit(1)

    return {
        "zine_candidate": {
            "name": result.zine_candidate.name,
            "confidence": result.zine_candidate.confidence,
        },
        "themes": result.themes,
        "has_quote": result.has_quote,
        "quotes": result.quotes if result.has_quote else [],
        "draft_status": result.draft_status,
        "publish": result.publish,
        "memo": result.memo,
    }


# --- エントリポイント ---

def main() -> None:
    parser = argparse.ArgumentParser(
        description="日記テキストをClaude APIで分析してYAMLタグを出力する",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="例: python tag_diary.py ~/Documents/diary/2024-01.txt",
    )
    parser.add_argument("file", help="分析するtxtファイルのパス")
    args = parser.parse_args()

    file_path = Path(args.file).expanduser().resolve()

    if not file_path.exists():
        print(f"Error: ファイルが見つかりません: {file_path}", file=sys.stderr)
        sys.exit(1)

    if not file_path.is_file():
        print(f"Error: ファイルではありません: {file_path}", file=sys.stderr)
        sys.exit(1)

    result = analyze_file(file_path)

    print(yaml.dump(
        result,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
        width=80,
    ), end="")


if __name__ == "__main__":
    main()
