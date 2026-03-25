#!/usr/bin/env python3
"""
代码简化脚本：根据分析结果移除死代码
"""
import ast
import sys
from typing import List, Set, Dict


class DeadCodeRemover(ast.NodeTransformer):
    """AST转换器：移除死代码"""

    def __init__(self, dead_functions: Set[str], dead_branches: Set[int]):
        self.dead_functions = dead_functions
        self.dead_branches = dead_branches
        self.removed_count = 0
        self.removed_items = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST:
        """移除未使用的函数"""
        if node.name in self.dead_functions:
            self.removed_count += 1
            self.removed_items.append({
                'type': 'function',
                'name': node.name,
                'line': node.lineno
            })
            return None  # 移除整个函数
        return self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> ast.AST:
        """移除未使用的异步函数"""
        if node.name in self.dead_functions:
            self.removed_count += 1
            self.removed_items.append({
                'type': 'async_function',
                'name': node.name,
                'line': node.lineno
            })
            return None
        return self.generic_visit(node)

    def visit_If(self, node: ast.If) -> ast.AST:
        """简化未使用的分支"""
        self.generic_visit(node)

        # 检查if分支是否死亡
        if node.lineno in self.dead_branches:
            # 如果if死亡但else存活，用else替换整个if
            if node.orelse:
                # 检查else是否也是死代码
                else_dead = True
                for stmt in node.orelse:
                    if hasattr(stmt, 'lineno') and stmt.lineno not in self.dead_branches:
                        else_dead = False
                        break

                if not else_dead:
                    self.removed_count += 1
                    self.removed_items.append({
                        'type': 'if_branch',
                        'line': node.lineno
                    })
                    # 返回else的内容（展平）
                    return node.orelse
                else:
                    # 整个if-else都死亡
                    self.removed_count += 1
                    self.removed_items.append({
                        'type': 'if_else_block',
                        'line': node.lineno
                    })
                    return None
            else:
                # 没有else，整个if死亡
                self.removed_count += 1
                self.removed_items.append({
                    'type': 'if_block',
                    'line': node.lineno
                })
                return None

        return node


def remove_dead_code(
    file_path: str,
    dead_functions: List[Dict],
    dead_branches: List[Dict],
    output_path: str = None
) -> Dict:
    """
    从文件中移除死代码

    Args:
        file_path: 源文件路径
        dead_functions: 死函数列表 [{'line': int, 'function': str}, ...]
        dead_branches: 死分支列表 [{'line': int, 'type': str}, ...]
        output_path: 输出路径（默认覆盖原文件）

    Returns:
        {'removed_count': int, 'removed_items': List[Dict]}
    """
    # 读取源文件
    with open(file_path, 'r', encoding='utf-8') as f:
        source = f.read()

    # 解析AST
    tree = ast.parse(source)

    # 准备移除集合
    func_names = {f['function'] for f in dead_functions}
    branch_lines = {b['line'] for b in dead_branches}

    # 转换
    remover = DeadCodeRemover(func_names, branch_lines)
    new_tree = remover.visit(tree)

    # 如果没有移除任何东西，直接返回
    if remover.removed_count == 0:
        return {'removed_count': 0, 'removed_items': []}

    # 修复AST
    ast.fix_missing_locations(new_tree)

    # 生成代码
    try:
        import astor
        new_source = astor.to_source(new_tree)
    except ImportError:
        # 如果没有astor，使用ast.unparse (Python 3.9+)
        new_source = ast.unparse(new_tree)

    # 写入文件
    target = output_path or file_path
    with open(target, 'w', encoding='utf-8') as f:
        f.write(new_source)

    return {
        'removed_count': remover.removed_count,
        'removed_items': remover.removed_items
    }


def restore_from_backup(file_path: str, backup_path: str):
    """从备份恢复文件"""
    import shutil
    shutil.copy2(backup_path, file_path)


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: simplify.py <file_path> <analysis_json> <output_path>")
        sys.exit(1)

    file_path = sys.argv[1]
    analysis_path = sys.argv[2]
    output_path = sys.argv[3]

    # 读取分析结果
    import json
    with open(analysis_path, 'r') as f:
        analysis = json.load(f)

    # 简化代码
    result = remove_dead_code(
        file_path,
        analysis.get('unused_functions', []),
        analysis.get('unused_branches', []),
        output_path
    )

    print(f"Removed {result['removed_count']} dead code items")
    for item in result['removed_items']:
        print(f"  - {item['type']} at line {item.get('line', 'N/A')}: {item.get('name', '')}")
