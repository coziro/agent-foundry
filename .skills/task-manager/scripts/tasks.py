#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = ["ruamel.yaml"]
# ///
"""Task management CLI for Agent Foundry.

Usage:
  uv run .skills/task-manager/scripts/tasks.py list [--status STATUS] [--priority PRIORITY] [--tag TAG] [--sort KEY [KEY...]] [-v] [-w]
  uv run .skills/task-manager/scripts/tasks.py update ID [--status STATUS] [--priority PRIORITY] [--title TITLE] [--description DESC]

Sort keys (applied left to right):
  status    in_progress → todo → blocked → done
  priority  high → medium → low
  created   oldest first

Examples:
  --sort status priority   # status first, then priority within each status
  --sort priority          # priority only

Note: To add a task, edit .tasks/tasks.yaml directly. See references/schema.md for the schema.
"""

import argparse
import io
import re
import sys
from pathlib import Path

from ruamel.yaml import YAML

TASKS_FILE = Path(__file__).parents[3] / ".tasks" / "tasks.yaml"

PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}
STATUS_ORDER = {"in_progress": 0, "todo": 1, "blocked": 2, "done": 3}
VALID_STATUSES = {"todo", "in_progress", "done", "blocked"}
VALID_PRIORITIES = {"high", "medium", "low"}


def load_data():
    yaml = YAML()
    with open(TASKS_FILE) as f:
        return yaml.load(f)


def save_data(data):
    yaml = YAML()
    yaml.default_flow_style = False
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
        status = t.get("status", "?")
        priority = t.get("priority", "?")
        title = t.get("title", "")
        tags = t.get("tags") or []
        tag_str = f" [{', '.join(tags)}]" if tags else ""
        print(f"{tid}  [{status:11}]  [{priority:6}]  {title}{tag_str}")
        if args.verbose and t.get("description"):
            print(f"    {t['description']}")


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

    # update
    p_update = sub.add_parser("update", help="Update a task")
    p_update.add_argument("id", help="Task ID (e.g. TASK-001)")
    p_update.add_argument("--title")
    p_update.add_argument("--description")
    p_update.add_argument("--status", choices=sorted(VALID_STATUSES))
    p_update.add_argument("--priority", choices=sorted(VALID_PRIORITIES))
    p_update.set_defaults(func=cmd_update)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
