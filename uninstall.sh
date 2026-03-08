#!/bin/bash
#
# uninstall: 卸载与 claude_config 相关的 agents, commands, skills
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_DIR="$HOME/.claude"

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 从本地目录读取列表
LOCAL_AGENTS="$SCRIPT_DIR/agents"
LOCAL_COMMANDS="$SCRIPT_DIR/commands"
LOCAL_SKILLS="$SCRIPT_DIR/skills"

# 读取本地安装的文件列表
get_local_agents() {
    if [ -d "$LOCAL_AGENTS" ]; then
        ls -1 "$LOCAL_AGENTS" 2>/dev/null | grep '\.md$' || true
    fi
}

get_local_commands() {
    if [ -d "$LOCAL_COMMANDS" ]; then
        ls -1 "$LOCAL_COMMANDS" 2>/dev/null | grep '\.md$' || true
    fi
}

get_local_skills() {
    if [ -d "$LOCAL_SKILLS" ]; then
        ls -1 "$LOCAL_SKILLS" 2>/dev/null || true
    fi
}

# 从 remote_skills.json 读取远程安装的 skills
get_remote_skills() {
    local config_file="$SCRIPT_DIR/remote_skills.json"
    if [ -f "$config_file" ]; then
        jq -r '.skills[].skills[]' "$config_file" 2>/dev/null || true
    fi
}

echo "=== Claude Config 卸载脚本 ==="
echo ""
echo "此脚本将删除以下内容："
echo ""

# 显示将要删除的内容
local_agents=($(get_local_agents))
local_commands=($(get_local_commands))
local_skills=($(get_local_skills))
remote_skills=($(get_remote_skills))

# 合并所有 skills 并去重
all_skills=($(echo "${local_skills[@]} ${remote_skills[@]}" | tr ' ' '\n' | sort -u))

if [ ${#local_agents[@]} -gt 0 ]; then
    echo "  - agents: ${local_agents[*]%.md}"
fi
if [ ${#local_commands[@]} -gt 0 ]; then
    echo "  - commands: ${local_commands[*]%.md}"
fi
if [ ${#all_skills[@]} -gt 0 ]; then
    echo "  - skills: ${all_skills[*]}"
fi
if [ ${#local_agents[@]} -eq 0 ] && [ ${#local_commands[@]} -eq 0 ] && [ ${#all_skills[@]} -eq 0 ]; then
    echo "  (无内容可卸载)"
fi
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
if [ ${#local_agents[@]} -gt 0 ]; then
    echo "[agents] 删除中..."
    for agent in "${local_agents[@]}"; do
        path="$CLAUDE_DIR/agents/$agent"
        if [ -f "$path" ]; then
            rm -v "$path"
        fi
    done
fi

# 删除 commands
if [ ${#local_commands[@]} -gt 0 ]; then
    echo ""
    echo "[commands] 删除中..."
    for cmd in "${local_commands[@]}"; do
        path="$CLAUDE_DIR/commands/$cmd"
        if [ -f "$path" ]; then
            rm -v "$path"
        fi
    done
fi

# 删除 skills
if [ ${#all_skills[@]} -gt 0 ]; then
    echo ""
    echo "[skills] 删除中..."
    for skill in "${all_skills[@]}"; do
        path="$CLAUDE_DIR/skills/$skill"
        if [ -d "$path" ]; then
            rm -rf "$path"
            echo -e "${GREEN}[已删除]${NC} $path"
        fi
    done
fi

# 清理空目录
for dir in "$CLAUDE_DIR/agents" "$CLAUDE_DIR/commands" "$CLAUDE_DIR/skills"; do
    if [ -d "$dir" ] && [ -z "$(ls -A "$dir" 2>/dev/null)" ]; then
        rmdir "$dir" 2>/dev/null && echo -e "${YELLOW}[清理]${NC} 已移除空目录: $dir" || true
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
