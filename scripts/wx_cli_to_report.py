#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Convert WeChat messages from wx-cli/wechat-cli into report inputs.

Preferred source:
    wx history "群名" --since 2026-04-30 --until 2026-04-30 -n 5000 --json

Compatible fallback:
    wechat-cli history "群名" --start-time 2026-04-30 --end-time 2026-04-30 --limit 5000 --format json
"""

import argparse
import datetime as dt
import json
import os
import random
import re
import shutil
import subprocess
import sys
from collections import Counter, defaultdict

try:
    import jieba
    JIEBA_AVAILABLE = True
except ImportError:
    JIEBA_AVAILABLE = False


STOPWORDS = {
    "的", "了", "我", "是", "你", "在", "他", "她", "它", "我们", "你们", "他们",
    "这个", "那个", "就是", "可以", "不是", "没有", "一个", "一下", "现在",
    "感觉", "觉得", "应该", "可能", "已经", "还是", "什么", "怎么", "哈哈",
    "哈哈哈", "图片", "表情", "动画表情", "语音", "链接", "文件", "分享",
}


def parse_arguments():
    parser = argparse.ArgumentParser(description="Use wx-cli/wechat-cli history output to generate stats.json and simplified_chat.txt.")
    parser.add_argument("--chatroom", help="WeChat chat/group name. Required unless --input-json includes a chat name.")
    parser.add_argument("--date", help="Single day filter, format YYYY-MM-DD.")
    parser.add_argument("--start", help="Start time/date passed to CLI.")
    parser.add_argument("--end", help="End time/date passed to CLI.")
    parser.add_argument("--limit", type=int, default=5000, help="Maximum messages to fetch from CLI.")
    parser.add_argument("--cli", choices=["auto", "wx", "wechat-cli"], default="auto", help="CLI command to use.")
    parser.add_argument("--binary", help="Explicit wx/wechat-cli binary path. Useful for a locally unpacked package.")
    parser.add_argument("--input-json", help="Use an existing wx-cli/wechat-cli JSON file instead of calling the CLI.")
    parser.add_argument("--raw-output", help="Save raw CLI JSON to this path.")
    parser.add_argument("--output-stats", default="stats.json", help="Path to output stats JSON.")
    parser.add_argument("--output-text", default="simplified_chat.txt", help="Path to output simplified chat text.")
    return parser.parse_args()


def ensure_parent(path):
    parent = os.path.dirname(os.path.abspath(path))
    if parent:
        os.makedirs(parent, exist_ok=True)


def infer_cli_kind(binary):
    name = os.path.basename(binary)
    if name == "wx" or name.startswith("wx."):
        return "wx"
    return "wechat-cli"


def pick_cli(requested, binary=None):
    if binary:
        if not os.path.exists(binary):
            raise RuntimeError(f"找不到 CLI 文件：{binary}")
        return infer_cli_kind(binary), binary

    if requested != "auto":
        found = shutil.which(requested)
        if found:
            return requested, found
        raise RuntimeError(f"找不到命令：{requested}")
    for candidate in ("wx", "wechat-cli"):
        found = shutil.which(candidate)
        if found:
            return candidate, found
    raise RuntimeError("找不到 wx 或 wechat-cli。请先安装 @jackwener/wx-cli，或把本地 wechat-cli 包安装到 PATH。")


def run_cli(args):
    cli, executable = pick_cli(args.cli, args.binary)
    if not args.chatroom:
        raise RuntimeError("调用 CLI 时必须提供 --chatroom")

    start = args.start or args.date
    end = args.end or args.date

    if cli == "wx":
        cmd = [executable, "history", args.chatroom, "-n", str(args.limit), "--json"]
        if start:
            cmd.extend(["--since", start])
        if end:
            cmd.extend(["--until", end])
    else:
        cmd = [executable, "history", args.chatroom, "--limit", str(args.limit), "--format", "json"]
        if start:
            cmd.extend(["--start-time", start])
        if end:
            cmd.extend(["--end-time", end])

    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode != 0:
        raise RuntimeError(
            "读取微信聊天记录失败：\n"
            f"Command: {' '.join(cmd)}\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )
    return cli, result.stdout


def load_json_text(text):
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Some wrappers may print hints before/after JSON. Keep a conservative fallback.
    starts = [i for i in (text.find("{"), text.find("[")) if i >= 0]
    ends = [i for i in (text.rfind("}"), text.rfind("]")) if i >= 0]
    if not starts or not ends:
        raise ValueError("CLI output is not valid JSON")
    fragment = text[min(starts):max(ends) + 1]
    return json.loads(fragment)


def load_source(args):
    if args.input_json:
        with open(args.input_json, "r", encoding="utf-8") as f:
            text = f.read()
        return "input-json", load_json_text(text), text

    cli, text = run_cli(args)
    return cli, load_json_text(text), text


def extract_messages(data):
    if isinstance(data, list):
        return data, {}
    if not isinstance(data, dict):
        return [], {}

    for key_path in (
        ("messages",),
        ("data", "messages"),
        ("result", "messages"),
        ("history", "messages"),
    ):
        cursor = data
        for key in key_path:
            if isinstance(cursor, dict):
                cursor = cursor.get(key)
            else:
                cursor = None
        if isinstance(cursor, list):
            return cursor, data

    return [], data


def parse_time_value(value, default_date=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        # wx-cli timestamps are seconds.
        return dt.datetime.fromtimestamp(value)
    if not isinstance(value, str):
        return None

    text = value.strip()
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y/%m/%d %H:%M:%S",
        "%Y/%m/%d %H:%M",
        "%Y-%m-%dT%H:%M:%S",
    ]
    for fmt in formats:
        try:
            return dt.datetime.strptime(text[:19], fmt)
        except ValueError:
            pass

    if default_date:
        for fmt in ("%H:%M:%S", "%H:%M"):
            try:
                parsed = dt.datetime.strptime(text, fmt)
                base = dt.datetime.strptime(default_date, "%Y-%m-%d")
                return base.replace(hour=parsed.hour, minute=parsed.minute, second=parsed.second)
            except ValueError:
                pass
    return None


def normalize_message(message, default_date=None):
    if not isinstance(message, dict):
        return None

    timestamp = message.get("timestamp") or message.get("create_time") or message.get("time_ts")
    parsed_time = parse_time_value(timestamp, default_date)
    if parsed_time is None:
        parsed_time = parse_time_value(message.get("time") or message.get("datetime") or message.get("created_at"), default_date)

    sender = (
        message.get("sender")
        or message.get("sender_name")
        or message.get("from")
        or message.get("from_name")
        or message.get("talker")
        or ""
    )
    sender = str(sender).strip() or "未知成员"

    content = message.get("content") or message.get("text") or message.get("message") or ""
    if isinstance(content, (dict, list)):
        content = json.dumps(content, ensure_ascii=False)
    content = str(content).replace("\r", "").strip()

    msg_type = str(message.get("type") or message.get("msg_type") or message.get("local_type") or "text")

    if not content:
        content = f"[{msg_type}]"

    return {
        "dt": parsed_time,
        "timestamp": int(parsed_time.timestamp()) if parsed_time else 0,
        "time": parsed_time.strftime("%Y-%m-%d %H:%M") if parsed_time else str(message.get("time") or ""),
        "sender": sender,
        "content": content,
        "type": msg_type,
    }


def normalize_messages(messages, default_date=None):
    normalized = [normalize_message(m, default_date) for m in messages]
    normalized = [m for m in normalized if m]
    normalized.sort(key=lambda m: (m["timestamp"], m["time"]))
    return normalized


def generate_word_cloud(messages, top_n=60):
    words = []
    text = " ".join(m["content"] for m in messages if m["content"])
    if JIEBA_AVAILABLE:
        words = [w for w in jieba.cut(text) if len(w) > 1 and w not in STOPWORDS]
    else:
        words = [w for w in re.split(r"[\s,，。！？、:：;；/\\()\[\]{}<>《》\"'`]+", text) if len(w) > 1 and w not in STOPWORDS]

    counts = Counter(words).most_common(top_n)
    colors = ["#7a351f", "#287a5b", "#415f8f", "#d39b35", "#8b5a86", "#b45f2a"]
    random.seed(20260501)
    result = []
    max_count = counts[0][1] if counts else 1
    for word, count in counts:
        result.append({
            "text": word,
            "count": count,
            "size": int(min(40, max(14, 12 + (count / max_count) * 28))),
            "color": random.choice(colors),
            "left": random.randint(8, 88),
            "top": random.randint(44, 260),
            "rotate": random.randint(-12, 12),
        })
    return result


def generate_simplified_text(messages, chat_name, date_str, output_text):
    lines = [f"=== 群名称: {chat_name} | 日期: {date_str or '-'} | 消息总数: {len(messages)} ==="]
    if not messages:
        ensure_parent(output_text)
        with open(output_text, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        return [output_text]

    groups = []
    current = []
    window_start = None
    for message in messages:
        ts = message["timestamp"]
        if window_start is None or ts - window_start <= 5 * 60:
            current.append(message)
            if window_start is None:
                window_start = ts
        else:
            groups.append(current)
            current = [message]
            window_start = ts
    if current:
        groups.append(current)

    for group in groups:
        start_time = group[0]["dt"].strftime("%H:%M") if group[0]["dt"] else group[0]["time"]
        end_time = group[-1]["dt"].strftime("%H:%M") if group[-1]["dt"] else group[-1]["time"]
        time_range = start_time if start_time == end_time else f"{start_time}~{end_time}"

        segments = []
        previous_sender = None
        for message in group:
            content = re.sub(r"\s+", " ", message["content"]).strip()
            if len(content) > 220:
                content = content[:220] + "..."
            sender = message["sender"]
            if sender == previous_sender and segments:
                segments[-1] += "/" + content
            else:
                segments.append(f"{sender}:{content}")
                previous_sender = sender
        lines.append(f"[{time_range}] " + " | ".join(segments))

    ensure_parent(output_text)
    with open(output_text, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return [output_text]


def build_stats(messages, meta, chat_name, date_str, output_text_paths, source_name):
    total_count = len(messages)
    active_users = sorted({m["sender"] for m in messages if m["sender"]})
    counts = Counter(m["sender"] for m in messages)

    top_talkers = []
    for index, (name, count) in enumerate(counts.most_common(3), 1):
        common_words = []
        combined = " ".join(m["content"] for m in messages if m["sender"] == name)
        if JIEBA_AVAILABLE:
            words = [w for w in jieba.cut(combined) if len(w) > 1 and w not in STOPWORDS]
            common_words = [w for w, _ in Counter(words).most_common(5)]
        top_talkers.append({
            "rank": index,
            "name": name,
            "count": count,
            "common_words": common_words,
        })

    night_messages = []
    for message in messages:
        when = message["dt"]
        if not when:
            continue
        if when.hour >= 23 or when.hour < 6:
            minutes_from_23 = (when.hour - 23 if when.hour >= 23 else when.hour + 1) * 60 + when.minute
            night_messages.append((minutes_from_23, message))

    night_owl = None
    if night_messages:
        _, latest = max(night_messages, key=lambda item: item[0])
        night_owl = {
            "name": latest["sender"],
            "last_time": latest["dt"].strftime("%H:%M") if latest["dt"] else latest["time"],
            "msg_count": sum(1 for _, m in night_messages if m["sender"] == latest["sender"]),
            "last_msg": latest["content"],
            "title": "熬夜冠军",
        }

    dated_messages = [m for m in messages if m["dt"]]
    if dated_messages:
        start = dated_messages[0]["dt"].strftime("%H:%M")
        end = dated_messages[-1]["dt"].strftime("%H:%M")
        inferred_date = dated_messages[0]["dt"].strftime("%Y-%m-%d")
    else:
        start = end = "-"
        inferred_date = date_str or "-"

    chat_from_meta = None
    if isinstance(meta, dict):
        chat_from_meta = meta.get("chat") or meta.get("name") or meta.get("display_name")
    final_chat_name = chat_name or chat_from_meta or "微信群"

    return {
        "meta": {
            "name": final_chat_name,
            "source": source_name,
            "date": date_str or inferred_date,
            "total_count": total_count,
            "active_user_count": len(active_users),
            "time_range": f"{start} 至 {end}",
        },
        "top_talkers": top_talkers,
        "night_owl": night_owl,
        "word_cloud": generate_word_cloud(messages),
        "name_avatar_map": {},
        "raw_text_paths": output_text_paths,
    }


def main():
    args = parse_arguments()
    try:
        source_name, data, raw_text = load_source(args)
        messages_raw, meta = extract_messages(data)
        chat_name = args.chatroom or (meta.get("chat") if isinstance(meta, dict) else None) or "微信群"
        date_str = args.date or args.start or ""
        if date_str and len(date_str) > 10:
            date_str = date_str[:10]

        messages = normalize_messages(messages_raw, date_str or None)

        if args.raw_output:
            ensure_parent(args.raw_output)
            with open(args.raw_output, "w", encoding="utf-8") as f:
                f.write(raw_text)

        text_paths = generate_simplified_text(messages, chat_name, date_str, args.output_text)
        stats = build_stats(messages, meta, chat_name, date_str, text_paths, source_name)

        ensure_parent(args.output_stats)
        with open(args.output_stats, "w", encoding="utf-8") as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)

        print(f"Source: {source_name}")
        print(f"Messages: {len(messages)}")
        print(f"Stats saved to: {args.output_stats}")
        print(f"Simplified text saved to: {', '.join(text_paths)}")
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
