#!/bin/bash
#
# update: 将 ~/.claude 下的 agents, commands, skills 同步到当前目录并提交 git
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

CLAUDE_DIR="$HOME/.claude"
LOCAL_AGENTS="$SCRIPT_DIR/agents"
LOCAL_COMMANDS="$SCRIPT_DIR/commands"
LOCAL_SKILLS="$SCRIPT_DIR/skills"
LOCAL_CLAUDE_MD="$SCRIPT_DIR/CLAUDE.md"

echo "=== 同步 ~/.claude 到本地目录 ==="

# 同步 agents
if [ -d "$CLAUDE_DIR/agents" ]; then
    echo "[agents] 同步中..."
    mkdir -p "$LOCAL_AGENTS"
    rsync -av --delete "$CLAUDE_DIR/agents/" "$LOCAL_AGENTS/"
fi

# 同步 commands
if [ -d "$CLAUDE_DIR/commands" ]; then
    echo "[commands] 同步中..."
    mkdir -p "$LOCAL_COMMANDS"
    rsync -av --delete "$CLAUDE_DIR/commands/" "$LOCAL_COMMANDS/"
fi

# 同步 skills (保留子目录结构)
if [ -d "$CLAUDE_DIR/skills" ]; then
    echo "[skills] 同步中..."
    mkdir -p "$LOCAL_SKILLS"
    rsync -av --delete "$CLAUDE_DIR/skills/" "$LOCAL_SKILLS/"
fi

# 同步 CLAUDE.md
if [ -f "$CLAUDE_DIR/CLAUDE.md" ]; then
    echo "[CLAUDE.md] 同步中..."
    cp "$CLAUDE_DIR/CLAUDE.md" "$LOCAL_CLAUDE_MD"
fi

echo ""
echo "=== 同步完成 ==="
echo ""

# 检查是否有变更需要提交
if git diff --quiet HEAD && git diff --cached --quiet HEAD; then
    echo "没有文件变更，跳过 git 提交"
    exit 0
fi

# 使用 /summary_and_commit 提交
echo "正在执行 /summary_and_commit 提交变更..."
claude --permission-mode dontAsk --output-format text -p "/summary_and_commit"

echo ""
echo "=== 提交完成 ==="
