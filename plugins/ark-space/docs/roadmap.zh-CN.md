# 路线图与开发计划

[English](roadmap.md) | 中文

ArkSpace 正在从一组实用的本地 Skills 集合，演进为一个稳定的多 Host Agent Skills 包。本路线图采用 outcome-focused 的表达方式：每个阶段先说明用户或维护者能获得什么结果，再说明为了实现这个结果需要推进哪些开发工作。

## 产品方向

ArkSpace 应该让 Agent 工作在不同 Host 之间更容易路由、复用、验证和安装，同时避免为不同平台拆出多份 Skill 正文。

项目保留四个长期产品承诺：

- Skills 仍然是公开能力契约，放在 `skills/<skill-name>/SKILL.md`。
- Callable Agents 仍然是角色责任主体，放在 `agents/`，Host 原生输出由 `integrations/` 生成。
- Workflows 和 registries 显式描述路由、Provider 选择、来源治理和验证规则。
- 私有 Provider 配置和个人 overlays 不进入公开包。

## 路线图

| 阶段 | 目标结果 | 主要工作 | 成功信号 |
|---|---|---|---|
| 1. 调用体验 | 用户可以用短且可预测的名字调用 Agents 和 Skills。 | 保持 Agent 名称与文件名、文档、registries、生成集成和 installed-host smoke tests 一致。 | `orchestrator`、`knowledge-manager` 等短 Agent 名可以在 Codex 和 Claude Code 适配层被发现，且没有过期的 `arkspace-*` 别名残留。 |
| 2. 包可靠性 | 维护者修改 canonical sources 时，不会让生成包漂移。 | 强化 `convert`、`package-codex`、validation、stale-copy checks 和本地 cache refresh 指引。 | `python3 scripts/arkspace.py doctor` 可以清楚区分 source、package、integration 和 installed-host readiness。 |
| 3. Provider readiness | Web 和 research Skills 在缺配置时给出可执行 setup 指引，而不是静默换 Provider。 | 改进 Provider 配置诊断、key rotation 检查、setup recovery 和按 capability 拆分的 Provider registries。 | SearXNG、Exa、Firecrawl 或 Tavily 缺配置时，会给出清楚的 setup path，且不会声称执行了不支持的 fallback。 |
| 4. 知识管理深度 | Obsidian 相关 Skills 在更广义的 ArkSpace 包中继续有用。 | 明确哪些操作直接编辑文件、哪些需要 `obsidian` CLI；保持 Bases、Kanban、Canvas 和 Markdown Skills 与 Obsidian 行为一致；在 workflow 容易歧义的地方补示例。 | 知识管理任务可以在 `knowledge-manager`、`personal-assistant` 和直接 Obsidian Skills 之间清晰路由。 |
| 5. Host 扩展 | 新 Host 可以复用同一套 Skills 和 Agents，而不复制行为。 | 文档化 adapter 要求；只在 Host contract 清楚时新增 generator target；Host 专用 metadata 不进入 canonical skill bodies。 | 新 Host adapter 可以通过扩展生成和验证流程加入，而不是 fork Skills。 |
| 6. 贡献者就绪 | 外部贡献者可以添加 Skills、Providers 和 Agents，而不破坏治理契约。 | 完善 `docs/adding-skills.md`、registry 示例、source provenance 规则和 validation 错误信息。 | 新增 active public skill 时，可以明确包含来源治理、角色归属、调用 metadata，并通过 validation。 |

## 开发计划

### Workstream 1：调用与 Agent 命名

目标：让 callable agents 易记，并且在 source、generated、packaged 和 installed states 中保持一致。

计划工作：

- 保持 `registry/agents.yaml` 的 ids 与 agent frontmatter 的 `name` 一致。
- 生成文件使用短 Agent 名命名。
- `agents/` 内部 handoff 引用使用同一套短名。
- callability smoke tests 聚焦用户实际调用的名字。

验证：

```bash
python3 scripts/validate-skills.py
python3 scripts/arkspace.py doctor
python3 scripts/arkspace.py doctor --installed-host codex
```

只有刷新本地 Host cache 后，才运行 installed-host gate。

### Workstream 2：Source、Package 与 Cache 完整性

目标：让维护者能清楚判断一次改动究竟只在 source 有效、已经进入 package output，还是已经进入 installed host cache。

计划工作：

- 将 `plugins/ark-space/` 视为从 canonical root sources 生成出来的 package output。
- 将 `integrations/` 视为从 `agents/` 生成出来的派生输出。
- 改进 package 文件与 canonical 文件不一致时的 stale-copy checks。
- 在维护文档中明确什么时候运行 `convert`、`package-codex`、`doctor` 和 cache refresh 命令。

验证：

```bash
python3 scripts/arkspace.py convert --host all
python3 scripts/arkspace.py package-codex
python3 scripts/arkspace.py doctor
```

### Workstream 3：Provider Runtime 成熟度

目标：让 Provider-backed Skills 足够可靠，可以支撑常规 research 和 web workflows。

计划工作：

- 按任务形态保持 capability registries 拆分：search、fetch、map、crawl、structured extract、interaction、monitor、deep research、code context 和 related pages。
- 改进 Provider checks，确保每个 capability 验证它实际需要的 helper。
- 私有 endpoint 和 secret handling 继续留在提交包之外。
- 保持明确的 missing-configuration behavior，不假装 Provider 已经执行。

验证：

```bash
python3 scripts/arkspace.py provider check searxng --capability web_search
python3 scripts/arkspace.py provider check exa --capability web_search
python3 scripts/arkspace.py provider check tavily --capability web_search
python3 scripts/arkspace.py provider check firecrawl --capability web_search
```

Provider checks 只能证明本地配置解析可用，不能替代端到端 Host smoke tests。

### Workstream 4：Obsidian 与知识管理

目标：保留项目最初的 Obsidian 价值，同时让 ArkSpace 保持通用。

计划工作：

- 文档化哪些 Obsidian 操作需要 `obsidian` CLI，哪些只是直接文件编辑。
- 保持 `obsidian-markdown`、`obsidian-bases`、`obsidian-kanban`、`obsidian-cli` 和 `json-canvas` 聚焦且可组合。
- 让 `personal-assistant` 聚焦 Kanban-first 的个人执行系统。
- 让 `knowledge-manager` 聚焦更广义的 vault organization、Bases、Canvas、notes 和 taxonomy。

验证：

- 文件级变更：验证 Markdown、YAML、JSON 和 board structure。
- App/runtime 级变更：通过 `obsidian` CLI 在运行中的 Obsidian 实例上验证。
- Package 级变更：运行 ArkSpace 常规 validation gates。

### Workstream 5：文档与贡献者流程

目标：降低项目维护门槛，不依赖口头知识。

计划工作：

- README 保持面向用户，简洁具体。
- `docs/` 聚焦 architecture、invocation、platform support、provider setup、roadmap 和 maintenance。
- `AGENTS.md` 和 `CLAUDE.md` 保持面向 Agent。
- 添加或改造 Skills 时，让 source governance 规则足够醒目。

验证：

```bash
python3 scripts/validate-skills.py
```

当文档变更涉及结构行为、生成输出、package layout 或 Host support 时，运行更宽的 doctor command。

## 发布就绪检查

在 publish、tag 或发送版本之前，必须列出实际跑过的 workflow-level checks：

- Source registry 和 skill validation。
- Generated integration freshness。
- Codex package freshness。
- Codex 和 Claude Code 的 direct invocation smoke tests。
- 对每个声称 ready 的 Host 运行 installed-host smoke tests。
- 当 release 改动 Provider 行为时，运行 Provider capability checks。

如果当前环境无法执行其中某一项，就明确写出这个缺口，不要声称 release 已完全验证。

## 暂不纳入范围

- 为某个 Host 复制一份独立 Skill body。
- 发布 private overlays 或本地 Provider secrets。
- 将 `reference/` 内容当作 runtime package content。
- 在 invocation、packaging 和 validation contract 还不清楚前添加新 Host adapter。
