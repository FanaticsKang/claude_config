#!/bin/bash
# Claude Config 安装脚本
# 功能：读取 remote_config.json，同步本地组件，输出插件安装命令

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIG_FILE="$SCRIPT_DIR/remote_config.json"

echo -e "${BOLD}========================================${NC}"
echo -e "${BOLD}    Claude Config 安装工具${NC}"
echo -e "${BOLD}========================================${NC}"
echo ""

# ============================================
# 检查配置文件
# ============================================
if [ ! -f "$CONFIG_FILE" ]; then
    echo -e "${RED}错误: 配置文件不存在: $CONFIG_FILE${NC}"
    exit 1
fi

# ============================================
# 解析 remote_config.json
# ============================================
echo -e "${YELLOW}读取配置文件...${NC}"

# 使用 Python 解析 JSON 并生成安装命令
PLUGINS_CMD=$(python3 -c "
import json
import sys

with open('$CONFIG_FILE', 'r') as f:
    config = json.load(f)

if config.get('version') != '3.0':
    print('警告: 配置版本不是 3.0', file=sys.stderr)

commands = []

for plugin in config.get('plugins', []):
    plugin_type = plugin.get('type')

    if plugin_type == 'official':
        plugins_list = plugin.get('plugins', [])
        for p in plugins_list:
            commands.append(f'/plugin install {p}@claude-plugins-official')

    elif plugin_type == 'marketplace':
        repo = plugin.get('repo', '')
        if repo:
            commands.append(f'/plugin marketplace add {repo}')

for cmd in commands:
    print(cmd)
" 2>&1)

if [ -z "$PLUGINS_CMD" ]; then
    echo -e "${RED}错误: 未找到任何插件配置${NC}"
    exit 1
fi

# 统计命令数量
PLUGIN_COUNT=$(echo "$PLUGINS_CMD" | grep -c '/plugin install' || true)
MARKETPLACE_COUNT=$(echo "$PLUGINS_CMD" | grep -c '/plugin marketplace' || true)

echo -e "  ${GREEN}官方插件: $PLUGIN_COUNT 个${NC}"
echo -e "  ${GREEN}Marketplace: $MARKETPLACE_COUNT 个${NC}"
echo ""

# ============================================
# 同步本地组件
# ============================================
echo -e "${YELLOW}同步本地组件...${NC}"

# 同步 agents
if [ -d "$SCRIPT_DIR/agents" ] && [ "$(ls -A "$SCRIPT_DIR/agents" 2>/dev/null)" ]; then
    echo -e "  ${GREEN}同步 agents...${NC}"
    rsync -av --delete "$SCRIPT_DIR/agents/" "$HOME/.claude/agents/"
fi

# 同步 commands
if [ -d "$SCRIPT_DIR/commands" ] && [ "$(ls -A "$SCRIPT_DIR/commands" 2>/dev/null)" ]; then
    echo -e "  ${GREEN}同步 commands...${NC}"
    rsync -av --delete "$SCRIPT_DIR/commands/" "$HOME/.claude/commands/"
fi

# 同步 skills
if [ -d "$SCRIPT_DIR/skills" ] && [ "$(ls -A "$SCRIPT_DIR/skills" 2>/dev/null)" ]; then
    echo -e "  ${GREEN}同步 skills...${NC}"
    rsync -av --delete "$SCRIPT_DIR/skills/" "$HOME/.claude/skills/"
fi

# 同步 CLAUDE.md
if [ -f "$SCRIPT_DIR/claude_md_files/CLAUDE.md" ]; then
    echo -e "  ${GREEN}同步 CLAUDE.md...${NC}"
    cp "$SCRIPT_DIR/claude_md_files/CLAUDE.md" "$HOME/.claude/CLAUDE.md"
fi

echo ""

# ============================================
# 输出插件安装命令
# ============================================
echo -e "${BOLD}========================================${NC}"
echo -e "${GREEN}本地组件同步完成！${NC}"
echo -e "${BOLD}========================================${NC}"
echo ""
echo -e "${YELLOW}请在 Claude Code 中执行以下命令安装插件：${NC}"
echo ""

# 添加序号
echo "$PLUGINS_CMD" | nl -w2 -s'. '

echo ""
