---
name: git-email-rewrite
description: 修改 Git 提交历史中的作者/提交者邮箱地址。支持精确匹配和通配符模式（*）批量替换邮箱，自动清理历史记录并支持强制推送。当用户需要修改 git 历史中的错误邮箱、统一邮箱格式或迁移到新的邮箱地址时使用此 skill。
---

# Git 邮箱重写 Skill

## 用途

修改 Git 仓库提交历史中的邮箱地址，支持：
- 精确邮箱匹配替换
- 通配符模式匹配（如 `*@old.com`）
- 批量替换多个邮箱
- 自动清理 reflog 和备份引用

## 重要警告

⚠️ **这会重写 Git 提交历史**：
- 如果代码已推送到远程仓库，需要使用 `--force` 推送
- 会影响其他协作者，他们需要重新同步仓库
- 建议先备份仓库或在测试分支上验证

## 使用方法

```
/git-email-rewrite old_email=<旧邮箱> new_email=<新邮箱> [new_name=<新用户名>]
```

### 参数说明

- **old_email**（必需）：要替换的旧邮箱，支持通配符 `*`
  - 精确匹配：`old@example.com`
  - 通配符：`*@example.com`、`old@*`、`*old*`
- **new_email**（必需）：新的邮箱地址
- **new_name**（可选）：新的用户名，如果不提供则保留原名

### 使用示例

```
# 精确替换单个邮箱
/git-email-rewrite old_email=old@example.com new_email=new@example.com

# 替换整个域名的所有邮箱
/git-email-rewrite old_email=*@oldcompany.com new_email=@newcompany.com

# 替换并同时修改用户名
/git-email-rewrite old_email=john@old.com new_email=john@new.com new_name="John Doe"

# 匹配包含特定字符串的邮箱
/git-email-rewrite old_email=*test* new_email=official@company.com
```

## 工作流程

### 1. 查找匹配的提交

```bash
# 精确匹配
git log --all --format='%H %ae %an' | grep "old@example.com"

# 通配符匹配（使用 shell 通配符转换）
git log --all --format='%ae' | grep -E 'pattern'
```

### 2. 确认替换范围

执行替换前，向用户展示：
- 匹配到的提交数量
- 涉及的邮箱列表
- 请求用户确认

### 3. 执行邮箱重写

使用 `git filter-branch` 或 `git filter-repo`（如果可用）重写历史：

```bash
# 使用 filter-branch（内置）
git filter-branch -f --env-filter '
OLD_EMAIL_PATTERN="old@example.com"
NEW_EMAIL="new@example.com"
NEW_NAME="New Name"

# 检查并替换作者邮箱
if [[ "$GIT_AUTHOR_EMAIL" == $OLD_EMAIL_PATTERN ]]; then
    export GIT_AUTHOR_EMAIL="$NEW_EMAIL"
    [ -n "$NEW_NAME" ] && export GIT_AUTHOR_NAME="$NEW_NAME"
fi

# 检查并替换提交者邮箱
if [[ "$GIT_COMMITTER_EMAIL" == $OLD_EMAIL_PATTERN ]]; then
    export GIT_COMMITTER_EMAIL="$NEW_EMAIL"
    [ -n "$NEW_NAME" ] && export GIT_COMMITTER_NAME="$NEW_NAME"
fi
' --tag-name-filter cat -- --all
```

### 4. 清理历史记录

```bash
# 删除备份引用
rm -rf .git/refs/original/

# 清理 reflog
git reflog expire --expire=now --all

# 垃圾回收
git gc --prune=now --aggressive
```

### 5. 验证结果

```bash
# 检查是否还有旧邮箱
git log --all --format='%ae' | grep "old@example.com"

# 显示最近的提交历史
git log --oneline -5
```

## 实现细节

### 通配符匹配规则

- `*` 匹配任意字符序列（包括空序列）
- 内部将 shell 通配符转换为正则表达式：
  - `*@old.com` → `.*@old\.com$`
  - `user@*` → `^user@.*`
  - `*test*` → `.*test.*`

### 处理范围

- 默认处理所有分支 (`--all`)
- 同时修改作者邮箱 (`GIT_AUTHOR_EMAIL`) 和提交者邮箱 (`GIT_COMMITTER_EMAIL`)
- 保留原始时间戳
- 重写所有标签 (`--tag-name-filter cat`)

### 安全提示

1. 执行前始终显示匹配结果并请求确认
2. 提醒用户强制推送的风险
3. 建议在执行前创建备份分支
4. 如果仓库较大，重写可能需要较长时间

## 输出示例

```
=== Git 邮箱重写 ===
搜索模式: *@oldcompany.com
新邮箱: user@newcompany.com

找到 12 个匹配的提交:
  - abc1234 old1@oldcompany.com
  - def5678 old2@oldcompany.com
  ...

确认执行替换? (y/N): y

重写历史记录中...
Rewrite 1/12 (8 seconds passed)
...
Ref 'refs/heads/master' was rewritten

清理历史记录...

验证结果:
✓ 未再发现匹配的邮箱

最近的提交:
abc1234 更新配置文件
...

=== 完成 ===
提示: 使用 'git push --force' 推送修改后的历史
```
