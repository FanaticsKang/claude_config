#!/bin/bash
#
# install: 将本地的 agents, commands, skills 安装到 ~/.claude 下
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_DIR="$HOME/.claude"

LOCAL_AGENTS="$SCRIPT_DIR/agents"
LOCAL_COMMANDS="$SCRIPT_DIR/commands"
LOCAL_SKILLS="$SCRIPT_DIR/skills"
LOCAL_CLAUDE_MD="$SCRIPT_DIR/CLAUDE.md"

echo "=== 安装本地文件到 ~/.claude ==="

# 安装 agents
if [ -d "$LOCAL_AGENTS" ]; then
    echo "[agents] 安装中..."
    mkdir -p "$CLAUDE_DIR/agents"
    rsync -av --delete "$LOCAL_AGENTS/" "$CLAUDE_DIR/agents/"
fi

# 安装 commands
if [ -d "$LOCAL_COMMANDS" ]; then
    echo "[commands] 安装中..."
    mkdir -p "$CLAUDE_DIR/commands"
    rsync -av --delete "$LOCAL_COMMANDS/" "$CLAUDE_DIR/commands/"
fi

# 安装 skills (保留子目录结构)
if [ -d "$LOCAL_SKILLS" ]; then
    echo "[skills] 安装中..."
    mkdir -p "$CLAUDE_DIR/skills"
    rsync -av --delete "$LOCAL_SKILLS/" "$CLAUDE_DIR/skills/"
fi

# 安装 CLAUDE.md
if [ -f "$LOCAL_CLAUDE_MD" ]; then
    echo "[CLAUDE.md] 安装中..."
    cp "$LOCAL_CLAUDE_MD" "$CLAUDE_DIR/CLAUDE.md"
fi

echo ""
echo "=== 安装完成 ==="
echo "已安装到: $CLAUDE_DIR"
