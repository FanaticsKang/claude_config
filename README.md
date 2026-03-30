# Claude Config

个人 Claude Code 配置仓库，包含自定义 agents、commands 和 skills。

## 项目结构

```
.
├── .claude/               # Claude Code 配置目录
│   └── settings.local.json
│
├── agents/                # 自定义 Agent 定义
│
├── claude_md_files/       # Claude 全局配置
│   └── CLAUDE.md
│
├── commands/              # 自定义 Slash Commands
│
├── skills/                # 本地 Skills
│
├── special_skills/        # 特殊 Skills
│
├── test/                  # 测试数据
│
├── .gitignore             # Git 忽略文件
├── install.sh             # 安装脚本
├── remote_config.json     # 远程插件配置 (v3.0)
└── README.md              # 项目说明
```

## 安装

### 1. 同步本地组件

```bash
./install.sh
```

脚本会同步 agents、commands、skills 和 CLAUDE.md 到 `~/.claude/` 目录。

### 2. 安装插件

在 Claude Code 对话中执行以下命令：

```bash
# 官方插件（18个）
/plugin install agent-sdk-dev@claude-plugins-official
/plugin install clangd-lsp@claude-plugins-official
/plugin install claude-code-setup@claude-plugins-official
/plugin install claude-md-management@claude-plugins-official
/plugin install code-review@claude-plugins-official
/plugin install code-simplifier@claude-plugins-official
/plugin install commit-commands@claude-plugins-official
/plugin install example-plugin@claude-plugins-official
/plugin install explanatory-output-style@claude-plugins-official
/plugin install feature-dev@claude-plugins-official
/plugin install frontend-design@claude-plugins-official
/plugin install learning-output-style@claude-plugins-official
/plugin install playground@claude-plugins-official
/plugin install plugin-dev@claude-plugins-official
/plugin install pr-review-toolkit@claude-plugins-official
/plugin install pyright-lsp@claude-plugins-official
/plugin install ralph-loop@claude-plugins-official
/plugin install skill-creator@claude-plugins-official

# Marketplace
/plugin marketplace add obra/superpowers-marketplace
```

将 `agents/`、`commands/`、`skills/` 目录复制到 `~/.claude/` 对应目录：

```bash
# 复制 agents
rsync -av agents/ ~/.claude/agents/

# 复制 commands
rsync -av commands/ ~/.claude/commands/

# 复制 skills
rsync -av skills/ ~/.claude/skills/

# 复制 CLAUDE.md
cp claude_md_files/CLAUDE.md ~/.claude/
```

## remote_config.json 配置

配置格式 v3.0：

```json
{
  "version": "3.0",
  "plugins": [
    {
      "name": "claude-plugins-official",
      "type": "official",
      "plugins": []           // 空数组表示安装全部官方插件
    },
    {
      "name": "superpowers-marketplace",
      "type": "marketplace",
      "repo": "obra/superpowers-marketplace",
      "agents": [],
      "skills": []
    }
  ]
}
```

**配置说明：**

| 字段 | 说明 |
|-----|------|
| `type: official` | Claude 官方插件 |
| `type: marketplace` | GitHub Marketplace 插件 |
| `plugins` | 空数组 = 安装全部，指定名称 = 选择性安装 |

## 组件说明

### Agents

| Agent | 用途 |
|-------|------|
| `algorithm` | 自动驾驶算法专家，专注算法设计与优化 |
| `architect` | 架构设计专家，负责系统级技术整合 |
| `label_prompt_pro` | 提示词专家，擅长图像标注提示词设计 |

### Commands

| Command | 功能 |
|---------|------|
| `/check_new_code` | 检查新代码是否符合编码规范 |
| `/git_summary` | 总结 Git 提交历史 |
| `/plot_in_vcs` | 使用 matplotlib 可视化 VCS 数据 |
| `/simplify_your_code` | 简化代码，提升可读性 |
| `/summary_and_commit` | 自动总结并提交 Git 更改 |

### Skills

| Skill | 用途 | 类型 |
|-------|------|------|
| `json_analysis` | 分析大型 JSON 文件结构，生成文档 | 本地 |
| `pdf` | PDF 文件处理（读取、合并、拆分等） | 远程 |
| `skill-creator` | 创建、测试和优化 skills | 远程 |
| `superpowers` | 开发工作流增强技能集 | 远程 |

**说明：**
- **本地**：位于 `skills/` 目录，随仓库一起管理
- **远程**：通过 `/plugin install` 安装

## CLAUDE.md 配置

全局编码规范配置，包含：
- 项目约定
- 命名风格（snake_case / PascalCase）
- 防止过度设计原则
- 工作流程规范

## 依赖

- Claude Code CLI
- rsync（用于 install.sh）

## License

MIT
