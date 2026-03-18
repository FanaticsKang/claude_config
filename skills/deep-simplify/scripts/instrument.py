#!/usr/bin/env python3
"""
代码插桩脚本：在Python代码中插入日志标记以追踪执行路径
"""
import ast
import sys
from typing import Set, Tuple


class CodeInstrumentor(ast.NodeTransformer):
    """AST转换器：在关键代码位置插入日志语句"""

    def __init__(self, file_name: str):
        self.file_name = file_name
        self.current_function = None
        self.instrumented_count = 0

    def _create_log_call(self, line: int, tag_type: str) -> ast.Expr:
        """创建日志打印语句"""
        func_name = self.current_function or "module"
        log_msg = f"[DEEP_SIMPLIFY] {self.file_name}:{line}:{func_name}:{tag_type}"
        return ast.Expr(
            value=ast.Call(
                func=ast.Name(id='print', ctx=ast.Load()),
                args=[ast.Constant(value=log_msg)],
                keywords=[]
            )
        )

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        """在函数入口插入日志"""
        old_func = self.current_function
        self.current_function = node.name

        # 在函数体第一行插入日志
        log_stmt = self._create_log_call(node.lineno, "func_entry")
        node.body.insert(0, log_stmt)
        self.instrumented_count += 1

        # 访问函数体内部
        self.generic_visit(node)

        self.current_function = old_func
        return node

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> ast.AsyncFunctionDef:
        """在异步函数入口插入日志"""
        old_func = self.current_function
        self.current_function = node.name

        log_stmt = self._create_log_call(node.lineno, "func_entry")
        node.body.insert(0, log_stmt)
        self.instrumented_count += 1

        self.generic_visit(node)
        self.current_function = old_func
        return node

    def visit_For(self, node: ast.For) -> ast.For:
        """在循环体入口插入日志"""
        self.generic_visit(node)
        log_stmt = self._create_log_call(node.lineno, "loop_entry")
        node.body.insert(0, log_stmt)
        self.instrumented_count += 1
        return node

    def visit_While(self, node: ast.While) -> ast.While:
        """在while循环体入口插入日志"""
        self.generic_visit(node)
        log_stmt = self._create_log_call(node.lineno, "loop_entry")
        node.body.insert(0, log_stmt)
        self.instrumented_count += 1
        return node

    def visit_If(self, node: ast.If) -> ast.If:
        """在if-else分支中插入日志"""
        # 确定分支类型
        parent = getattr(node, '_parent', None)
        is_elif = False
        if parent and isinstance(parent, ast.If):
            is_elif = True

        # 在if体前插入日志
        tag = "elif_branch" if is_elif else "if_branch"
        log_stmt = self._create_log_call(node.lineno, tag)
        node.body.insert(0, log_stmt)
        self.instrumented_count += 1

        # 处理else分支
        if node.orelse:
            if len(node.orelse) == 1 and isinstance(node.orelse[0], ast.If):
                # elif情况，递归处理
                node.orelse[0]._parent = node
                self.visit(node.orelse[0])
            else:
                # 真正的else分支
                else_log = self._create_log_call(node.orelse[0].lineno if hasattr(node.orelse[0], 'lineno') else node.lineno, "else_branch")
                node.orelse.insert(0, else_log)
                self.instrumented_count += 1
                # 访问else内部
                for stmt in node.orelse[1:]:
                    self.visit(stmt)

        # 访问if体内部（跳过已插入的日志）
        for stmt in node.body[1:]:
            self.visit(stmt)

        return node

    def visit_Try(self, node: ast.Try) -> ast.Try:
        """在try-except-finally中插入日志"""
        # try块
        log_stmt = self._create_log_call(node.lineno, "try_block")
        node.body.insert(0, log_stmt)
        self.instrumented_count += 1

        # except块
        for handler in node.handlers:
            handler_log = self._create_log_call(handler.lineno, "except_block")
            handler.body.insert(0, handler_log)
            self.instrumented_count += 1

        # finally块
        if node.finalbody:
            finally_log = self._create_log_call(node.finalbody[0].lineno if hasattr(node.finalbody[0], 'lineno') else node.lineno, "finally_block")
            node.finalbody.insert(0, finally_log)
            self.instrumented_count += 1

        self.generic_visit(node)
        return node


def instrument_file(file_path: str, output_path: str = None) -> Tuple[str, int]:
    """
    对Python文件进行插桩

    Args:
        file_path: 源文件路径
        output_path: 输出文件路径（默认覆盖原文件，原文件备份为.bak）

    Returns:
        (备份文件路径, 插桩点数量)
    """
    import shutil

    # 读取源文件
    with open(file_path, 'r', encoding='utf-8') as f:
        source = f.read()

    # 解析AST
    tree = ast.parse(source)

    # 创建备份
    backup_path = file_path + '.bak'
    shutil.copy2(file_path, backup_path)

    # 插桩
    file_name = file_path.split('/')[-1]
    instrumentor = CodeInstrumentor(file_name)
    instrumented_tree = instrumentor.visit(tree)

    # 修复AST位置信息
    ast.fix_missing_locations(instrumented_tree)

    # 生成代码
    import astor
    new_source = astor.to_source(instrumented_tree)

    # 写入文件
    target_path = output_path or file_path
    with open(target_path, 'w', encoding='utf-8') as f:
        f.write(new_source)

    return backup_path, instrumentor.instrumented_count


def extract_instrumentation_points(file_path: str) -> Set[Tuple[int, str, str]]:
    """
    提取文件中的所有插桩点信息

    Returns:
        Set of (line_number, function_name, tag_type)
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        source = f.read()

    tree = ast.parse(source)
    file_name = file_path.split('/')[-1]

    class PointExtractor(ast.NodeVisitor):
        def __init__(self):
            self.points = set()
            self.current_function = None

        def visit_FunctionDef(self, node):
            old_func = self.current_function
            self.current_function = node.name
            self.points.add((node.lineno, node.name, "func_entry"))
            self.generic_visit(node)
            self.current_function = old_func

        def visit_AsyncFunctionDef(self, node):
            old_func = self.current_function
            self.current_function = node.name
            self.points.add((node.lineno, node.name, "func_entry"))
            self.generic_visit(node)
            self.current_function = old_func

        def visit_For(self, node):
            func = self.current_function or "module"
            self.points.add((node.lineno, func, "loop_entry"))
            self.generic_visit(node)

        def visit_While(self, node):
            func = self.current_function or "module"
            self.points.add((node.lineno, func, "loop_entry"))
            self.generic_visit(node)

        def visit_If(self, node):
            func = self.current_function or "module"
            self.points.add((node.lineno, func, "if_branch"))
            # 简化处理，不深入elif/else
            self.generic_visit(node)

    extractor = PointExtractor()
    extractor.visit(tree)
    return extractor.points


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: instrument.py <file_path>")
        sys.exit(1)

    file_path = sys.argv[1]
    backup, count = instrument_file(file_path)
    print(f"Instrumented {count} points in {file_path}")
    print(f"Backup saved to: {backup}")
