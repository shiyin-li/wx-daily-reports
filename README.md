# WeChat Daily Report Skill

把微信群聊天记录整理成一份可阅读、可截图、可归档的「群日报」。

这版重点重做了 UI：不再是普通统计卡片，而是接近你喜欢的群日报页面形式：左侧目录与成员过滤，右侧是今日剧情、聊天气泡、资料收纳、问答和成员观察。HTML 可以交互查看，PNG 可以直接发群或放进 Obsidian。

## 预览

![群日报预览](examples/qun-ribao-demo.png)

本仓库内置示例：

- [在线预览](https://siuserxiaowei.github.io/wechat-daily-report-skill/)
- [HTML 预览](examples/qun-ribao-demo.html)
- [PNG 长图](examples/qun-ribao-demo.png)

## 能做到什么

- 生成微信群「每日聊天记录报告」
- 汇总今日话题、资源链接、重要消息、精彩对话、问答、成员输出
- 用聊天气泡还原关键对话，不只是统计数字
- 输出交互式 HTML 和可分享 PNG 长图
- 支持按成员过滤相关内容
- 可以作为 Obsidian 归档素材：把 HTML/PNG/生成的 Markdown 放进 vault 即可

## 不能误解的地方

这不是 Obsidian 插件，也不是安装后自动打通微信的插件。

它是一个 Skill + 本地脚本工作流：先拿到微信聊天数据，再让 AI 生成结构化日报内容，最后渲染成 HTML/PNG。如果你想在 Obsidian 里长期查看聊天记录、附件和资料，需要再把导出的 Markdown/HTML/图片/附件目录放入 Obsidian vault。

## 数据来源怎么选

不是只能用 WeFlow。

| 方式 | 适合场景 | 说明 |
| --- | --- | --- |
| 手工导出的聊天文本/JSON | 最快试用 | 直接让 AI 按 `references/ai_prompt.md` 生成 `ai_content.json`，再渲染 |
| WeFlow | 推荐长期方案 | 适合做本地导出、解密、年报、本地 API，后续可以接适配器 |
| CipherTalk | 底层参考 | 更适合参考微信数据库解密与读取思路 |
| 本仓库内置脚本 | 本机微信数据分析 | 可从本地解密后的微信数据库里分析群聊并生成统计文件 |

更详细说明见 [数据来源说明](docs/data-sources.md)。

## 安装

```bash
git clone https://github.com/siuserxiaowei/wechat-daily-report-skill.git
cd wechat-daily-report-skill
python3 -m pip install -r requirements.txt
python3 -m playwright install chromium
```

如果你要作为 Codex/Claude Skill 使用，也可以把仓库放到对应 skills 目录：

```bash
mkdir -p ~/.codex/skills
git clone https://github.com/siuserxiaowei/wechat-daily-report-skill.git ~/.codex/skills/wechat-daily-report-skill
```

## 先跑一遍示例

```bash
python3 scripts/generate_report.py \
  --stats examples/sample_stats.json \
  --ai-content examples/sample_ai_content.json \
  --output examples/qun-ribao-demo.html
```

生成 PNG 长图：

```bash
python3 scripts/generate_report.py \
  --stats examples/sample_stats.json \
  --ai-content examples/sample_ai_content.json \
  --output examples/qun-ribao-demo.png \
  --viewport-width 1180 \
  --viewport-height 1400 \
  --device-scale-factor 2
```

## 生成真实群日报

### 1. 准备微信数据

如果你已经有 WeFlow、聊天导出工具、手工整理的聊天文本，直接进入第 3 步。

如果你要用本仓库的本地数据库方式：

```bash
python3 scripts/setup_check.py --ensure-decryptor
python3 scripts/decrypt_wechat.py
python3 scripts/list_wechat_groups.py
```

### 2. 分析目标群聊

```bash
python3 scripts/analyze_chat.py \
  --chatroom "群名称或 chatroom id" \
  --date 2026-04-30 \
  --output-stats stats.json \
  --output-text simplified_chat.txt
```

产物：

- `stats.json`：消息数、活跃成员、话唠榜、词云等统计数据
- `simplified_chat.txt`：压缩后的聊天文本，给 AI 生成日报内容用

### 3. 生成 AI 内容

把下面三个东西一起交给 AI：

- `references/ai_prompt.md`
- `stats.json`
- `simplified_chat.txt`

要求 AI 只输出合法 JSON，保存为：

```text
ai_content.json
```

### 4. 渲染日报

生成交互式网页：

```bash
python3 scripts/generate_report.py \
  --stats stats.json \
  --ai-content ai_content.json \
  --output report.html
```

生成可分享长图：

```bash
python3 scripts/generate_report.py \
  --stats stats.json \
  --ai-content ai_content.json \
  --output report.png \
  --viewport-width 1180 \
  --viewport-height 1400 \
  --device-scale-factor 2
```

## 放进 Obsidian

推荐目录：

```text
YourVault/
  WeChat/
    DailyReports/
      2026-04-30-report.html
      2026-04-30-report.png
      2026-04-30-ai_content.json
      2026-04-30-stats.json
```

你可以在 Obsidian 里新建一篇笔记：

```markdown
# 2026-04-30 群日报

![[2026-04-30-report.png]]

HTML 交互版：[[2026-04-30-report.html]]
```

## 项目结构

```text
assets/report_template.html      # 新版日报 UI 模板
scripts/analyze_chat.py          # 从本地微信数据生成 stats/simplified_chat
scripts/generate_report.py       # Jinja2 渲染 HTML，并用 Playwright 输出 PNG
references/ai_prompt.md          # AI 生成 ai_content.json 的提示词
examples/                        # 示例数据、HTML 和长图截图
docs/data-sources.md             # 数据来源和 WeFlow/CipherTalk 接入说明
SKILL.md                         # 给 Codex/Claude 使用的 Skill 说明
```

## 参考来源

- UI 方向参考：[群日报示例页面](https://simonlin000.github.io/qun-riba-20260430/)
- 原始 skill 思路参考：[ADVISORYDZ/wechat-daily-report-skill](https://github.com/ADVISORYDZ/wechat-daily-report-skill)
- 数据导出方向参考：[hicccc77/WeFlow](https://github.com/hicccc77/WeFlow)
- 微信解密思路参考：[ILoveBingLu/CipherTalk](https://github.com/ILoveBingLu/CipherTalk)

## License

MIT
