---
name: python-naming-convention
description: |
  检查并修复 Python 文件的命名规范，确保文件名与主要类名保持一致。

  **命令格式：**
  `/python-naming-convention <file_path> [--fix]`

  - 无 `--fix`：仅检查，输出命名规范报告
  - 有 `--fix`：执行完整修复流程（复制文件→更新引用→验证）

  **触发场景：**
  - 用户要求检查代码命名规范
  - 用户提到文件名和类名不一致
  - 需要验证 Python 文件是否符合项目的命名约定
  - 需要自动修复命名不一致的问题

  **检查规则：**
  - 类名使用大驼峰（PascalCase），如：EgoMsgMapNode
  - 文件名使用小写+下划线（snake_case），如：ego_msg_map_node.py
  - 文件名应与主类名对应：EgoMsgMapNode → ego_msg_map_node.py
---

# Python 命名规范检查与修复

## 工作流程

### 1. 检查文件命名

读取指定的 Python 文件，分析其中的类定义：

1. **提取类名**：查找所有使用 `@register_node` 装饰器或继承自特定基类的类
2. **确定主类**：如果只有一个类，将其视为主类；如果有多个，优先选择使用 `@register_node` 装饰的类
3. **计算期望文件名**：将类名转换为 snake_case 格式
   - EgoMsgMapNode → ego_msg_map_node
   - HttpRequestHandler → http_request_handler
4. **对比检查**：比较实际文件名与期望文件名

如果文件名正确，结束流程。

### 2. 复制并纠正文件名

如果文件名与类名不匹配：

1. **生成正确的文件名**：将类名转换为 snake_case 并添加 `.py` 后缀
2. **复制文件内容**：将原文件内容复制到新文件（此时原文件保留，便于后续对比）
3. **验证新文件**：确保新文件可以正常解析

### 3. 检查引用

在整个项目中搜索对原文件名的引用：

1. **搜索导入语句**：`from xxx import`、`import xxx`
2. **搜索配置文件**：`.yaml`、`.json`、`.toml` 等配置文件中的模块引用
3. **搜索字符串引用**：动态导入、日志输出等

### 4. 修改引用

将所有对原文件名的引用修改为新的文件名：

1. **更新 Python 导入**：修改 `from module.old_name import Xxx` → `from module.new_name import Xxx`
2. **更新配置文件**：修改配置文件中的模块路径
3. **更新其他引用**：字符串、文档等

### 5. 验证并清理

1. **运行验证**：执行测试或运行程序，确保修改后的代码正常工作
2. **删除原文件**：验证通过后，删除原文件
3. **输出报告**：告知用户完整的修改结果

## 命名转换规则

### 类名 → 文件名转换

```python
def to_snake_case(name: str) -> str:
    """将大驼峰类名转换为 snake_case 文件名"""
    import re
    # 处理连续大写字母（如 HTTPRequest → http_request）
    s1 = re.sub('([A-Z]+)([A-Z][a-z])', r'\1_\2', name)
    # 处理小写字母后接大写字母（如 HttpRequest → http_request）
    s2 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1)
    return s2.lower()
```

**转换示例：**
| 类名 | 文件名 |
|------|--------|
| EgoMsgMapNode | ego_msg_map_node.py |
| HttpRequestHandler | http_request_handler.py |
| UserManager | user_manager.py |
| APIGateway | api_gateway.py |
| XMLParser | xml_parser.py |

## 使用方式

### 命令格式

```
/python-naming-convention <file_path> [--fix]
```

**参数说明：**
- `file_path`: 要检查的 Python 文件路径（必填）
- `--fix`: 可选修饰符，添加此参数会执行修复操作；不添加则仅检查

### 示例

```bash
# 仅检查命名规范（不修改任何文件）
/python-naming-convention node/msg_map_node.py

# 检查并修复（复制文件 + 更新引用）
/python-naming-convention node/msg_map_node.py --fix

# 指定项目目录（用于搜索引用）
/python-naming-convention node/msg_map_node.py --fix --project-dir /path/to/project
```

### 底层脚本调用

```bash
# 仅检查
python ~/.claude/skills/python-naming-convention/scripts/check_naming.py <file_path>

# 检查并修复
python ~/.claude/skills/python-naming-convention/scripts/check_naming.py <file_path> --fix

# 模拟修复（查看建议但不实际执行）
python ~/.claude/skills/python-naming-convention/scripts/check_naming.py <file_path> --dry-run
```

### 完整工作流程示例

```bash
# 1. 检查命名规范
python ~/.claude/skills/python-naming-convention/scripts/check_naming.py node/msg_map_node.py
# 输出：发现命名不规范，当前文件 msg_map_node.py，期望文件 ego_msg_map_node.py

# 2. 模拟修复（查看会影响哪些文件）
python ~/.claude/skills/python-naming-convention/scripts/check_naming.py node/msg_map_node.py --dry-run

# 3. 实际修复
python ~/.claude/skills/python-naming-convention/scripts/check_naming.py node/msg_map_node.py --fix
# 输出：
#   [1/5] 复制文件 → 创建 ego_msg_map_node.py
#   [2/5] 查找引用 → 找到 X 处引用
#   [3/5] 更新引用 → 修改相关导入语句
#   [4/5] 验证 → 提示运行测试
#   [5/5] 清理 → 原文件保留，需手动删除

# 4. 运行测试验证
python main.py

# 5. 验证通过后删除原文件
rm node/msg_map_node.py
```

### 在 Python 代码中使用

```python
from pathlib import Path
import sys

# 添加 skill 脚本路径
sys.path.insert(0, str(Path.home() / '.claude/skills/python-naming-convention/scripts'))
from check_naming import check_naming_convention, fix_naming

# 检查命名规范
result = check_naming_convention('node/msg_map_node.py')
print(result['message'])

# 自动修复（检查类名、复制文件、更新引用）
if not result['valid']:
    fix_result = fix_naming(
        'node/msg_map_node.py',
        project_dir='.',  # 项目根目录
        dry_run=False
    )
    print(fix_result['message'])
```

## 输出格式

检查完成后，向用户报告：

**情况1：命名正确**
```
文件名检查通过 ✅
- 当前文件: ego_msg_map_node.py
- 主类名: EgoMsgMapNode
- 命名规范符合要求
```

**情况2：命名不匹配**
```
发现命名不规范 ❌
- 当前文件: msg_map_node.py
- 主类名: EgoMsgMapNode
- 期望文件: ego_msg_map_node.py

正在修复...
✅ 已重命名: msg_map_node.py → ego_msg_map_node.py
```

## 边界情况处理

1. **文件不包含类**：报告错误，无法检查
2. **文件包含多个类**：优先选择有 `@register_node` 装饰器的类
3. **文件已在 git 跟踪中**：使用 `git mv` 进行重命名
4. **目标文件已存在**：提示用户手动处理冲突
