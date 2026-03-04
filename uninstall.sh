#!/bin/bash
#
# uninstall: 卸载与 claude_config 相关的 agents, commands, skills
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_DIR="$HOME/.claude"

echo "=== Claude Config 卸载脚本 ==="
echo ""
echo "此脚本将删除以下内容："
echo "  - agents: algorithm, architect, label_prompt_pro"
echo "  - commands: check_new_code, git_summary, plot_in_vcs,"
echo "              prompt_check_input_follow_LLM, prompt_check_task_follow_LLM,"
echo "              simplify_your_code, summary_and_commit"
echo "  - skills: find-skills, git-email-rewrite, json_analysis, skill-creator"
echo ""

read -p "确认卸载? (y/N): " confirm
if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
    echo "已取消卸载"
    exit 0
fi

echo ""
echo "=== 开始卸载 ==="
echo ""

# 删除 agents
echo "[agents] 删除中..."
AGENTS=("algorithm.md" "architect.md" "label_prompt_pro.md")
for agent in "${AGENTS[@]}"; do
    path="$CLAUDE_DIR/agents/$agent"
    if [ -f "$path" ]; then
        rm -v "$path"
    fi
done

# 删除 commands
echo ""
echo "[commands] 删除中..."
COMMANDS=("check_new_code.md" "git_summary.md" "plot_in_vcs.md"
          "prompt_check_input_follow_LLM.md" "prompt_check_task_follow_LLM.md"
          "simplify_your_code.md" "summary_and_commit.md")
for cmd in "${COMMANDS[@]}"; do
    path="$CLAUDE_DIR/commands/$cmd"
    if [ -f "$path" ]; then
        rm -v "$path"
    fi
done

# 删除 skills
echo ""
echo "[skills] 删除中..."
SKILLS=("find-skills" "git-email-rewrite" "json_analysis" "skill-creator")
for skill in "${SKILLS[@]}"; do
    path="$CLAUDE_DIR/skills/$skill"
    if [ -d "$path" ]; then
        rm -rf "$path"
        echo "已删除: $path"
    fi
done

# 清理空目录
for dir in "$CLAUDE_DIR/agents" "$CLAUDE_DIR/commands" "$CLAUDE_DIR/skills"; do
    if [ -d "$dir" ] && [ -z "$(ls -A "$dir" 2>/dev/null)" ]; then
        rmdir "$dir" 2>/dev/null && echo "已移除空目录: $dir" || true
    fi
done

echo ""
echo "=== 卸载完成 ==="
echo ""

# 提示是否删除项目目录
echo "项目目录: $SCRIPT_DIR"
read -p "是否删除项目目录本身? (y/N): " remove_project
if [[ "$remove_project" == "y" || "$remove_project" == "Y" ]]; then
    echo "删除项目目录..."
    rm -rf "$SCRIPT_DIR"
    echo "项目已完全移除"
else
    echo "保留项目目录（仅移除了 ~/.claude 下的配置）"
fi

echo ""
echo "卸载完成！"
