# Life Itself — CLAUDE.md

日記・エッセイのテキストを貼り付けたら、以下をyaml形式で返すこと。

```yaml
zine_candidate:
  name: Memories/Language/Music/Reading/Diary/未分類
  confidence: 高/中/低
themes:
  - （5つまで）
has_quote: true/false
quotes:
  - （あれば抽出）
draft_status: 断片/下書き/ほぼ完成
publish: true/false
memo: （どの章と接続可能か、編集上の気づき）
```

## テキストが貼り付けられたときの動作

1. YAMLでタグ付けを返す
2. 確認なしにそのままHugoの記事として保存する
3. git pushまで自動で実行する

保存・pushには以下のスクリプトを使うこと：

```bash
python ~/Documents/lifeitself/scripts/diary_to_hugo.py <txtファイルパス> "<yaml文字列>"
```

txtファイルがない場合（テキストを直接貼り付けた場合）は、
`/tmp/diary_<日付>.txt` に一時保存してから上記スクリプトを実行すること。

## よく使うコマンド

### 非公開記事を含めてローカルで確認する
cd ~/Documents/lifeitself
hugo server -D
→ ブラウザで http://localhost:1313 を開く
→ 確認が終わったらターミナルでControl+Cで停止

### 記事をpushする
cd ~/Documents/lifeitself
git add .
git commit -m "記事追加"
git push

## プロジェクト情報

| ZINE | テーマ |
|---|---|
| Dancing To Memories | 祖母・祖父の記憶、世代継承、身体と言語 |
| Dancing To Language | スペイン語学習、音楽、野球 |
| Dancing To Papa | 父親になる体験、子育て |
