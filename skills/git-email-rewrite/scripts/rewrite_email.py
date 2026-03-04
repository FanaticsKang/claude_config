#!/usr/bin/env python3
"""
Git 邮箱重写辅助脚本
用于查找和替换 Git 提交历史中的邮箱地址
"""

import subprocess
import sys
import re
import fnmatch
from typing import List, Tuple, Set


def run_git_command(args: List[str]) -> str:
    """执行 git 命令并返回输出"""
    result = subprocess.run(
        ["git"] + args,
        capture_output=True,
        text=True,
        check=True
    )
    return result.stdout.strip()


def find_matching_commits(pattern: str) -> List[Tuple[str, str, str]]:
    """
    查找匹配指定模式的提交
    返回: [(commit_hash, author_email, author_name), ...]
    """
    log_output = run_git_command([
        "log", "--all", "--format=%H|%ae|%an|%ce|%cn"
    ])

    matches = []
    for line in log_output.split('\n'):
        if not line:
            continue
        parts = line.split('|')
        if len(parts) >= 4:
            commit_hash, author_email, author_name, committer_email = parts[:4]
            # 使用 shell 风格的通配符匹配
            if fnmatch.fnmatch(author_email, pattern) or fnmatch.fnmatch(committer_email, pattern):
                matches.append((commit_hash, author_email, author_name))

    return matches


def get_unique_emails(pattern: str) -> Set[str]:
    """获取匹配模式的所有唯一邮箱地址"""
    log_output = run_git_command([
        "log", "--all", "--format=%ae\n%ce"
    ])

    emails = set()
    for email in log_output.split('\n'):
        email = email.strip()
        if email and fnmatch.fnmatch(email, pattern):
            emails.add(email)

    return emails


def generate_filter_script(old_pattern: str, new_email: str, new_name: str = None) -> str:
    """生成 git filter-branch 的 env-filter 脚本"""

    name_script = f'export GIT_AUTHOR_NAME="{new_name}"\n    export GIT_COMMITTER_NAME="{new_name}"' if new_name else ""

    # 使用通配符匹配
    script = f'''case "$GIT_AUTHOR_EMAIL" in
    {old_pattern})
        export GIT_AUTHOR_EMAIL="{new_email}"
        {name_script}
        ;;
esac

case "$GIT_COMMITTER_EMAIL" in
    {old_pattern})
        export GIT_COMMITTER_EMAIL="{new_email}"
        {name_script}
        ;;
esac'''

    return script


def rewrite_history(old_pattern: str, new_email: str, new_name: str = None) -> bool:
    """执行历史重写"""
    try:
        # 构建 env-filter 脚本
        env_filter = f'''
OLD_PATTERN="{old_pattern}"
NEW_EMAIL="{new_email}"
{('NEW_NAME="' + new_name + '"') if new_name else ''}

# 使用通配符匹配
if [[ "$GIT_AUTHOR_EMAIL" == $OLD_PATTERN ]]; then
    export GIT_AUTHOR_EMAIL="$NEW_EMAIL"
    {('export GIT_AUTHOR_NAME="$NEW_NAME"') if new_name else ''}
fi

if [[ "$GIT_COMMITTER_EMAIL" == $OLD_PATTERN ]]; then
    export GIT_COMMITTER_EMAIL="$NEW_EMAIL"
    {('export GIT_COMMITTER_NAME="$NEW_NAME"') if new_name else ''}
fi
'''

        subprocess.run([
            "git", "filter-branch", "-f",
            "--env-filter", env_filter,
            "--tag-name-filter", "cat",
            "--", "--all"
        ], check=True, capture_output=False)

        return True
    except subprocess.CalledProcessError as e:
        print(f"重写历史失败: {e}", file=sys.stderr)
        return False


def cleanup_refs():
    """清理备份引用和 reflog"""
    import shutil
    import os

    # 删除备份引用
    original_refs = ".git/refs/original"
    if os.path.exists(original_refs):
        shutil.rmtree(original_refs)

    # 清理 reflog
    subprocess.run(["git", "reflog", "expire", "--expire=now", "--all"],
                   check=False, capture_output=True)

    # 垃圾回收
    subprocess.run(["git", "gc", "--prune=now", "--aggressive"],
                   check=False, capture_output=True)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="重写 Git 提交历史中的邮箱")
    parser.add_argument("old_pattern", help="要匹配的旧邮箱模式（支持通配符 *）")
    parser.add_argument("new_email", help="新的邮箱地址")
    parser.add_argument("--new-name", "-n", help="新的用户名（可选）")
    parser.add_argument("--dry-run", "-d", action="store_true",
                        help="仅显示匹配结果，不执行重写")

    args = parser.parse_args()

    print(f"=== Git 邮箱重写 ===")
    print(f"搜索模式: {args.old_pattern}")
    print(f"新邮箱: {args.new_email}")
    if args.new_name:
        print(f"新用户名: {args.new_name}")
    print()

    # 查找匹配的邮箱
    unique_emails = get_unique_emails(args.old_pattern)

    if not unique_emails:
        print("未找到匹配的邮箱地址")
        return 0

    print(f"找到 {len(unique_emails)} 个唯一邮箱:")
    for email in sorted(unique_emails):
        print(f"  - {email}")
    print()

    # 查找匹配的具体提交
    commits = find_matching_commits(args.old_pattern)
    print(f"影响 {len(commits)} 个提交")
    print()

    if args.dry_run:
        print("(试运行模式，未执行实际修改)")
        return 0

    # 确认执行
    response = input("确认执行替换? [y/N]: ")
    if response.lower() != 'y':
        print("已取消")
        return 0

    print("\n重写历史记录中...")
    if rewrite_history(args.old_pattern, args.new_email, args.new_name):
        print("重写完成")

        print("\n清理历史记录...")
        cleanup_refs()

        # 验证结果
        remaining = get_unique_emails(args.old_pattern)
        if remaining:
            print(f"\n警告: 仍有 {len(remaining)} 个邮箱未替换:")
            for email in remaining:
                print(f"  - {email}")
        else:
            print("\n✓ 所有匹配的邮箱已成功替换")

        print("\n最近的提交:")
        subprocess.run(["git", "log", "--oneline", "-5"])

        print("\n=== 完成 ===")
        print("提示: 使用 'git push --force' 推送修改后的历史")
        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())
