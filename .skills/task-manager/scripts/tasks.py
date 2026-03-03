#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = ["ruamel.yaml"]
# ///
"""Task management CLI for Agent Foundry.

Usage:
  uv run scripts/tasks.py list [--status STATUS] [--priority PRIORITY] [--tag TAG] [--sort KEY [KEY...]] [-v] [-w]
  uv run scripts/tasks.py add TITLE [-d DESC] [--status STATUS] [--priority PRIORITY] [--icon ICON] [--tags TAG ...]
  uv run scripts/tasks.py update ID [--status STATUS] [--priority PRIORITY] [--title TITLE] [--description DESC] [--icon ICON]

Sort keys (applied left to right):
  status    in_progress → scoping → planning → todo → in_review → blocked → done
  priority  high → medium → low
  created   oldest first

The 'add' command also creates .tasks/details/{TASK-ID}/ and requirements.md.
"""

import argparse
import datetime
import io
import re
import sys
from pathlib import Path

from ruamel.yaml import YAML

def _find_project_root() -> Path:
    """スクリプトの位置から親ディレクトリを辿り、.tasks/ を含むプロジェクトルートを返す。"""
    d = Path(__file__).resolve().parent
    while d != d.parent:
        if (d / ".tasks").is_dir():
            return d
        d = d.parent
    raise FileNotFoundError("Project root with .tasks/ directory not found")


_PROJECT_ROOT = _find_project_root()
TASKS_FILE = _PROJECT_ROOT / ".tasks" / "tasks.yaml"
DETAILS_DIR = _PROJECT_ROOT / ".tasks" / "details"

PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}
STATUS_ORDER = {
    "in_progress": 0,
    "scoping": 1,
    "planning": 2,
    "todo": 3,
    "in_review": 4,
    "blocked": 5,
    "done": 6,
}
VALID_STATUSES = set(STATUS_ORDER)
VALID_PRIORITIES = {"high", "medium", "low"}
VALID_ICONS = {"🔥", "⭐", "🌱", "🔍", "⏳", "⚡️", "🔧", "✅", "🚫"}

# テキスト表示になりうる絵文字のベースコードポイント → FE0F 付きへの正規化マップ
# VSCode 等のモノスペースフォントで正しくカラー表示するために必要
_EMOJI_NORMALIZE = {
    "\u26A1": "\u26A1\uFE0F",  # ⚡ → ⚡️
    "\u2B50": "\u2B50\uFE0F",  # ⭐ → ⭐️
    "\u231B": "\u231B\uFE0F",  # ⏳ → ⏳️
}


def _normalize_icon(icon: str) -> str:
    """icon 文字列内のテキスト表示になりうる絵文字に FE0F を付与する。"""
    for bare, with_fe0f in _EMOJI_NORMALIZE.items():
        icon = icon.replace(bare + "\uFE0F", "\x00PLACEHOLDER\x00")  # 既に FE0F 付きのものを保護
        icon = icon.replace(bare, with_fe0f)  # bare に FE0F を付与
        icon = icon.replace("\x00PLACEHOLDER\x00", with_fe0f)  # 保護を戻す
    return icon


# フィールドの正規順序（save_data で並び替えに使用）
FIELD_ORDER = [
    "id", "icon", "title", "description", "status", "priority",
    "created_at", "updated_at", "depends_on", "tags",
]


def load_data():
    yaml = YAML()
    with open(TASKS_FILE) as f:
        return yaml.load(f)


def _reorder_task(task):
    """タスクのフィールドを正規順序に並べ替えた新しい dict を返す。"""
    from ruamel.yaml.comments import CommentedMap
    ordered = CommentedMap()
    for key in FIELD_ORDER:
        if key in task:
            ordered[key] = task[key]
    # FIELD_ORDER に含まれない未知のフィールドも末尾に追加
    for key in task:
        if key not in ordered:
            ordered[key] = task[key]
    return ordered


def save_data(data):
    yaml = YAML()
    yaml.default_flow_style = False
    # フィールド順序を正規化
    if data.get("tasks"):
        data["tasks"] = [_reorder_task(t) for t in data["tasks"]]
    buf = io.StringIO()
    yaml.dump(data, buf)
    # 可読性のため、各タスク ("- id: ...") の前に空行を挿入する
    text = re.sub(r"(?<!\n)\n- id:", "\n\n- id:", buf.getvalue())
    with open(TASKS_FILE, "w") as f:
        f.write(text)


def cmd_list(args):
    data = load_data()
    tasks = list(data.get("tasks") or [])

    if args.status:
        tasks = [t for t in tasks if t.get("status") == args.status]
    if args.priority:
        tasks = [t for t in tasks if t.get("priority") == args.priority]
    if args.tag:
        tasks = [t for t in tasks if args.tag in (t.get("tags") or [])]

    def sort_key(t):
        key = []
        for s in args.sort:
            if s == "priority":
                key.append(PRIORITY_ORDER.get(t.get("priority", ""), 99))
            elif s == "status":
                key.append(STATUS_ORDER.get(t.get("status", ""), 99))
            elif s == "created":
                key.append(str(t.get("created_at", "")))
        return tuple(key)

    tasks.sort(key=sort_key)

    # --write: ソート結果をファイルに書き戻す
    if args.write:
        data["tasks"] = tasks
        save_data(data)

    if not tasks:
        print("No tasks found.")
        return

    for t in tasks:
        tid = t.get("id", "?")
        icon = t.get("icon", "")
        icon_str = f"  {icon}" if icon else "   "
        status = t.get("status", "?")
        priority = t.get("priority", "?")
        title = t.get("title", "")
        tags = t.get("tags") or []
        tag_str = f" [{', '.join(tags)}]" if tags else ""
        deps = t.get("depends_on") or []
        dep_str = f" ← {', '.join(deps)}" if deps else ""
        print(f"{tid}{icon_str}  [{status:11}]  [{priority:6}]  {title}{tag_str}{dep_str}")
        if args.verbose and t.get("description"):
            print(f"    {t['description']}")
        if args.verbose and deps:
            print(f"    depends_on: {', '.join(deps)}")


def next_task_id(tasks: list) -> str:
    max_num = 0
    for t in tasks:
        tid = t.get("id", "")
        m = re.match(r"TASK-(\d+)", tid)
        if m:
            max_num = max(max_num, int(m.group(1)))
    return f"TASK-{max_num + 1:03d}"


REQUIREMENTS_TEMPLATE = """\
# {title}

## 背景・目的

{description}

## 要件

- [ ] TBD
"""


def cmd_add(args):
    data = load_data()
    tasks = list(data.get("tasks") or [])

    task_id = next_task_id(tasks)
    today = datetime.date.today()

    task = {
        "id": task_id,
        "title": args.title,
        "status": args.status,
        "priority": args.priority,
        "created_at": today,
    }
    if args.icon:
        task["icon"] = _normalize_icon(args.icon)
    if args.description:
        task["description"] = args.description + "\n"
    if args.tags:
        task["tags"] = args.tags

    tasks.append(task)
    data["tasks"] = tasks
    save_data(data)

    # Create details directory and requirements.md
    detail_dir = DETAILS_DIR / task_id
    detail_dir.mkdir(parents=True, exist_ok=True)

    req_file = detail_dir / "requirements.md"
    if not req_file.exists():
        req_file.write_text(
            REQUIREMENTS_TEMPLATE.format(
                title=args.title,
                description=(args.description or "").strip() or "TBD",
            )
        )

    print(f"Added: {task_id} - {args.title}")
    print(f"Details: .tasks/details/{task_id}/")
    print(f"Requirements: .tasks/details/{task_id}/requirements.md")


def cmd_update(args):
    data = load_data()
    tasks = list(data.get("tasks") or [])

    for task in tasks:
        if str(task.get("id")) == args.id:
            if args.status:
                task["status"] = args.status
            if args.priority:
                task["priority"] = args.priority
            if args.title:
                task["title"] = args.title
            if args.description:
                task["description"] = args.description
            if args.icon:
                task["icon"] = _normalize_icon(args.icon)
            task["updated_at"] = datetime.date.today()
            data["tasks"] = tasks
            save_data(data)
            print(f"Updated: {task['id']} - {task.get('title', '')}")
            return

    print(f"Error: task '{args.id}' not found.", file=sys.stderr)
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Task management CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    # list
    p_list = sub.add_parser("list", help="List tasks")
    p_list.add_argument("--status", choices=sorted(VALID_STATUSES))
    p_list.add_argument("--priority", choices=sorted(VALID_PRIORITIES))
    p_list.add_argument("--tag")
    p_list.add_argument("--sort", choices=["priority", "status", "created"], nargs="+", default=["status", "priority"])
    p_list.add_argument("-w", "--write", action="store_true", help="Write sort order to file")
    p_list.add_argument("-v", "--verbose", action="store_true", help="Show description")
    p_list.set_defaults(func=cmd_list)

    # add
    p_add = sub.add_parser("add", help="Add a new task")
    p_add.add_argument("title", help="Task title")
    p_add.add_argument("-d", "--description", help="Task description")
    p_add.add_argument("--status", choices=sorted(VALID_STATUSES), default="todo")
    p_add.add_argument("--priority", choices=sorted(VALID_PRIORITIES), default="medium")
    p_add.add_argument("--icon", help="Icon emoji for the task")
    p_add.add_argument("--tags", nargs="+", help="Tags for the task")
    p_add.set_defaults(func=cmd_add)

    # update
    p_update = sub.add_parser("update", help="Update a task")
    p_update.add_argument("id", help="Task ID (e.g. TASK-001)")
    p_update.add_argument("--title")
    p_update.add_argument("--description")
    p_update.add_argument("--status", choices=sorted(VALID_STATUSES))
    p_update.add_argument("--priority", choices=sorted(VALID_PRIORITIES))
    p_update.add_argument("--icon", help="Icon emoji for the task")
    p_update.set_defaults(func=cmd_update)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
