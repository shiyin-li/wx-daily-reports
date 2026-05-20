#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build a GitHub Pages site from generated daily report artifacts."""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import shutil
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(
        description="Build a GitHub Pages site from report.html/report.png"
    )
    parser.add_argument("--report-html", default="report.html", help="Generated report HTML")
    parser.add_argument("--report-png", default="report.png", help="Generated report PNG")
    parser.add_argument("--stats", default="stats.json", help="Statistics JSON for metadata")
    parser.add_argument("--output", default="site", help="Output site directory")
    parser.add_argument("--title", default=None, help="Override site/report title")
    parser.add_argument("--date", default=None, help="Override report date (YYYY-MM-DD)")
    return parser.parse_args()


def load_json(path: Path):
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def ensure_parent(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)


def copy_file(source: Path, target: Path):
    ensure_parent(target)
    shutil.copy2(source, target)


def render_index(site_title: str, report_date: str, has_png: bool) -> str:
    png_block = (
        '<a class="button secondary" href="report.png">查看 PNG 长图</a>'
        if has_png
        else ""
    )
    updated_at = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    safe_title = html.escape(site_title)
    safe_date = html.escape(report_date)
    safe_updated_at = html.escape(updated_at)
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{safe_title}</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f5f1e8;
      --panel: rgba(255,255,255,.82);
      --ink: #18221d;
      --muted: #60706a;
      --line: #d9e0d7;
      --accent: #b55d2f;
      --accent-ink: #fff7ed;
      --shadow: 0 24px 60px rgba(28, 38, 33, .10);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      min-height: 100vh;
      font-family: "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
      color: var(--ink);
      background:
        radial-gradient(circle at top left, rgba(202, 220, 209, .85), transparent 36%),
        radial-gradient(circle at right 18%, rgba(240, 213, 186, .8), transparent 28%),
        linear-gradient(145deg, #eef3ee, var(--bg) 48%, #edf0f5);
    }}
    main {{
      width: min(980px, calc(100vw - 32px));
      margin: 0 auto;
      padding: 56px 0 72px;
    }}
    .hero {{
      padding: 32px;
      border: 1px solid var(--line);
      border-radius: 24px;
      background: var(--panel);
      backdrop-filter: blur(12px);
      box-shadow: var(--shadow);
    }}
    .eyebrow {{
      font-size: 12px;
      font-weight: 800;
      letter-spacing: .12em;
      text-transform: uppercase;
      color: var(--accent);
    }}
    h1 {{
      margin: 10px 0 12px;
      font-size: clamp(36px, 6vw, 72px);
      line-height: .98;
    }}
    .lead {{
      margin: 0;
      max-width: 700px;
      color: var(--muted);
      font-size: 17px;
      line-height: 1.8;
    }}
    .meta {{
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      margin-top: 22px;
    }}
    .pill {{
      padding: 10px 14px;
      border: 1px solid var(--line);
      border-radius: 999px;
      background: rgba(255,255,255,.72);
      color: var(--muted);
      font-size: 14px;
    }}
    .actions {{
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      margin-top: 26px;
    }}
    .button {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      padding: 12px 18px;
      border-radius: 999px;
      text-decoration: none;
      font-weight: 700;
      border: 1px solid transparent;
      background: var(--accent);
      color: var(--accent-ink);
    }}
    .button.secondary {{
      border-color: var(--line);
      background: rgba(255,255,255,.76);
      color: var(--ink);
    }}
    .preview {{
      margin-top: 24px;
      overflow: hidden;
      border-radius: 20px;
      border: 1px solid var(--line);
      background: rgba(255,255,255,.86);
      box-shadow: var(--shadow);
    }}
    iframe {{
      display: block;
      width: 100%;
      min-height: 78vh;
      border: 0;
      background: white;
    }}
    @media (max-width: 720px) {{
      main {{ width: min(100vw - 20px, 980px); padding-top: 24px; }}
      .hero {{ padding: 24px; border-radius: 20px; }}
      iframe {{ min-height: 68vh; }}
    }}
  </style>
</head>
<body>
  <main>
    <section class="hero">
      <div class="eyebrow">Daily Report</div>
      <h1>{safe_title}</h1>
      <p class="lead">这页是当前最新的群日报发布页。你可以直接把这个链接发给群友；如果他们想看原始长图，也能从这里继续打开 PNG 版本。</p>
      <div class="meta">
        <span class="pill">日报日期：{safe_date}</span>
        <span class="pill">页面更新：{safe_updated_at}</span>
      </div>
      <div class="actions">
        <a class="button" href="report.html">打开 HTML 正文</a>
        {png_block}
      </div>
    </section>
    <section class="preview">
      <iframe title="{safe_title}" src="report.html"></iframe>
    </section>
  </main>
</body>
</html>
"""


def main():
    args = parse_args()
    report_html = Path(args.report_html).resolve()
    report_png = Path(args.report_png).resolve()
    stats_path = Path(args.stats).resolve()
    output_dir = Path(args.output).resolve()

    if not report_html.exists():
        raise SystemExit(f"report HTML not found: {report_html}")

    stats = load_json(stats_path)
    meta = stats.get("meta", {}) if isinstance(stats, dict) else {}
    site_title = args.title or meta.get("name") or "微信群日报"
    report_date = args.date or meta.get("date") or dt.date.today().isoformat()

    output_dir.mkdir(parents=True, exist_ok=True)
    copy_file(report_html, output_dir / "report.html")
    copy_file(report_html, output_dir / "reports" / report_date / "index.html")

    has_png = report_png.exists()
    if has_png:
      copy_file(report_png, output_dir / "report.png")
      copy_file(report_png, output_dir / "reports" / report_date / "report.png")

    (output_dir / ".nojekyll").write_text("", encoding="utf-8")
    (output_dir / "index.html").write_text(
        render_index(site_title, report_date, has_png),
        encoding="utf-8",
    )

    print(f"Pages site built at: {output_dir}")


if __name__ == "__main__":
    main()
