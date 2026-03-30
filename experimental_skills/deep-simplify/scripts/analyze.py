#!/usr/bin/env python3
"""
日志分析脚本：分析运行时日志，识别死代码
"""
import re
import sys
from collections import defaultdict
from typing import Dict, List, Set, Tuple


def parse_logs(log_output: str) -> Dict[str, Set[Tuple[int, str, str]]]:
    """
    解析日志输出，提取执行的代码点

    Returns:
        Dict[file_name, Set of (line_number, function_name, tag_type)]
    """
    executed = defaultdict(set)

    # 匹配格式: [DEEP_SIMPLIFY] file_name:line:func:tag_type
    pattern = r'\[DEEP_SIMPLIFY\] ([^:]+):(\d+):([^:]+):(\w+)'

    for match in re.finditer(pattern, log_output):
        file_name = match.group(1)
        line = int(match.group(2))
        func = match.group(3)
        tag = match.group(4)
        executed[file_name].add((line, func, tag))

    return executed


def analyze_coverage(
    instrumented_points: Set[Tuple[int, str, str]],
    executed_points: Set[Tuple[int, str, str]],
    source_lines: List[str]
) -> Dict:
    """
    分析代码覆盖情况

    Returns:
        {
            'total_points': int,
            'executed_points': int,
            'coverage_rate': float,
            'dead_code_regions': List[Dict],
            'unused_functions': List[str],
            'unused_branches': List[Dict]
        }
    """
    # 按类型分组
    by_type = defaultdict(lambda: {'instrumented': set(), 'executed': set()})

    for point in instrumented_points:
        line, func, tag = point
        by_type[tag]['instrumented'].add((line, func))

    for point in executed_points:
        line, func, tag = point
        by_type[tag]['executed'].add((line, func))

    # 分析死代码区域
    dead_regions = []
    unused_functions = []
    unused_branches = []

    for tag, data in by_type.items():
        instrumented = data['instrumented']
        executed = data['executed']
        dead = instrumented - executed

        if tag == 'func_entry':
            for line, func in dead:
                unused_functions.append({
                    'line': line,
                    'function': func,
                    'reason': 'Function never called during execution'
                })
        elif tag in ('if_branch', 'elif_branch', 'else_branch'):
            for line, func in dead:
                unused_branches.append({
                    'line': line,
                    'function': func,
                    'type': tag,
                    'reason': f'{tag} never executed'
                })

        for line, func in dead:
            dead_regions.append({
                'line': line,
                'function': func,
                'type': tag,
                'code': source_lines[line-1].strip() if line <= len(source_lines) else 'N/A'
            })

    total = len(instrumented_points)
    executed_count = len(executed_points)
    coverage_rate = executed_count / total if total > 0 else 0

    return {
        'total_points': total,
        'executed_points': executed_count,
        'coverage_rate': coverage_rate,
        'dead_code_regions': dead_regions,
        'unused_functions': unused_functions,
        'unused_branches': unused_branches,
        'by_type': {
            tag: {
                'total': len(data['instrumented']),
                'executed': len(data['executed']),
                'dead': len(data['instrumented'] - data['executed'])
            }
            for tag, data in by_type.items()
        }
    }


def generate_report(analysis: Dict, file_name: str) -> str:
    """生成分析报告"""
    lines = []
    lines.append(f"\n{'='*60}")
    lines.append(f"代码覆盖率分析报告: {file_name}")
    lines.append(f"{'='*60}")
    lines.append(f"\n总体统计:")
    lines.append(f"  总插桩点: {analysis['total_points']}")
    lines.append(f"  已执行: {analysis['executed_points']}")
    lines.append(f"  覆盖率: {analysis['coverage_rate']:.1%}")

    lines.append(f"\n按类型统计:")
    for tag, stats in analysis['by_type'].items():
        lines.append(f"  {tag}: {stats['executed']}/{stats['total']} (死代码: {stats['dead']})")

    if analysis['unused_functions']:
        lines.append(f"\n未使用的函数 ({len(analysis['unused_functions'])}个):")
        for func in analysis['unused_functions']:
            lines.append(f"  第{func['line']}行: {func['function']}")

    if analysis['unused_branches']:
        lines.append(f"\n未执行的分支 ({len(analysis['unused_branches'])}个):")
        for branch in analysis['unused_branches']:
            lines.append(f"  第{branch['line']}行 ({branch['function']}): {branch['type']}")

    if analysis['dead_code_regions']:
        lines.append(f"\n死代码区域 ({len(analysis['dead_code_regions'])}个):")
        for region in analysis['dead_code_regions'][:20]:  # 只显示前20个
            lines.append(f"  第{region['line']}行 [{region['type']}]: {region['code'][:60]}...")

    lines.append(f"\n{'='*60}\n")

    return '\n'.join(lines)


def load_instrumentation_log(log_file: str) -> Set[Tuple[int, str, str]]:
    """从文件加载插桩点记录"""
    points = set()
    with open(log_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line:
                parts = line.split(':')
                if len(parts) == 3:
                    points.add((int(parts[0]), parts[1], parts[2]))
    return points


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: analyze.py <log_file> <instrumented_log> [source_file]")
        sys.exit(1)

    log_file = sys.argv[1]
    inst_log_file = sys.argv[2]
    source_file = sys.argv[3] if len(sys.argv) > 3 else None

    # 读取日志
    with open(log_file, 'r') as f:
        log_output = f.read()

    # 解析执行日志
    executed = parse_logs(log_output)

    # 加载插桩点
    instrumented = load_instrumentation_log(inst_log_file)

    # 读取源代码（用于显示死代码）
    source_lines = []
    if source_file:
        with open(source_file, 'r') as f:
            source_lines = f.readlines()

    # 分析（假设只有一个文件）
    for file_name, exec_points in executed.items():
        analysis = analyze_coverage(instrumented, exec_points, source_lines)
        print(generate_report(analysis, file_name))
