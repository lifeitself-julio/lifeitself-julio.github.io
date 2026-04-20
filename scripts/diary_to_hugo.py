#!/usr/bin/env python3
"""
日記txtとタグYAMLをHugo markdownに変換してgit pushするスクリプト

使い方:
    # YAMLファイルを渡す
    python diary_to_hugo.py ~/diary.txt tags.yaml

    # YAML文字列を直接渡す
    python diary_to_hugo.py ~/diary.txt "$(cat tags.yaml)"

    # pushしない
    python diary_to_hugo.py ~/diary.txt tags.yaml --no-push

依存パッケージ:
    pip install pyyaml
"""

import sys
import re
import subprocess
import argparse
from pathlib import Path
from datetime import datetime

import yaml


POSTS_DIR = Path("~/Documents/lifeitself/content/posts").expanduser()
REPO_DIR  = Path("~/Documents/lifeitself").expanduser()


# --- テキスト処理 ---

def parse_date(text: str) -> datetime:
    """テキスト先頭行から日付を抽出する（例: # 2026/04/15）。"""
    first_line = text.strip().splitlines()[0]
    match = re.search(r"(\d{4})[/\-](\d{1,2})[/\-](\d{1,2})", first_line)
    if not match:
        raise ValueError(f"日付が読み取れませんでした: {first_line!r}")
    return datetime(int(match.group(1)), int(match.group(2)), int(match.group(3)))


def strip_date_line(text: str) -> str:
    """先頭の日付見出し行を除いた本文を返す。"""
    lines = text.strip().splitlines()
    if lines and re.match(r"^#\s*\d{4}[/\-]", lines[0]):
        lines = lines[1:]
    return "\n".join(lines).strip()


# --- front matter 構築 ---

def build_front_matter(date: datetime, tags: dict) -> dict:
    zine_name = tags.get("zine_candidate", {}).get("name", "未分類")
    themes    = tags.get("themes", [])
    publish   = tags.get("publish", False)
    memo      = tags.get("memo", "").strip()

    return {
        "title":      f"{date.year}年{date.month}月{date.day}日",
        "date":       date.strftime("%Y-%m-%dT00:00:00+09:00"),
        "draft":      not publish,
        "tags":       themes[:5],
        "categories": [zine_name],
        "memo":       memo,
    }


def to_markdown(front_matter: dict, body: str) -> str:
    fm = yaml.dump(
        front_matter,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
        width=120,
    ).strip()
    return f"---\n{fm}\n---\n\n{body}\n"


# --- git 操作 ---

def git_add_commit_push(file_path: Path, date: datetime, push: bool) -> None:
    label = date.strftime("%Y-%m-%d")

    subprocess.run(["git", "add", str(file_path)], cwd=REPO_DIR, check=True)
    subprocess.run(
        ["git", "commit", "-m", f"Add diary post {label}"],
        cwd=REPO_DIR, check=True,
    )
    if push:
        subprocess.run(["git", "push", "origin", "main"], cwd=REPO_DIR, check=True)


# --- エントリポイント ---

def main() -> None:
    parser = argparse.ArgumentParser(
        description="日記txtとタグYAMLをHugo markdownに変換してgit pushする",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='例: python diary_to_hugo.py diary.txt tags.yaml',
    )
    parser.add_argument("txt_file",   help="日記txtファイルのパス")
    parser.add_argument("yaml_input", help="タグYAML（ファイルパスまたはYAML文字列）")
    parser.add_argument("--no-push",  action="store_true", help="git pushをスキップする")
    args = parser.parse_args()

    # txtファイル読み込み
    txt_path = Path(args.txt_file).expanduser().resolve()
    if not txt_path.is_file():
        print(f"Error: ファイルが見つかりません: {txt_path}", file=sys.stderr)
        sys.exit(1)
    text = txt_path.read_text(encoding="utf-8")

    # YAML読み込み（ファイルパスまたは文字列）
    yaml_candidate = Path(args.yaml_input).expanduser()
    if yaml_candidate.is_file():
        yaml_str = yaml_candidate.read_text(encoding="utf-8")
    else:
        yaml_str = args.yaml_input

    tags = yaml.safe_load(yaml_str)
    if not isinstance(tags, dict):
        print("Error: YAMLの解析に失敗しました。", file=sys.stderr)
        sys.exit(1)

    # 日付抽出
    try:
        date = parse_date(text)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # 出力先
    POSTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = POSTS_DIR / f"{date.strftime('%Y%m%d')}.md"

    if out_path.exists():
        print(f"Warning: 既に存在します: {out_path}", file=sys.stderr)
        answer = input("上書きしますか？ [y/N]: ").strip().lower()
        if answer != "y":
            print("中断しました。")
            sys.exit(0)

    # markdown生成・保存
    front_matter = build_front_matter(date, tags)
    body         = strip_date_line(text)
    out_path.write_text(to_markdown(front_matter, body), encoding="utf-8")
    print(f"保存: {out_path}")

    # git
    try:
        git_add_commit_push(out_path, date, push=not args.no_push)
        print("commit 完了" + (" / push 完了" if not args.no_push else " (push スキップ)"))
    except subprocess.CalledProcessError as e:
        print(f"Warning: git操作に失敗しました: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
