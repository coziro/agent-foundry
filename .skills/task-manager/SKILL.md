---
name: task-manager
description: タスクの追加・更新・一覧表示などタスク管理に関する操作を行う。ユーザーがタスクの追加・確認・ステータス変更・優先度変更を依頼したとき、またはエージェントが自主的に新しいタスクをトラッキングすべきと判断したときに使用する。「タスクリストに追加して」「TASK-XXXを完了にして」「今のタスクを見せて」などの表現でも使用する。
metadata:
  version: "0.1"
---

# Task Manager

`.tasks/tasks.yaml` を使ってタスクを管理するスキル。
スキーマの詳細は [references/schema.md](references/schema.md) を参照。

**前提条件:** `scripts/tasks.py` の実行には `uv`（Python パッケージマネージャ）が必要。

## ファイルパス

- タスクファイル: `.tasks/tasks.yaml`（プロジェクトルートからの相対パス）
- 操作スクリプト: `scripts/tasks.py`（このスキルのベースディレクトリからの相対パス）

## 操作方法

スクリプトは `uv run` で実行する（依存ライブラリを自動インストール）。
パスはこのスキルのベースディレクトリからの相対パス `scripts/tasks.py` を使用する。

> **例:** ベースディレクトリが `.skills/task-manager` なら `uv run .skills/task-manager/scripts/tasks.py list`

### 一覧表示・フィルタリング・ソート

```bash
# すべてのタスクを優先度順で表示（デフォルト）
uv run {base}/scripts/tasks.py list

# ステータスでフィルタ
uv run {base}/scripts/tasks.py list --status todo

# 優先度でフィルタ
uv run {base}/scripts/tasks.py list --priority high

# タグでフィルタ
uv run {base}/scripts/tasks.py list --tag infrastructure

# ソート順を変更（複数キーを左から順に適用）
uv run {base}/scripts/tasks.py list --sort status priority

# ソート結果をファイルにも書き戻す
uv run {base}/scripts/tasks.py list --sort status priority --write

# 詳細（description）も表示
uv run {base}/scripts/tasks.py list -v
```

### タスクの追加

スクリプトの `add` コマンドを使う。YAML への追記、詳細フォルダ (`.tasks/details/{TASK-ID}/`) の作成、`requirements.md` のテンプレート生成を一括で行う。

```bash
# 基本
uv run {base}/scripts/tasks.py add "タスクのタイトル"

# 説明・優先度・アイコン・タグ付き
uv run {base}/scripts/tasks.py add "タスクのタイトル" \
  -d "詳細な説明" \
  --priority high \
  --icon ⭐ \
  --tags experiment improvement
```

IDは自動採番（既存の最大ID + 1）。追加後に `list --sort status priority --write` でソートするとよい。

### 依存関係

`depends_on` フィールドで他タスクへの依存を宣言できる。依存先がすべて `done` になってから着手する想定。

- 一覧表示では依存先が `← TASK-XXX` として表示される
- `-v` オプションで詳細表示すると `depends_on:` 行も出力される

### タスクの更新

```bash
# ステータスを更新
uv run {base}/scripts/tasks.py update TASK-001 --status done

# 優先度を変更
uv run {base}/scripts/tasks.py update TASK-001 --priority low

# アイコンを変更
uv run {base}/scripts/tasks.py update TASK-001 --icon ✅
```

## ステータス遷移

```
todo → in_progress → done
            ↓
         blocked → todo / in_progress
```

`done` にしたタスクは基本的に変更しない。誤りの場合のみ修正する。

## エージェントが自主的にタスクを追加する場合

会話の中でトラッキングすべき作業が発生したと判断したら、ユーザーへの確認なしにタスクを追加してよい。ただし追加後に「〇〇というタスクをリストに追加しました」と報告する。

迷う場合はユーザーに確認する。

## ソートについて

ユーザーが「ソートして」と言った場合は、`list --write` を使ってファイルの並び順も変更する。

## アイコン（icon フィールド）

タスクの温度感を視覚的に表現するための絵文字フィールド。status/priority とは独立した軸で、人間が YAML を流し読みする際にタスクの状態を素早く把握できる。

有効な絵文字（詳細は [references/schema.md](references/schema.md) を参照）:
🔥 緊急 / ⭐ 重要 / 🌱 低優先 / 🔍 アイデア / ⏳ 待ち / ⚡️ 進行中 / 🔧 改善余地あり / ✅ 完了 / 🚫 やらない

運用ルール:
- タスク追加時に AI が推定して設定する。人間が違和感を感じたら修正する
- status 変更に合わせて icon も更新する（完了時は ✅、やらない場合は 🚫）
- 複数絵文字の組み合わせも可（最大2つ推奨。例: `⭐⏳`）

## 注意事項

- 一部の絵文字（⚡️ ⭐ ⏳ 等）は Variation Selector (U+FE0F) がないとモノスペースフォントでテキスト表示になる。`tasks.py` 経由なら自動で正規化されるが、YAML を直接編集する場合は注意すること
- YAMLファイルを直接編集する場合、ファイル冒頭のコメント（スキーマ説明）を削除しない
- IDは既存の最大番号に+1する。欠番は補填しない。削除されたIDは再利用しない
- タスクを変更したら `updated_at` を必ず更新する。`tasks.py update` 経由なら自動セットされるが、YAML直接編集時は手動で当日の日付を記入すること
