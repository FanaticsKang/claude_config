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
LOCAL_CLAUDE_MD="$SCRIPT_DIR/claude_md_files/CLAUDE.md"

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 计数器
ADDED=0
MODIFIED=0
DELETED=0
UNCHANGED=0

# 比较两个文件是否相同
files_equal() {
    local src="$1"
    local dst="$2"
    if [ ! -f "$dst" ]; then
        return 1
    fi
    if diff -q "$src" "$dst" > /dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# 处理目录安装（详细模式 - 显示每个文件）
install_directory_detailed() {
    local src_dir="$1"
    local dst_dir="$2"
    local name="$3"

    if [ ! -d "$src_dir" ]; then
        return
    fi

    echo ""
    echo "=== [$name] ==="
    echo ""

    mkdir -p "$dst_dir"

    # 创建临时文件存储所有文件列表
    local tmp_all_files=$(mktemp)
    local tmp_src_files=$(mktemp)
    local tmp_dst_files=$(mktemp)

    # 收集源目录中的文件
    if [ -d "$src_dir" ]; then
        find "$src_dir" -type f 2>/dev/null | sed "s|^$src_dir/||" | sort > "$tmp_src_files"
    fi

    # 收集目标目录中的文件
    if [ -d "$dst_dir" ]; then
        find "$dst_dir" -type f 2>/dev/null | sed "s|^$dst_dir/||" | sort > "$tmp_dst_files"
    fi

    # 合并所有文件（去重）
    cat "$tmp_src_files" "$tmp_dst_files" 2>/dev/null | sort -u > "$tmp_all_files"

    # 显示每个文件的状态
    local has_output=false
    while IFS= read -r rel_path; do
        [ -z "$rel_path" ] && continue

        local src_file="$src_dir/$rel_path"
        local dst_file="$dst_dir/$rel_path"

        # 跳过目录占位符
        if [[ "$rel_path" == */.gitkeep ]]; then
            continue
        fi

        # 判断状态
        if [ ! -f "$src_file" ]; then
            # 源文件不存在，标记为删除
            echo -e "  ${RED}[删除]${NC} $rel_path"
            DELETED=$((DELETED + 1))
            has_output=true
        elif [ ! -f "$dst_file" ]; then
            # 目标文件不存在，标记为新增
            echo -e "  ${GREEN}[新增]${NC} $rel_path"
            ADDED=$((ADDED + 1))
            has_output=true
        elif files_equal "$src_file" "$dst_file"; then
            # 文件相同，标记为未变更
            echo -e "  ${BLUE}[未变]${NC} $rel_path"
            UNCHANGED=$((UNCHANGED + 1))
            has_output=true
        else
            # 文件不同，标记为修改
            echo -e "  ${YELLOW}[修改]${NC} $rel_path"
            MODIFIED=$((MODIFIED + 1))
            has_output=true
        fi
    done < "$tmp_all_files"

    # 清理临时文件
    rm -f "$tmp_all_files" "$tmp_src_files" "$tmp_dst_files"

    if [ "$has_output" = false ]; then
        echo -e "  ${BLUE}[无变更]${NC}"
    fi

    # 执行 rsync 同步
    rsync -a --delete "$src_dir/" "$dst_dir/" 2>/dev/null
}

# 处理 skills 目录（按文件夹聚合显示）
install_skills() {
    local src_dir="$1"
    local dst_dir="$2"

    if [ ! -d "$src_dir" ]; then
        return
    fi

    echo ""
    echo "=== [skills] ==="
    echo ""

    mkdir -p "$dst_dir"

    # 获取所有 skill 目录
    local tmp_skills=$(mktemp)
    ls -1 "$src_dir" 2>/dev/null > "$tmp_skills"

    # 也检查目标目录中存在的 skill
    if [ -d "$dst_dir" ]; then
        ls -1 "$dst_dir" 2>/dev/null >> "$tmp_skills"
    fi

    # 去重排序
    sort -u "$tmp_skills" -o "$tmp_skills"

    local has_output=false
    while IFS= read -r skill_name; do
        [ -z "$skill_name" ] && continue

        local src_skill="$src_dir/$skill_name"
        local dst_skill="$dst_dir/$skill_name"

        # 判断状态
        if [ ! -d "$src_skill" ]; then
            # 源目录不存在，标记为删除
            echo -e "  ${RED}[删除]${NC} $skill_name/"
            DELETED=$((DELETED + 1))
            has_output=true
        elif [ ! -d "$dst_skill" ]; then
            # 目标目录不存在，标记为新增
            echo -e "  ${GREEN}[新增]${NC} $skill_name/"
            ADDED=$((ADDED + 1))
            has_output=true
        else
            # 检查 skill 内是否有文件变更
            local has_change=false
            local tmp_all_files=$(mktemp)

            # 收集源目录中的文件
            find "$src_skill" -type f 2>/dev/null | sed "s|^$src_skill/||" > "$tmp_all_files"
            # 收集目标目录中的文件
            find "$dst_skill" -type f 2>/dev/null | sed "s|^$dst_skill/||" >> "$tmp_all_files"
            # 去重
            sort -u "$tmp_all_files" -o "$tmp_all_files"

            while IFS= read -r rel_path; do
                [ -z "$rel_path" ] && continue
                [[ "$rel_path" == */.gitkeep ]] && continue

                local src_file="$src_skill/$rel_path"
                local dst_file="$dst_skill/$rel_path"

                if [ ! -f "$src_file" ] || [ ! -f "$dst_file" ]; then
                    has_change=true
                    break
                elif ! files_equal "$src_file" "$dst_file"; then
                    has_change=true
                    break
                fi
            done < "$tmp_all_files"

            rm -f "$tmp_all_files"

            if [ "$has_change" = true ]; then
                echo -e "  ${YELLOW}[修改]${NC} $skill_name/"
                MODIFIED=$((MODIFIED + 1))
            else
                echo -e "  ${BLUE}[未变]${NC} $skill_name/"
                UNCHANGED=$((UNCHANGED + 1))
            fi
            has_output=true
        fi
    done < "$tmp_skills"

    rm -f "$tmp_skills"

    if [ "$has_output" = false ]; then
        echo -e "  ${BLUE}[无变更]${NC}"
    fi

    # 执行 rsync 同步
    rsync -a --delete "$src_dir/" "$dst_dir/" 2>/dev/null
}

# 处理单个文件安装
install_file() {
    local src_file="$1"
    local dst_file="$2"
    local name="$3"

    echo ""
    echo "=== [$name] ==="
    echo ""

    if [ ! -f "$src_file" ]; then
        echo -e "  ${BLUE}[跳过]${NC} 源文件不存在"
        return
    fi

    # 判断状态
    if [ ! -f "$dst_file" ]; then
        echo -e "  ${GREEN}[新增]${NC} $name"
        ADDED=$((ADDED + 1))
    elif files_equal "$src_file" "$dst_file"; then
        echo -e "  ${BLUE}[未变]${NC} $name"
        UNCHANGED=$((UNCHANGED + 1))
    else
        echo -e "  ${YELLOW}[修改]${NC} $name"
        MODIFIED=$((MODIFIED + 1))
    fi

    # 执行复制
    cp "$src_file" "$dst_file"
}

echo "=========================================="
echo "      Claude Config 安装工具"
echo "=========================================="
echo ""
echo "源目录: $SCRIPT_DIR"
echo "目标目录: $CLAUDE_DIR"
echo ""

# 安装 agents（详细模式）
install_directory_detailed "$LOCAL_AGENTS" "$CLAUDE_DIR/agents" "agents"

# 安装 commands（详细模式）
install_directory_detailed "$LOCAL_COMMANDS" "$CLAUDE_DIR/commands" "commands"

# 安装 skills（按文件夹聚合）
install_skills "$LOCAL_SKILLS" "$CLAUDE_DIR/skills"

# 安装 CLAUDE.md
install_file "$LOCAL_CLAUDE_MD" "$CLAUDE_DIR/CLAUDE.md" "CLAUDE.md"

echo ""
echo "=========================================="
echo "              安装完成"
echo "=========================================="
echo ""
echo "汇总统计:"
echo -e "  ${GREEN}新增: $ADDED${NC}"
echo -e "  ${YELLOW}修改: $MODIFIED${NC}"
echo -e "  ${RED}删除: $DELETED${NC}"
echo -e "  ${BLUE}未变: $UNCHANGED${NC}"
echo ""
echo "已安装到: $CLAUDE_DIR"
echo ""
