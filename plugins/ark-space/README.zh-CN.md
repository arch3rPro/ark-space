# ArkSpace

中文 | [English](README.md)

ArkSpace 是一个面向 Claude Code、Codex 以及兼容 AI Agent Host 的 Agent Skills 工作区。它将可复用 Skills、可调用 Agent 角色、工作流协议、Provider 路由元数据和 Host 适配层组织在一起，让 AI Agent 可以为每个任务选择聚焦、可复用的上下文。

Skills 是公开契约。运行时脚本和 Provider CLI 用于在 Skill 需要配置、搜索、提取或验证时提供支撑。

## AI Agent 如何使用 ArkSpace

在 AI Agent 会话中优先使用 slash 调用。

```text
/ark-space:orchestrator search for the claude-code-everything project
/ark-space:arxiv-search search diffusion transformers
/ark-space:exa-search search Claude Code plugin docs
/ark-space:tavily-research research the AI coding agents market
/ark-space:firecrawl-scrape scrape https://example.com
```

按意图选择入口：

| 路径 | 使用场景 |
|---|---|
| `/ark-space:orchestrator ...` | 希望 ArkSpace 自动选择角色、工作流、能力和 Provider。 |
| `/ark-space:<skill-name> ...` | 已经知道要使用哪个 Skill 或 Provider。 |
| `agents/*` | Host 支持 callable agents/subagents，需要使用角色行为配置。 |

完整调用契约和能力拆分见 [docs/invocation.md](docs/invocation.md)。

## 核心模型

ArkSpace 有四个 Host 无关的核心层：

| 层 | 作用 |
|---|---|
| `skills/` | 标准 Agent Skills。每个公开 Skill 位于 `skills/<name>/SKILL.md`。 |
| `agents/` | 可调用角色定义，组合 Skills 和 Workflows，不复制 Skill 内容。 |
| `workflows/` | 路由、交接、Provider 选择和质量门协议。 |
| `registry/` | 来源治理、角色归属、Skill 清单、Provider 元数据和验证契约。 |

Host 相关内容只是适配层：

| 路径 | 作用 |
|---|---|
| `.claude-plugin/` | Claude Code 插件元数据。 |
| `.codex-plugin/` | Codex 插件元数据。 |
| `integrations/` | 从 `agents/` 生成的 Host 原生 Agent 输出。 |
| `plugins/ark-space/` | 从标准源生成的 Codex marketplace 包。 |

Claude Code、Codex 和未来 Host 通过适配层复用同一份 Skill 文件。

## 可调用 Agents

| Agent | 职责 |
|---|---|
| `arkspace-orchestrator` | 轻量路由、Provider 配置路由、工作流选择。 |
| `arkspace-code-engineer` | 实现、重构、测试、调试。 |
| `arkspace-code-reviewer` | 缺陷、回归、风险和测试缺口审查。 |
| `arkspace-doc-writer` | 项目文档和必要的 Obsidian Markdown。 |
| `arkspace-knowledge-manager` | 笔记、Obsidian 资产、来源发现、抓取、爬取、提取。 |
| `arkspace-prd-planner` | 需求、范围、验收标准、产品决策。 |
| `arkspace-competitive-analyst` | 产品、竞品、市场和公开证据分析。 |
| `arkspace-project-manager` | 里程碑、任务拆解、风险和状态结构。 |
| `arkspace-skill-manager` | Skill 生命周期、上游来源、注册表和包完整性。 |

## Included Skills

### 核心与治理

| Skill | 作用 |
|---|---|
| `orchestrator` | 将任务路由到最小可用角色、工作流、能力和 Provider。 |
| `skill-manager` | 创建、改造、验证、来源追踪和治理 ArkSpace Skills。 |
| `provider-manager` | 配置和检查 Provider URL、Key 引用、可用性和轮询。 |

### 搜索、抓取与研究 Provider

| Skill | 作用 |
|---|---|
| `searxng-search` | 查询已配置的自托管 SearXNG 实例。 |
| `arxiv-search` | 按关键词、作者、标题、分类或 ID 搜索 arXiv 论文。 |
| `defuddle` | 通过 Defuddle CLI 将普通网页提取为干净 Markdown。 |
| `exa-search` | 语义搜索 Web、文档、仓库和限定域名来源。 |
| `exa-contents` | 通过 Exa 抓取 URL 内容、摘要、高亮和元数据。 |
| `exa-answer` | 对聚焦研究问题生成带引用的简洁回答。 |
| `exa-context` | 获取面向实现的代码上下文和 API 使用示例。 |
| `exa-similar` | 从已知 URL 查找相似页面、项目、论文、产品或竞品。 |
| `tavily-search` | 通过 Tavily 做当前 Web 搜索。 |
| `tavily-extract` | 通过 Tavily 从 URL 提取可读内容。 |
| `tavily-map` | 通过 Tavily 发现站点 URL 和结构。 |
| `tavily-crawl` | 通过 Tavily 爬取站点区域并提取多页面内容。 |
| `tavily-research` | 通过 Tavily 生成长篇带引用研究报告。 |

### Firecrawl Web 自动化

| Skill | 作用 |
|---|---|
| `firecrawl-search` | 通过 Firecrawl CLI 搜索，可选抓取搜索结果。 |
| `firecrawl-scrape` | 通过 Firecrawl CLI 抓取渲染页面或难提取页面。 |
| `firecrawl-map` | 通过 Firecrawl CLI 发现站点 URL。 |
| `firecrawl-crawl` | 通过 Firecrawl CLI 爬取站点区域。 |
| `firecrawl-agent` | 运行 schema 驱动的 Firecrawl Agent 提取。 |
| `firecrawl-browser` | 控制 Firecrawl 远程浏览器会话。 |
| `firecrawl-interact` | 与 Firecrawl 抓取页面会话交互。 |
| `firecrawl-monitor` | 管理 Firecrawl 定时监控。 |

### 知识管理与 Obsidian 工具

| Skill | 作用 |
|---|---|
| `json-canvas` | 创建和编辑 JSON Canvas 文件。 |
| `obsidian-bases` | 创建和编辑 Obsidian Bases。 |
| `obsidian-cli` | 通过 CLI 操作 Obsidian。 |
| `obsidian-kanban` | 创建和维护 Obsidian Kanban 看板。 |
| `obsidian-markdown` | 创建和编辑 Obsidian 风格 Markdown。 |

Obsidian 相关 Skills 作为知识管理工具保留在更完整的 ArkSpace 包中。

## Provider 配置

ArkSpace 将私有 Provider 配置保存在公开仓库之外。当 Provider 缺少 URL 或 API Key 时，Skill 应该引导用户通过本地配置和私有密钥完成设置。

Provider 设置支持：

- SearXNG 这类自托管服务地址
- Exa、Tavily、Firecrawl 这类 API Provider
- 多个 API Key 轮询
- 本地私有密钥存储或环境变量引用

命令设置、手动恢复和 Agent 引导设置见 [docs/provider-configuration.md](docs/provider-configuration.md)。

## 文档

| 文档 | 作用 |
|---|---|
| [docs/invocation.md](docs/invocation.md) | Slash 调用、直接 Skill、Orchestrator 路由、能力拆分。 |
| [docs/provider-configuration.md](docs/provider-configuration.md) | Provider URL、API Key、多 Key 轮询和配置恢复。 |
| [docs/maintenance.md](docs/maintenance.md) | 维护者验证、打包、Host 缓存检查和本地开发命令。 |
| [docs/architecture.md](docs/architecture.md) | 框架分层和运行入口。 |
| [docs/adding-skills.md](docs/adding-skills.md) | 如何新增或改造 Skills。 |
| [docs/platform-support.md](docs/platform-support.md) | Host 适配要求和支持说明。 |
| [docs/improvement-backlog.md](docs/improvement-backlog.md) | 框架优化 Backlog。 |

## 开发契约

- 标准 Skills 放在 `skills/<skill-name>/SKILL.md`。
- 可调用 Agent 源文件放在 `agents/`。
- 编排协议放在 `workflows/`。
- Host 专用信息只放在适配层目录。
- Provider 和来源治理放在 `registry/`。
- `integrations/` 从 `agents/` 生成，是派生输出。
- 私有配置不进入公开包。

维护者验证和打包命令见 [docs/maintenance.md](docs/maintenance.md)。
