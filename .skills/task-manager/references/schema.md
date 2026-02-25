# Task Schema Reference

`.tasks/tasks.yaml` のスキーマ仕様。

## ファイル構造

```yaml
tasks:
  - id: TASK-001
    title: タスクのタイトル
    description: 詳細説明（省略可）
    status: todo
    priority: high
    created_at: 2026-02-25
    tags:
      - tag1
      - tag2
```

## フィールド定義

| フィールド | 必須 | 型 | 説明 |
|---|---|---|---|
| `id` | ✅ | 文字列 | 一意な識別子。`TASK-NNN` 形式（3桁ゼロ埋め） |
| `title` | ✅ | 文字列 | タスクの短いタイトル。一覧表示時の主要な情報 |
| `status` | ✅ | 列挙 | 下記参照 |
| `priority` | ✅ | 列挙 | 下記参照 |
| `created_at` | ✅ | 日付 | `YYYY-MM-DD` 形式。タスク作成日 |
| `description` | — | 文字列 | タスクの詳細説明。タイトルだけでは不十分な場合に記載 |
| `tags` | — | 文字列リスト | フィルタリング・分類用。小文字ケバブケース推奨 |

## status の有効値

| 値 | 意味 |
|---|---|
| `todo` | 未着手 |
| `in_progress` | 進行中 |
| `done` | 完了 |
| `blocked` | ブロック中（依存タスクや外部要因で進められない状態） |

## priority の有効値

| 値 | 意味 |
|---|---|
| `high` | 高優先度。早急に対応が必要 |
| `medium` | 中優先度。通常の対応 |
| `low` | 低優先度。時間があれば対応 |

## ID採番ルール

- 形式: `TASK-NNN`（NNNは3桁ゼロ埋めの連番）
- 新しいIDは「既存の最大番号 + 1」とする
- 欠番は補填しない。削除されたIDは再利用しない
- タスクの追加はYAMLファイルの直接編集で行う

## ソート順の定義

スクリプトのデフォルトソートは priority → status の順：

**priority順**: high → medium → low

**status順**: in_progress → todo → blocked → done
（doneは最後に表示することで、未完了タスクが上に来る）
