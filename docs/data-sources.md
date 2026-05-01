# 数据来源说明

这套日报模板只关心两类输入：

- `stats.json`：统计信息，比如消息数、活跃成员、话唠榜、词云、熬夜冠军
- `ai_content.json`：AI 生成的结构化日报内容，比如话题、资料、对话、问答、成员画像

所以数据来源可以换，不需要被某一种工具绑死。

## 推荐方案：jackwener/wx-cli

现在推荐把 `jackwener/wx-cli` 作为微信聊天记录入口。

安装：

```bash
npm install -g @jackwener/wx-cli
```

初始化后，确认能读取会话：

```bash
wx sessions
```

生成日报输入：

```bash
python3 scripts/wx_cli_to_report.py \
  --chatroom "群名称或 chatroom id" \
  --date 2026-04-30 \
  --limit 5000 \
  --output-stats stats.json \
  --output-text simplified_chat.txt \
  --raw-output raw_wx_history.json
```

内部等价于调用：

```bash
wx history "群名称或 chatroom id" --since 2026-04-30 --until 2026-04-30 -n 5000 --json
```

## 备用方案：本地 wechat-cli 包

如果暂时获取不到 `wx-cli`，可以用本地的 `wechat-cli-pkg.tar.gz`：

```bash
tar -xzf /path/to/wechat-cli-pkg.tar.gz -C /tmp/wechat-cli-pkg
python3 scripts/wx_cli_to_report.py \
  --binary /tmp/wechat-cli-pkg/wechat-cli-pkg/wechat-cli/node_modules/@canghe_ai/wechat-cli-darwin-arm64/bin/wechat-cli \
  --chatroom "群名称或 chatroom id" \
  --date 2026-04-30 \
  --limit 5000 \
  --output-stats stats.json \
  --output-text simplified_chat.txt
```

适配器会按 `wechat-cli` 参数调用：

```bash
wechat-cli history "群名称或 chatroom id" --start-time 2026-04-30 --end-time 2026-04-30 --limit 5000 --format json
```

## 方案 A：手工导出的聊天文本

适合最快试用。

1. 从微信或其他工具导出当天聊天文本
2. 让 AI 按 `references/ai_prompt.md` 生成 `ai_content.json`
3. 手工或脚本补一个最小 `stats.json`
4. 执行 `scripts/generate_report.py` 渲染

## 方案 B：WeFlow

适合长期方案。

WeFlow 做得更靠近完整产品路线：导出、解密、年报、本地 API 都可以作为另一个上游能力。本仓库可以把 WeFlow 输出的数据转成下面两个文件：

```text
stats.json
ai_content.json
```

后续如果要深度接入，建议新增一个适配脚本：

```text
scripts/adapters/weflow_to_report.py
```

它负责从 WeFlow 的导出目录或本地 API 读取消息、附件、成员信息，再生成本仓库需要的输入格式。

## 方案 C：CipherTalk

适合底层研究和解密链路参考。

CipherTalk 更偏数据库解密和读取思路，适合作为本地微信数据读取层的技术参考。它不是最终日报 UI，但可以帮助你理解微信数据如何从本地库进入可分析结构。

## 方案 D：本仓库内置脚本

适合直接从本机解密后的微信数据库生成日报统计。

```bash
python3 scripts/setup_check.py --ensure-decryptor
python3 scripts/decrypt_wechat.py
python3 scripts/list_wechat_groups.py
python3 scripts/analyze_chat.py --chatroom "群名称或 chatroom id" --date 2026-04-30
```

这条路线会生成：

- `stats.json`
- `simplified_chat.txt`

然后你再用 AI 根据 `simplified_chat.txt` 生成 `ai_content.json`。

## Obsidian 怎么接

这套 skill 生成的是可归档素材，不是 Obsidian 插件。

推荐把日报产物放到 vault 中：

```text
WeChat/DailyReports/2026-04-30-report.html
WeChat/DailyReports/2026-04-30-report.png
WeChat/DailyReports/2026-04-30-stats.json
WeChat/DailyReports/2026-04-30-ai_content.json
```

如果你想进一步做到“聊天记录、附件、链接资料全量进入 Obsidian”，建议把 WeFlow 作为上游导出器，再写一个 Obsidian vault 适配器，把消息转为 Markdown，把附件复制到 `attachments/`。
