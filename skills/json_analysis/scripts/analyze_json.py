#!/usr/bin/env python3
"""
JSON 文件分析工具
分析大型 JSON 文件结构并生成格式说明文档（支持 Markdown 和 CSV 输出）
"""

import json
import csv
import os
import sys
from collections import defaultdict
from pathlib import Path


def get_file_size_human(size_bytes):
    """将字节大小转换为人类可读格式"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.2f} TB"


def infer_key_type(keys):
    """推断键的类型"""
    if not keys:
        return 'unknown'
    sample = str(keys[0])

    # 纯数字
    if all(str(k).isdigit() for k in keys[:10]):
        if len(sample) >= 16:
            return 'timestamp_ns'
        elif len(sample) >= 13:
            return 'timestamp_ms'
        elif len(sample) >= 10:
            return 'timestamp'
        else:
            return 'numeric_id'

    # UUID 格式
    if '-' in sample and len(sample) == 36:
        return 'uuid'

    # 哈希（16进制）
    if all(c in '0123456789abcdefABCDEF' for c in sample) and len(sample) >= 16:
        return 'hash'

    return 'identifier'


def collect_fields(obj, path, field_occurrences, max_samples=2):
    """递归收集字段信息"""
    if isinstance(obj, dict):
        for key, value in obj.items():
            full_path = f"{path}.{key}" if path else key
            field_occurrences[full_path]['count'] += 1
            collect_fields(value, full_path, field_occurrences, max_samples)
    elif isinstance(obj, list):
        if obj:
            # 标记为数组
            array_path = path + '[]'
            for item in obj[:3]:  # 采样前3个元素
                collect_fields(item, array_path, field_occurrences, max_samples)
    else:
        field_occurrences[path]['types'].add(type(obj).__name__)
        if len(field_occurrences[path]['samples']) < max_samples:
            sample = str(obj)[:60] + '...' if len(str(obj)) > 60 else str(obj)
            if sample not in field_occurrences[path]['samples']:
                field_occurrences[path]['samples'].append(sample)


def analyze_dict_structure(data, sample_size=20):
    """分析字典结构，提取统一 Schema"""
    keys = list(data.keys())
    sample = keys[:min(sample_size, len(keys))]

    # 推断键类型
    key_type = infer_key_type(keys[:100])

    # 收集所有字段的出现情况（字段并集）
    field_occurrences = defaultdict(lambda: {
        'types': set(),
        'samples': [],
        'count': 0
    })

    # 从所有采样实例中收集字段
    for key in sample:
        collect_fields(data[key], '', field_occurrences)

    # 计算字段属性
    properties = {}
    type_mapping = {'str': 'string', 'int': 'integer', 'float': 'number',
                   'bool': 'boolean', 'list': 'array', 'dict': 'object'}

    for path, info in field_occurrences.items():
        presence_rate = info['count'] / len(sample)
        main_type = list(info['types'])[0] if info['types'] else 'object'

        properties[path] = {
            'type': type_mapping.get(main_type, main_type),
            'samples': info['samples'],
            'presence_rate': presence_rate,
            'optional': presence_rate < 0.95,
            'count': info['count']
        }

    return {
        'properties': properties,
        'is_homogeneous': True,
        'key_type': key_type,
        'total_count': len(keys),
        'sample_count': len(sample),
        'key_examples': keys[:5]
    }


def analyze_array_structure(data, sample_size=20):
    """分析数组结构"""
    sample = data[:min(sample_size, len(data))]

    field_occurrences = defaultdict(lambda: {
        'types': set(),
        'samples': [],
        'count': 0
    })

    for item in sample:
        collect_fields(item, '', field_occurrences)

    properties = {}
    type_mapping = {'str': 'string', 'int': 'integer', 'float': 'number',
                   'bool': 'boolean', 'list': 'array', 'dict': 'object'}

    for path, info in field_occurrences.items():
        presence_rate = info['count'] / len(sample)
        main_type = list(info['types'])[0] if info['types'] else 'object'

        properties[path] = {
            'type': type_mapping.get(main_type, main_type),
            'samples': info['samples'],
            'presence_rate': presence_rate,
            'optional': presence_rate < 0.95,
            'count': info['count']
        }

    return {
        'properties': properties,
        'is_homogeneous': False,
        'total_count': len(data),
        'sample_count': len(sample)
    }


def analyze_json_file(file_path, sample_size=20):
    """
    分析 JSON 文件，提取统一 Schema

    Args:
        file_path: JSON 文件路径
        sample_size: 采样大小，用于大文件

    Returns:
        分析结果字典
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 判断顶层结构
    if isinstance(data, list):
        return analyze_array_structure(data, sample_size)
    elif isinstance(data, dict):
        return analyze_dict_structure(data, sample_size)
    else:
        # 标量
        return {
            'properties': {'': {
                'type': type(data).__name__,
                'samples': [str(data)[:50]],
                'presence_rate': 1.0,
                'optional': False,
                'count': 1
            }},
            'is_homogeneous': False,
            'total_count': 1,
            'sample_count': 1
        }


def build_field_tree(properties):
    """将扁平的字段路径转换为树状结构"""
    root = {}
    for path, info in sorted(properties.items()):
        parts = path.split('.')
        current = root
        for i, part in enumerate(parts):
            is_array = part.endswith('[]')
            key = part.replace('[]', '')
            if key not in current:
                current[key] = {
                    '_info': {},
                    '_is_array': is_array,
                    '_children': {}
                }
            if i == len(parts) - 1:
                current[key]['_info'] = info
            else:
                current = current[key]['_children']
    return root


def render_tree(node, prefix='', is_last=True, max_depth=5, current_depth=0):
    """将树结构渲染为 Markdown 格式的文本"""
    if current_depth >= max_depth:
        return []

    lines = []
    items = list(node.items())

    for i, (key, value) in enumerate(items):
        is_last_item = (i == len(items) - 1)
        connector = '└── ' if is_last_item else '├── '

        info = value.get('_info', {})
        is_array = value.get('_is_array', False)
        node_type = info.get('type', 'object')
        optional = info.get('optional', False)

        # 节点标记
        type_marker = '[]' if is_array else ''
        optional_marker = '?' if optional else ''

        # 节点行
        node_line = f"{prefix}{connector}{key}{type_marker}{optional_marker}"
        if info and node_type != 'object':
            node_line += f" ({node_type})"
        lines.append(node_line)

        # 处理子节点
        children = value.get('_children', {})
        if children:
            child_prefix = prefix + ('    ' if is_last_item else '│   ')
            lines.extend(render_tree(children, child_prefix, is_last_item, max_depth, current_depth + 1))

    return lines


def generate_markdown_report(file_path, analysis_result, output_path=None):
    """生成 Markdown 格式的 JSON 结构说明文档"""
    file_size = os.path.getsize(file_path)
    file_size_mb = file_size / (1024 * 1024)

    properties = analysis_result['properties']
    is_homogeneous = analysis_result.get('is_homogeneous', False)
    key_type = analysis_result.get('key_type')
    total_count = analysis_result.get('total_count', 0)
    key_examples = analysis_result.get('key_examples', [])

    # 构建树结构
    tree = build_field_tree(properties)

    lines = []
    lines.append("# JSON 文件结构分析报告")
    lines.append("")
    lines.append(f"**源文件**: `{file_path}`")
    lines.append(f"**文件大小**: {file_size_mb:.2f} MB")
    lines.append(f"**总记录数**: {total_count}")
    lines.append(f"**分析字段数**: {len(properties)}")
    lines.append("")

    # 同质结构特殊说明
    if is_homogeneous:
        lines.append("## 结构特点")
        lines.append("")

        key_type_desc = {
            'timestamp_ms': '毫秒级时间戳（如 17687934610349602）',
            'timestamp_ns': '纳秒级时间戳（如 1768793461034960200）',
            'timestamp': '秒级时间戳',
            'numeric_id': '数字ID',
            'uuid': 'UUID 格式',
            'hash': '哈希值',
            'identifier': '标识符'
        }
        desc = key_type_desc.get(key_type, '标识符')

        lines.append(f"- **顶层键类型**: {desc}")
        lines.append(f"- **实例数量**: {total_count} 个")
        lines.append(f"- **字段一致性**: 基于采样的字段并集分析")

        optional_count = sum(1 for p in properties.values() if p.get('optional'))
        if optional_count > 0:
            lines.append(f"- **可选字段**: {optional_count} 个（部分实例可能缺失）")

        lines.append("")
        lines.append("### 顶层键示例")
        for key in key_examples:
            lines.append(f"- `{key}`")
        lines.append("")

    # 结构树
    lines.append("## 结构概览")
    lines.append("")

    if is_homogeneous:
        lines.append("### 统一 Schema 结构树")
        lines.append("")
        lines.append("```")
        lines.append("<key>  (实例标识符)")
        # 渲染子树，去掉顶层
        sub_tree = {}
        for k, v in tree.items():
            sub_tree.update(v.get('_children', {}))
        lines.extend(render_tree(sub_tree, prefix="│   "))
        lines.append("```")
    else:
        lines.append("```")
        lines.extend(render_tree(tree))
        lines.append("```")

    lines.append("")
    lines.append("*注：`?` 表示可选字段（出现率 < 95%），`[]` 表示数组*")
    lines.append("")

    # 字段详细说明
    lines.append("## 字段详细说明")
    lines.append("")
    lines.append("| 字段路径 | 类型 | 出现率 | 示例值 |")
    lines.append("|----------|------|--------|--------|")

    # 按路径深度和字母顺序排序
    sorted_fields = sorted(properties.items(), key=lambda x: (x[0].count('.'), x[0]))

    for path, info in sorted_fields:
        display_path = path
        if is_homogeneous and not path.startswith('<key>'):
            display_path = f"`<key>.{path}`" if path else "`<key>`"
        else:
            display_path = f"`{path}`" if path else "`root`"

        samples = ', '.join(info['samples'][:1]) if info.get('samples') else '-'
        samples = samples.replace('|', '\\|')[:30]
        presence = f"{info.get('presence_rate', 1)*100:.0f}%"

        lines.append(f"| {display_path} | {info.get('type', 'object')} | {presence} | {samples} |")

    content = '\n'.join(lines)

    # 写入文件
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"报告已生成: {output_path}")

    return content


def generate_csv_report(file_path, analysis_result, output_path=None, field_descriptions=None):
    """
    生成 CSV 格式的字段说明文档

    Args:
        file_path: JSON 文件路径
        analysis_result: 分析结果字典
        output_path: 输出路径
        field_descriptions: 字段描述字典 {字段路径: 描述}
    """
    file_size = os.path.getsize(file_path)
    file_size_mb = file_size / (1024 * 1024)

    properties = analysis_result['properties']
    is_homogeneous = analysis_result.get('is_homogeneous', False)
    total_count = analysis_result.get('total_count', 0)

    # 自动生成输出路径
    if not output_path:
        base_name = Path(file_path).stem
        output_path = f"{base_name}_fields.csv"

    # 按路径深度和字母顺序排序
    sorted_fields = sorted(properties.items(), key=lambda x: (x[0].count('.'), x[0]))

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        # 写入表头
        writer.writerow(['字段路径', '数据类型', '出现率', '是否可选', '示例值', '字段描述'])

        for path, info in sorted_fields:
            presence_rate = info.get('presence_rate', 1.0)
            presence_str = f"{presence_rate * 100:.0f}%"
            optional_str = "是" if info.get('optional') else "否"
            samples = ', '.join(info['samples'][:1]) if info.get('samples') else ''
            samples = samples[:50]  # 限制长度

            # 获取字段描述
            description = ''
            if field_descriptions and path in field_descriptions:
                description = field_descriptions[path]

            writer.writerow([
                path,
                info.get('type', 'object'),
                presence_str,
                optional_str,
                samples,
                description
            ])

    print(f"CSV 报告已生成: {output_path}")
    return output_path


def load_field_descriptions(desc_file):
    """
    从文件加载字段描述

    支持格式：
    - JSON: {"字段路径": "描述", ...}
    - CSV: 字段路径,描述
    """
    if not os.path.exists(desc_file):
        return {}

    ext = Path(desc_file).suffix.lower()

    try:
        if ext == '.json':
            with open(desc_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        elif ext == '.csv':
            desc_map = {}
            with open(desc_file, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                header = next(reader, None)  # 跳过表头
                for row in reader:
                    if len(row) >= 2:
                        desc_map[row[0]] = row[1]
            return desc_map
    except Exception as e:
        print(f"警告: 无法加载字段描述文件: {e}")
        return {}

    return {}


def main():
    """命令行入口"""
    if len(sys.argv) < 2:
        print("用法: python analyze_json.py <json文件路径> [选项]")
        print("")
        print("选项:")
        print("  -o, --output <路径>    指定输出路径")
        print("  -f, --format <格式>    输出格式: markdown (默认) | csv")
        print("  -s, --sample <数量>    采样大小，默认 20")
        print("  -d, --desc <文件>      字段描述文件 (JSON 或 CSV)")
        print("")
        print("示例:")
        print("  # 生成 Markdown 报告")
        print("  python analyze_json.py data.json")
        print("")
        print("  # 生成 CSV 报告")
        print("  python analyze_json.py data.json -f csv")
        print("")
        print("  # 指定输出路径和采样大小")
        print("  python analyze_json.py data.json -o report.md -s 50")
        print("")
        print("  # 使用字段描述文件生成 CSV")
        print("  python analyze_json.py data.json -f csv -d descriptions.json")
        sys.exit(1)

    file_path = sys.argv[1]

    if not os.path.exists(file_path):
        print(f"错误: 文件不存在 - {file_path}")
        sys.exit(1)

    # 解析参数
    output_path = None
    output_format = 'markdown'
    sample_size = 20
    desc_file = None

    i = 2
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg in ('-o', '--output') and i + 1 < len(sys.argv):
            output_path = sys.argv[i + 1]
            i += 2
        elif arg in ('-f', '--format') and i + 1 < len(sys.argv):
            output_format = sys.argv[i + 1].lower()
            i += 2
        elif arg in ('-s', '--sample') and i + 1 < len(sys.argv):
            sample_size = int(sys.argv[i + 1])
            i += 2
        elif arg in ('-d', '--desc') and i + 1 < len(sys.argv):
            desc_file = sys.argv[i + 1]
            i += 2
        else:
            # 兼容旧版参数：analyze_json.py <json> <output> <sample>
            if i == 2 and not arg.startswith('-'):
                output_path = arg
            elif i == 3 and not arg.startswith('-') and output_path:
                try:
                    sample_size = int(arg)
                except ValueError:
                    pass
            i += 1

    print(f"分析文件: {file_path}")
    print(f"文件大小: {get_file_size_human(os.path.getsize(file_path))}")
    print(f"输出格式: {output_format}")
    print(f"采样大小: {sample_size}")
    print("分析中...")

    result = analyze_json_file(file_path, sample_size)

    print(f"完成!")
    print(f"  - 总记录数: {result['total_count']}")
    print(f"  - 字段数: {len(result['properties'])}")

    # 自动生成输出路径
    if not output_path:
        base_name = Path(file_path).stem
        if output_format == 'csv':
            output_path = f"{base_name}_fields.csv"
        else:
            output_path = f"{base_name}_analysis_report.md"

    # 根据格式生成报告
    if output_format == 'csv':
        field_descriptions = load_field_descriptions(desc_file) if desc_file else None
        generate_csv_report(file_path, result, output_path, field_descriptions)
    else:
        generate_markdown_report(file_path, result, output_path)


if __name__ == '__main__':
    main()
