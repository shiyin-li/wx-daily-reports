#!/usr/bin/env python3
"""Build an anonymized GitHub Pages demo site.

The public Pages site is only for showing the daily-report experience. It must
not expose real group names, member names, avatars, chat snippets, links, word
clouds, or other details from private chats.
"""

from __future__ import annotations

import argparse
import html
from pathlib import Path


GROUPS = [
    ("group-1", "一群"),
    ("group-2", "二群"),
    ("group-3", "三群"),
    ("group-4", "四群"),
    ("group-5", "五群"),
]

LEGACY_GROUPS = [
    ("dontbesilent-money", "一群"),
    ("pengtao-vip", "二群"),
    ("yanhua-vip-1", "三群"),
    ("simonlin-ai", "四群"),
    ("ai-tools-vibecoding-5", "五群"),
]


CSS = """
:root {
  color-scheme: light;
  --ink: #18231f;
  --muted: #66736d;
  --line: #dbe5dc;
  --paper: #fbfaf5;
  --panel: #ffffff;
  --accent: #b95f2b;
  --accent-soft: #f5e7dc;
  --green: #2b6d58;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  min-height: 100vh;
  font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Hiragino Sans GB", "Helvetica Neue", Arial, sans-serif;
  color: var(--ink);
  background: linear-gradient(135deg, #eef4ec 0%, var(--paper) 48%, #eef2f6 100%);
}
main {
  width: min(1060px, calc(100vw - 48px));
  margin: 0 auto;
  padding: 72px 0 88px;
}
.eyebrow {
  color: var(--accent);
  font-size: 13px;
  font-weight: 800;
  letter-spacing: 0;
  text-transform: uppercase;
}
h1 {
  margin: 12px 0 12px;
  font-size: clamp(42px, 8vw, 88px);
  line-height: .96;
  letter-spacing: 0;
}
.lead {
  width: min(760px, 100%);
  margin: 0;
  color: var(--muted);
  font-size: 18px;
  line-height: 1.8;
}
.summary, .cards {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
  margin-top: 40px;
}
.metric, .card, .report-card, .notice {
  border: 1px solid var(--line);
  border-radius: 8px;
  background: rgba(255, 255, 255, .78);
  box-shadow: 0 18px 50px rgba(36, 48, 40, .06);
}
.metric { padding: 22px; }
.metric strong { display: block; font-size: 34px; line-height: 1; }
.metric span { display: block; margin-top: 10px; color: var(--muted); font-size: 14px; }
.grid { display: grid; gap: 12px; margin-top: 28px; }
.report-card {
  display: grid;
  grid-template-columns: 1fr auto auto;
  align-items: center;
  gap: 16px;
  padding: 20px 22px;
  color: inherit;
  text-decoration: none;
}
.report-card:hover { border-color: #c9d7cd; transform: translateY(-1px); }
.slug { font-size: 19px; font-weight: 800; }
.day { color: var(--muted); font-variant-numeric: tabular-nums; }
.arrow {
  padding: 8px 11px;
  border-radius: 999px;
  background: var(--accent-soft);
  color: var(--accent);
  font-size: 12px;
  font-weight: 800;
  text-transform: uppercase;
}
.hero {
  margin-top: 38px;
  padding: 34px;
  border-radius: 8px;
  color: #fff9ed;
  background: linear-gradient(135deg, rgba(31, 43, 36, .96), rgba(54, 73, 84, .92), rgba(116, 55, 35, .88));
}
.hero h2 { margin: 10px 0 14px; font-size: clamp(42px, 7vw, 76px); line-height: 1; letter-spacing: 0; }
.hero p { width: min(760px, 100%); color: rgba(255, 249, 237, .82); font-size: 18px; line-height: 1.8; }
.hero-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
  margin-top: 30px;
}
.hero-metric {
  padding: 18px;
  border: 1px solid rgba(255,255,255,.2);
  border-radius: 8px;
  background: rgba(255,255,255,.08);
}
.hero-metric strong { display: block; font-size: 34px; }
.hero-metric span { display: block; margin-top: 8px; color: rgba(255,249,237,.72); font-size: 14px; }
.section-title { margin: 46px 0 16px; font-size: 32px; letter-spacing: 0; }
.cards { grid-template-columns: repeat(2, minmax(0, 1fr)); margin-top: 0; }
.card { padding: 24px; min-height: 150px; }
.card h3 { margin: 0 0 12px; font-size: 22px; }
.card p { margin: 0; color: var(--muted); line-height: 1.75; }
.notice {
  margin-top: 32px;
  padding: 18px 20px;
  color: var(--green);
  background: #eef6ef;
}
@media (max-width: 720px) {
  main { width: min(100vw - 28px, 1060px); padding-top: 36px; }
  h1 { font-size: 46px; }
  .summary, .cards, .hero-grid { grid-template-columns: 1fr; }
  .report-card { grid-template-columns: 1fr; align-items: start; }
}
"""


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def render_index(day: str) -> str:
    cards = "\n".join(
        f'''      <a class="report-card" href="reports/{slug}/{day}/index.html"><span class="slug">{label}</span><span class="day">{day}</span><span class="arrow">open</span></a>'''
        for slug, label in GROUPS
    )
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>微信群日报演示</title>
  <style>{CSS}</style>
</head>
<body>
  <main>
    <div class="eyebrow">Wechat Daily Demo</div>
    <h1>微信群日报演示</h1>
    <p class="lead">这是对外演示页，只展示日报产品形态。真实群名、成员昵称、聊天原文、链接、头像和敏感统计都已隐藏。</p>
    <section class="summary">
      <div class="metric"><strong>5</strong><span>演示群组</span></div>
      <div class="metric"><strong>08:30</strong><span>每天自动运行</span></div>
      <div class="metric"><strong>0</strong><span>公开聊天原文</span></div>
    </section>
    <section class="grid">
{cards}
    </section>
  </main>
</body>
</html>
"""


def render_report(day: str, slug: str, title: str) -> str:
    safe_title = html.escape(title)
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{safe_title}日报演示 · {day}</title>
  <style>{CSS}</style>
</head>
<body>
  <main>
    <div class="eyebrow">Wechat Daily Demo · {day}</div>
    <section class="hero">
      <div class="eyebrow">匿名群日报</div>
      <h2>{safe_title}日报</h2>
      <p>公开页面只展示日报样式和信息组织方式。真实群名、成员昵称、头像、聊天原文、链接、词云和具体讨论内容不会出现在这里。</p>
      <div class="hero-grid">
        <div class="hero-metric"><strong>已生成</strong><span>日报状态</span></div>
        <div class="hero-metric"><strong>已归档</strong><span>Obsidian 私有库</span></div>
        <div class="hero-metric"><strong>已发布</strong><span>GitHub Pages 演示</span></div>
      </div>
    </section>

    <h2 class="section-title">日报结构演示</h2>
    <section class="cards">
      <article class="card">
        <h3>今日概览</h3>
        <p>展示当天讨论是否活跃、是否有值得复盘的内容，以及是否已经写入本地知识库。</p>
      </article>
      <article class="card">
        <h3>话题提炼</h3>
        <p>把碎片化聊天归纳成几个主题，方便后续在 Obsidian 里继续整理成长期笔记。</p>
      </article>
      <article class="card">
        <h3>资料收纳</h3>
        <p>识别链接、文件、工具和案例，但公开演示页不会展示真实链接或原始分享人。</p>
      </article>
      <article class="card">
        <h3>行动项</h3>
        <p>把需要跟进的想法、问题和待办沉淀下来，第二天可以继续追踪。</p>
      </article>
    </section>

    <div class="notice">隐私说明：完整聊天记录和详细分析只保存在本地 Obsidian；公开页面仅用于展示产品效果。</div>
  </main>
</body>
</html>
"""


def build(output: Path, day: str) -> None:
    write(output / "index.html", render_index(day))
    for slug, title in GROUPS:
        write(output / "reports" / slug / day / "index.html", render_report(day, slug, title))
    for slug, title in LEGACY_GROUPS:
        write(output / "reports" / slug / day / "index.html", render_report(day, slug, title))


def main() -> int:
    parser = argparse.ArgumentParser(description="Build anonymized public demo pages")
    parser.add_argument("--output", default=".", help="GitHub Pages repository root")
    parser.add_argument("--date", default="2026-05-01", help="Demo report date")
    args = parser.parse_args()
    build(Path(args.output), args.date)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
