# Claude Config

个人 Claude Code 配置仓库，包含自定义 agents、commands 和 skills。

## 项目结构

```
.
├── agents/                 # 自定义 Agent 定义
│
├── commands/              # 自定义 Slash Commands
│
├── skills/                # 自定义 Skills
│
├── claude_md_files/
│   └── CLAUDE.md          # Claude 全局配置
│
├── install.sh             # 安装脚本
├── uninstall.sh           # 卸载脚本
└── test/                  # 测试数据
```

## 安装

```bash
./install.sh
```

安装脚本会将所有配置同步到 `~/.claude/` 目录下。

**安装输出示例：**

```
==========================================
      Claude Config 安装工具
==========================================

=== [agents] ===
  [未变] algorithm.md
  [未变] architect.md
  [未变] label_prompt_pro.md

=== [commands] ===
  [未变] check_new_code.md
  [未变] git_summary.md
  ...

=== [skills] ===
  [未变] find-skills/
  [修改] json_analysis/    # 内部文件有变更
  [未变] skill-creator/

==========================================
              安装完成
==========================================

汇总统计:
  新增: 0
  修改: 1
  删除: 0
  未变: 15
```

## 卸载

```bash
./uninstall.sh
```

卸载脚本会删除 `~/.claude/` 下的所有相关配置。

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
| `/prompt_check_input_follow_LLM` | 分析输入对 LLM 的适配性 |
| `/prompt_check_task_follow_LLM` | 分析任务对 LLM 的适配性 |
| `/simplify_your_code` | 简化代码，提升可读性 |
| `/summary_and_commit` | 自动总结并提交 Git 更改 |

### Skills

| Skill | 用途 |
|-------|------|
| `find-skills` | 帮助发现和安装可用的 skills |
| `git-email-rewrite` | 修改 Git 提交历史中的邮箱地址 |
| `json_analysis` | 分析大型 JSON 文件结构，生成文档 |
| `skill-creator` | 创建、测试和优化 skills |

## CLAUDE.md 配置

全局编码规范配置，包含：
- 项目约定
- 命名风格（snake_case / PascalCase）
- 防止过度设计原则
- 工作流程规范

## 依赖

- Claude Code CLI
- Python 3.x（用于部分 skills 脚本）
- rsync（用于 install.sh）

## License

MIT
