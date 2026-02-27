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
- 操作スクリプト: `.skills/task-manager/scripts/tasks.py`

## 操作方法

スクリプトは `uv run` で実行する（依存ライブラリを自動インストール）。

### 一覧表示・フィルタリング・ソート

```bash
# すべてのタスクを優先度順で表示（デフォルト）
uv run .skills/task-manager/scripts/tasks.py list

# ステータスでフィルタ
uv run .skills/task-manager/scripts/tasks.py list --status todo

# 優先度でフィルタ
uv run .skills/task-manager/scripts/tasks.py list --priority high

# タグでフィルタ
uv run .skills/task-manager/scripts/tasks.py list --tag infrastructure

# ソート順を変更（複数キーを左から順に適用）
uv run .skills/task-manager/scripts/tasks.py list --sort status priority

# ソート結果をファイルにも書き戻す
uv run .skills/task-manager/scripts/tasks.py list --sort status priority --write

# 詳細（description）も表示
uv run .skills/task-manager/scripts/tasks.py list -v
```

### タスクの追加

`.tasks/tasks.yaml` を直接編集する。IDの採番方法は [references/schema.md](references/schema.md) を参照。

```yaml
- id: TASK-005          # 既存の最大IDに+1
  title: タスクのタイトル
  status: todo
  priority: medium
  created_at: 2026-02-25
  description: |        # 長い説明はブロックスカラーで書ける
    詳細な説明をここに書く。
    複数行も自然に書ける。
  tags:
    - tag1
```

### タスクの更新

```bash
# ステータスを更新
uv run .skills/task-manager/scripts/tasks.py update TASK-001 --status done

# 優先度を変更
uv run .skills/task-manager/scripts/tasks.py update TASK-001 --priority low
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

## 注意事項

- YAMLファイルを直接編集する場合、ファイル冒頭のコメント（スキーマ説明）を削除しない
- IDは既存の最大番号に+1する。欠番は補填しない。削除されたIDは再利用しない
