#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Run the full daily-report pipeline once for a WeChat group."""

from __future__ import annotations

import argparse
import datetime as dt
import os
import subprocess
import sys
from pathlib import Path
from zoneinfo import ZoneInfo


TZ = ZoneInfo("Asia/Shanghai")


def parse_args():
    parser = argparse.ArgumentParser(description="Run the WeChat daily-report pipeline once.")
    parser.add_argument("--chatroom", default="agent 交流沟通群", help="WeChat group name or chatroom id")
    parser.add_argument("--date", default=None, help="Report date in YYYY-MM-DD; defaults to yesterday in Asia/Shanghai")
    parser.add_argument("--limit", type=int, default=5000, help="Maximum messages to fetch")
    parser.add_argument("--skip-push", action="store_true", help="Commit locally but do not push")
    parser.add_argument("--skip-commit", action="store_true", help="Generate outputs but do not commit")
    parser.add_argument("--openai-model", default=os.getenv("OPENAI_MODEL", "gpt-5-mini"), help="OpenAI model")
    return parser.parse_args()


def report_date(date_text: str | None) -> str:
    if date_text:
        return date_text
    return (dt.datetime.now(TZ).date() - dt.timedelta(days=1)).isoformat()


def run(cmd: list[str], cwd: Path):
    print("+", " ".join(cmd))
    subprocess.run(cmd, cwd=str(cwd), check=True)


def has_cached_changes(cwd: Path) -> bool:
    result = subprocess.run(
        ["git", "diff", "--cached", "--quiet"],
        cwd=str(cwd),
        check=False,
    )
    return result.returncode != 0


def main():
    args = parse_args()
    root = Path(__file__).resolve().parent.parent
    date_text = report_date(args.date)
    python = sys.executable

    run(
        [
            python,
            "scripts/wx_cli_to_report.py",
            "--chatroom",
            args.chatroom,
            "--date",
            date_text,
            "--limit",
            str(args.limit),
            "--output-stats",
            "stats.json",
            "--output-text",
            "simplified_chat.txt",
            "--raw-output",
            "raw_wx_history.json",
        ],
        root,
    )
    run(
        [
            python,
            "scripts/generate_ai_content.py",
            "--prompt",
            "references/ai_prompt.md",
            "--stats",
            "stats.json",
            "--chat",
            "simplified_chat.txt",
            "--output",
            "ai_content.json",
            "--model",
            args.openai_model,
        ],
        root,
    )
    run(
        [
            python,
            "scripts/generate_report.py",
            "--stats",
            "stats.json",
            "--ai-content",
            "ai_content.json",
            "--output",
            "report.html",
        ],
        root,
    )
    run(
        [
            python,
            "scripts/generate_report.py",
            "--stats",
            "stats.json",
            "--ai-content",
            "ai_content.json",
            "--output",
            "report.png",
        ],
        root,
    )

    for required in ("stats.json", "ai_content.json", "report.html", "report.png"):
        if not (root / required).exists():
            raise SystemExit(f"Missing required output: {required}")

    if args.skip_commit:
        print("Generated outputs successfully; skipping git commit/push.")
        return

    run(["git", "add", "-f", "stats.json", "ai_content.json", "report.html", "report.png"], root)

    if not has_cached_changes(root):
        print("No report changes to commit.")
        return

    run(["git", "commit", "-m", f"Update daily report for {date_text}"], root)

    if args.skip_push:
        print("Committed report locally; skipping push.")
        return

    run(["git", "push"], root)


if __name__ == "__main__":
    main()
