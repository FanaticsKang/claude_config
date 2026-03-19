#!/usr/bin/env python3
"""
Python 命名规范检查和修复工具
检查文件名是否与主要类名保持一致，并处理所有相关引用
"""

import os
import re
import ast
import argparse
from pathlib import Path
from typing import Optional, List, Dict, Tuple


def to_snake_case(name: str) -> str:
    """将大驼峰类名转换为 snake_case 文件名"""
    # 处理连续大写字母（如 HTTPRequest → http_request）
    s1 = re.sub('([A-Z]+)([A-Z][a-z])', r'\1_\2', name)
    # 处理小写字母后接大写字母（如 HttpRequest → http_request）
    s2 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1)
    return s2.lower()


def extract_class_names(file_path: str) -> List[Tuple[str, bool]]:
    """
    从 Python 文件中提取类名
    返回: [(类名, 是否有@register_node装饰器), ...]
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        tree = ast.parse(content)
        classes = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # 检查是否有 @register_node 装饰器
                has_register_node = False
                for decorator in node.decorator_list:
                    if isinstance(decorator, ast.Call):
                        if isinstance(decorator.func, ast.Name) and decorator.func.id == 'register_node':
                            has_register_node = True
                            break
                    elif isinstance(decorator, ast.Name) and decorator.id == 'register_node':
                        has_register_node = True
                        break

                classes.append((node.name, has_register_node))

        return classes
    except Exception as e:
        print(f"[Error] 解析文件失败: {e}")
        return []


def get_main_class(classes: List[Tuple[str, bool]]) -> Optional[str]:
    """
    从类列表中确定主类
    优先选择有 @register_node 装饰器的类
    """
    if not classes:
        return None

    # 优先选择有 register_node 装饰器的类
    for name, has_decorator in classes:
        if has_decorator:
            return name

    # 如果没有，返回第一个类
    return classes[0][0]


def check_naming_convention(file_path: str) -> Dict:
    """
    检查 Python 文件的命名规范

    Returns:
        {
            "valid": bool,
            "current_filename": str,
            "expected_filename": str,
            "class_name": str,
            "message": str
        }
    """
    path = Path(file_path)

    if not path.exists():
        return {
            "valid": False,
            "current_filename": path.name,
            "expected_filename": "",
            "class_name": "",
            "message": f"文件不存在: {file_path}"
        }

    if not path.suffix == '.py':
        return {
            "valid": False,
            "current_filename": path.name,
            "expected_filename": "",
            "class_name": "",
            "message": f"不是 Python 文件: {file_path}"
        }

    # 提取类名
    classes = extract_class_names(file_path)

    if not classes:
        return {
            "valid": False,
            "current_filename": path.name,
            "expected_filename": "",
            "class_name": "",
            "message": f"文件中没有找到类定义: {file_path}"
        }

    # 确定主类
    main_class = get_main_class(classes)

    if not main_class:
        return {
            "valid": False,
            "current_filename": path.name,
            "expected_filename": "",
            "class_name": "",
            "message": f"无法确定主类: {file_path}"
        }

    # 计算期望的文件名
    expected_filename = to_snake_case(main_class) + '.py'
    current_filename = path.name

    # 检查是否匹配
    valid = current_filename == expected_filename

    if valid:
        message = f"命名规范检查通过 ✅\n- 当前文件: {current_filename}\n- 主类名: {main_class}\n- 命名规范符合要求"
    else:
        message = f"发现命名不规范 ❌\n- 当前文件: {current_filename}\n- 主类名: {main_class}\n- 期望文件: {expected_filename}"

    return {
        "valid": valid,
        "current_filename": current_filename,
        "expected_filename": expected_filename,
        "class_name": main_class,
        "message": message
    }


def find_references(project_dir: str, old_module_name: str) -> List[Dict]:
    """
    在项目中查找对指定模块的所有引用

    Args:
        project_dir: 项目根目录
        old_module_name: 原模块名（不含.py后缀）

    Returns:
        引用列表，每个包含文件路径、行号、内容等信息
    """
    references = []
    project_path = Path(project_dir)

    # 搜索 Python 文件
    for py_file in project_path.rglob("*.py"):
        # 跳过 __pycache__ 和隐藏目录
        if "__pycache__" in str(py_file) or "/." in str(py_file):
            continue

        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            for line_num, line in enumerate(lines, 1):
                # 检查导入语句
                patterns = [
                    rf"from\s+\S*\.{old_module_name}\s+import",  # from x.old import
                    rf"import\s+\S*\.{old_module_name}",         # import x.old
                    rf"from\s+{old_module_name}\s+import",      # from old import
                    rf"import\s+{old_module_name}",             # import old
                ]

                for pattern in patterns:
                    if re.search(pattern, line):
                        references.append({
                            "file": str(py_file),
                            "line": line_num,
                            "content": line.strip(),
                            "type": "python_import"
                        })
                        break
        except Exception:
            continue

    # 搜索配置文件
    config_patterns = ['*.yaml', '*.yml', '*.json', '*.toml']
    for pattern in config_patterns:
        for config_file in project_path.rglob(pattern):
            if "__pycache__" in str(config_file) or "/." in str(config_file):
                continue

            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()

                for line_num, line in enumerate(lines, 1):
                    if old_module_name in line:
                        references.append({
                            "file": str(config_file),
                            "line": line_num,
                            "content": line.strip(),
                            "type": "config"
                        })
            except Exception:
                continue

    return references


def update_references(references: List[Dict], old_module: str, new_module: str, dry_run: bool = False) -> Dict:
    """
    更新所有引用

    Returns:
        {
            "updated": int,
            "failed": int,
            "details": List[str]
        }
    """
    updated = 0
    failed = 0
    details = []

    # 按文件分组
    files_to_update = {}
    for ref in references:
        file_path = ref["file"]
        if file_path not in files_to_update:
            files_to_update[file_path] = []
        files_to_update[file_path].append(ref)

    for file_path, refs in files_to_update.items():
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')

            modified = False
            for ref in refs:
                line_idx = ref["line"] - 1
                if 0 <= line_idx < len(lines):
                    old_line = lines[line_idx]
                    # 替换模块名（作为完整单词或路径的一部分）
                    new_line = old_line.replace(old_module, new_module)
                    if new_line != old_line:
                        lines[line_idx] = new_line
                        modified = True
                        details.append(f"  {file_path}:{ref['line']} | {old_line.strip()} → {new_line.strip()}")

            if modified and not dry_run:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(lines))

            if modified:
                updated += len([r for r in refs if old_module in r["content"]])

        except Exception as e:
            failed += len(refs)
            details.append(f"  [Error] {file_path}: {e}")

    return {
        "updated": updated,
        "failed": failed,
        "details": details
    }


def fix_naming(file_path: str, project_dir: Optional[str] = None, dry_run: bool = False) -> Dict:
    """
    修复文件名与类名不匹配的问题，并更新所有引用

    Args:
        file_path: Python 文件路径
        project_dir: 项目根目录（用于搜索引用），默认为文件所在目录的上级
        dry_run: 如果为 True，只返回建议不实际修改

    Returns:
        {
            "success": bool,
            "old_path": str,
            "new_path": str,
            "references_found": int,
            "references_updated": int,
            "message": str
        }
    """
    result = check_naming_convention(file_path)

    if result["valid"]:
        return {
            "success": True,
            "old_path": file_path,
            "new_path": file_path,
            "references_found": 0,
            "references_updated": 0,
            "message": "命名规范正确，无需修复"
        }

    if not result["expected_filename"]:
        return {
            "success": False,
            "old_path": file_path,
            "new_path": "",
            "references_found": 0,
            "references_updated": 0,
            "message": f"无法修复: {result['message']}"
        }

    path = Path(file_path)
    new_path = path.parent / result["expected_filename"]
    old_module = path.stem
    new_module = Path(result["expected_filename"]).stem

    # 确定项目目录
    if project_dir is None:
        project_dir = str(path.parent.parent)

    output_lines = [result["message"]]
    output_lines.append(f"\n开始修复流程...")

    # 步骤1: 复制文件
    output_lines.append(f"\n[1/5] 复制文件...")
    if new_path.exists():
        return {
            "success": False,
            "old_path": file_path,
            "new_path": str(new_path),
            "references_found": 0,
            "references_updated": 0,
            "message": f"修复失败: 目标文件已存在 {new_path}"
        }

    if not dry_run:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            with open(new_path, 'w', encoding='utf-8') as f:
                f.write(content)
            output_lines.append(f"  ✅ 已创建新文件: {new_path}")
        except Exception as e:
            return {
                "success": False,
                "old_path": file_path,
                "new_path": str(new_path),
                "references_found": 0,
                "references_updated": 0,
                "message": f"创建新文件失败: {e}"
            }
    else:
        output_lines.append(f"  [Dry Run] 将创建新文件: {new_path}")

    # 步骤2: 查找引用
    output_lines.append(f"\n[2/5] 查找项目中的引用...")
    references = find_references(project_dir, old_module)
    output_lines.append(f"  找到 {len(references)} 处引用")

    # 步骤3: 更新引用
    output_lines.append(f"\n[3/5] 更新引用...")
    if references:
        update_result = update_references(references, old_module, new_module, dry_run)
        output_lines.append(f"  更新 {update_result['updated']} 处引用")
        if update_result['failed'] > 0:
            output_lines.append(f"  失败 {update_result['failed']} 处")
        if update_result['details']:
            output_lines.append("  详情:")
            for detail in update_result['details'][:10]:  # 最多显示10条
                output_lines.append(detail)
            if len(update_result['details']) > 10:
                output_lines.append(f"  ... 还有 {len(update_result['details']) - 10} 处")
    else:
        output_lines.append("  无需更新引用")

    # 步骤4: 验证
    output_lines.append(f"\n[4/5] 验证...")
    output_lines.append(f"  {'[Dry Run] ' if dry_run else ''}请运行测试验证修改是否正确")

    # 步骤5: 删除原文件
    output_lines.append(f"\n[5/5] 清理原文件...")
    if not dry_run:
        # 暂不删除原文件，由用户确认后手动删除
        output_lines.append(f"  ⏸️ 原文件保留: {file_path}")
        output_lines.append(f"     验证无误后请手动删除，或使用: rm {file_path}")
    else:
        output_lines.append(f"  [Dry Run] 将在验证后删除原文件: {file_path}")

    output_lines.append(f"\n{'='*50}")
    output_lines.append(f"修复总结:")
    output_lines.append(f"  - 新文件: {new_path}")
    output_lines.append(f"  - 更新引用: {len(references)} 处")
    output_lines.append(f"  - 原文件: {file_path} (请手动删除)")

    return {
        "success": True,
        "old_path": file_path,
        "new_path": str(new_path),
        "references_found": len(references),
        "references_updated": len(references),
        "message": '\n'.join(output_lines)
    }


def main():
    parser = argparse.ArgumentParser(description='Python 命名规范检查工具')
    parser.add_argument('file', help='Python 文件路径')
    parser.add_argument('--project-dir', help='项目根目录（用于搜索引用）')
    parser.add_argument('--fix', action='store_true', help='自动修复命名不规范并更新引用')
    parser.add_argument('--dry-run', action='store_true', help='模拟运行，不实际修改')

    args = parser.parse_args()

    if args.fix or args.dry_run:
        result = fix_naming(args.file, project_dir=args.project_dir, dry_run=args.dry_run)
    else:
        result = check_naming_convention(args.file)

    print(result["message"])

    # 返回退出码
    if not result.get("success", result.get("valid", False)):
        exit(1)


if __name__ == '__main__':
    main()
