#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate ai_content.json from stats.json and simplified_chat.txt via OpenAI."""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path


OPENAI_URL = "https://api.openai.com/v1/responses"
DEFAULT_MODEL = "gpt-5-mini"


def parse_args():
    parser = argparse.ArgumentParser(description="Generate ai_content.json with the OpenAI Responses API.")
    parser.add_argument("--prompt", default="references/ai_prompt.md", help="Prompt template path")
    parser.add_argument("--stats", default="stats.json", help="stats.json path")
    parser.add_argument("--chat", default="simplified_chat.txt", help="simplified_chat.txt path")
    parser.add_argument("--output", default="ai_content.json", help="Output JSON path")
    parser.add_argument("--model", default=os.getenv("OPENAI_MODEL", DEFAULT_MODEL), help="OpenAI model name")
    parser.add_argument("--api-key", default=os.getenv("OPENAI_API_KEY"), help="OpenAI API key")
    parser.add_argument("--max-retries", type=int, default=2, help="Retries when model output is not valid JSON")
    return parser.parse_args()


def read_text(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def build_input(prompt_text: str, stats_text: str, chat_text: str) -> str:
    return (
        f"{prompt_text}\n\n"
        "下面是本次生成需要使用的输入文件内容。\n\n"
        "【stats.json】\n"
        f"{stats_text}\n\n"
        "【simplified_chat.txt】\n"
        f"{chat_text}\n\n"
        "再次强调：只输出合法 JSON，不要输出 Markdown，不要输出解释。"
    )


def call_openai(api_key: str, model: str, user_input: str) -> str:
    payload = {
        "model": model,
        "input": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": user_input,
                    }
                ],
            }
        ],
        "text": {
            "format": {
                "type": "json_object"
            }
        },
    }
    req = urllib.request.Request(
        OPENAI_URL,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    return body.get("output_text", "").strip()


def validate_ai_content(data: dict, stats: dict):
    required_keys = {
        "topics",
        "resources",
        "important_messages",
        "dialogues",
        "qas",
        "talker_profiles",
    }
    missing = required_keys - set(data.keys())
    if missing:
        raise ValueError(f"missing keys: {sorted(missing)}")

    talker_profiles = data.get("talker_profiles")
    if not isinstance(talker_profiles, dict):
        raise ValueError("talker_profiles must be an object")

    top_talkers = stats.get("top_talkers", [])
    expected_names = [item.get("name") for item in top_talkers if item.get("name")]
    if sorted(talker_profiles.keys()) != sorted(expected_names):
        raise ValueError(
            "talker_profiles keys must exactly match stats.json top_talkers names: "
            f"{expected_names}"
        )


def main():
    args = parse_args()
    if not args.api_key:
        raise SystemExit("Missing OPENAI_API_KEY")

    prompt_text = read_text(args.prompt)
    stats_text = read_text(args.stats)
    chat_text = read_text(args.chat)
    stats_data = json.loads(stats_text)
    user_input = build_input(prompt_text, stats_text, chat_text)

    last_error = None
    for attempt in range(1, args.max_retries + 2):
        try:
            output_text = call_openai(args.api_key, args.model, user_input)
            data = json.loads(output_text)
            validate_ai_content(data, stats_data)
            Path(args.output).write_text(
                json.dumps(data, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            print(f"AI content saved to: {args.output}")
            return
        except (json.JSONDecodeError, ValueError, urllib.error.HTTPError, urllib.error.URLError) as exc:
            last_error = exc
            if attempt > args.max_retries:
                break
            print(f"Retrying AI generation after error: {exc}", file=sys.stderr)

    raise SystemExit(f"Failed to generate valid ai_content.json: {last_error}")


if __name__ == "__main__":
    main()
