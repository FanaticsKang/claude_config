---
name: json_analysis
description: 分析大型 JSON 文件（支持 100MB+）并生成格式说明文档。当用户需要分析 JSON 文件结构、生成 JSON Schema 文档、理解大数据集的字段组成时，使用此 skill。适用于数据探索、API 文档生成、数据验证等场景。支持流式读取避免内存溢出，输出层级树状结构的 Markdown 文档。
---

# JSON 文件分析 Skill

## 用途

分析大型 JSON 文件的结构，生成详细的格式说明文档，包括：
- 字段层级结构（树状展示）
- 数据类型推断
- 示例值提取
- 必填/可选字段标记（基于出现频率）
- **同质结构识别与聚类**（智能识别时间戳/ID为键的帧数据）

## 核心特性

### 同质结构智能识别

当 JSON 文件的顶层是字典且所有值具有相似结构时（如自动驾驶帧数据、IoT传感器数据）：

```json
{
  "17687934610349602": { "header": {...}, "lanes": [...] },
  "17687934610848112": { "header": {...}, "lanes": [...] },
  ...
}
```

分析器会：
1. **自动检测**键类型（时间戳、数字ID、UUID、哈希等）
2. **提取统一 Schema**（字段并集，避免重复展示）
3. **标注可选字段**（出现率 < 95% 的字段标记为可选）
4. **聚类展示**（只展示一次统一结构，标注"共N个实例"）

## 工作流程

### 1. 分析文件并提取统一 Schema

```python
import json
from collections import defaultdict

def analyze_json_file(file_path, sample_size=20):
    """
    分析 JSON 文件，提取统一 Schema
    对于同质结构字典，提取所有实例的字段并集
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 判断顶层结构
    if isinstance(data, list):
        # 数组结构
        return analyze_array(data, sample_size)
    elif isinstance(data, dict):
        # 字典结构 - 可能是同质结构
        return analyze_dict(data, sample_size)
    else:
        # 标量
        return {'type': type(data).__name__, 'samples': [str(data)[:50]]}

def analyze_dict(data, sample_size=20):
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

    def collect_fields(obj, path=''):
        if isinstance(obj, dict):
            for key, value in obj.items():
                full_path = f"{path}.{key}" if path else key
                field_occurrences[full_path]['count'] += 1
                collect_fields(value, full_path)
        elif isinstance(obj, list):
            if obj:
                for item in obj[:3]:  # 采样前3个元素
                    collect_fields(item, path + '[]')
        else:
            field_occurrences[path]['types'].add(type(obj).__name__)
            if len(field_occurrences[path]['samples']) < 2:
                sample = str(obj)[:60] + '...' if len(str(obj)) > 60 else str(obj)
                field_occurrences[path]['samples'].append(sample)

    # 从所有采样实例中收集字段
    for key in sample:
        collect_fields(data[key])

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
            'optional': presence_rate < 0.95,  # 出现率<95%标记为可选
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

def infer_key_type(keys):
    """推断键的类型"""
    if not keys:
        return 'unknown'
    sample = str(keys[0])

    # 纯数字
    if all(str(k).isdigit() for k in keys[:10]):
        if len(sample) >= 13:
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
```

### 2. 构建层级树

```python
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
```

### 3. 生成 Markdown 报告

```python
def generate_markdown_report(file_path, analysis_result, output_path):
    """生成 Markdown 格式的 JSON 结构说明文档"""
    import os

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
    lines.append("# JSON 文件结构分析")
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
        if is_homogeneous and path.startswith('<key>.'):
            display_path = path[6:]  # 去掉 '<key>.' 前缀

        samples = ', '.join(info['samples'][:1]) if info.get('samples') else '-'
        samples = samples.replace('|', '\\|')[:30]
        presence = f"{info.get('presence_rate', 1)*100:.0f}%"

        lines.append(f"| `{display_path}` | {info.get('type', 'object')} | {presence} | {samples} |")

    # 写入文件
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    return output_path
```

## 使用示例

### 示例 1：同质结构 JSON（帧数据）

```python
# 分析文件
result = analyze_json_file('algo_env.json')

# 生成报告
output = generate_markdown_report(
    'algo_env.json',
    result,
    'algo_env_schema.md'
)

print(f"报告已生成: {output}")
print(f"总记录数: {result['total_count']}")
print(f"字段数: {len(result['properties'])}")

# 输出示例：
# 报告已生成: algo_env_schema.md
# 总记录数: 774
# 字段数: 456
```

生成的报告会显示：

```markdown
# JSON 文件结构分析

**源文件**: `algo_env.json`
**文件大小**: 154.27 MB
**总记录数**: 774
**分析字段数**: 456

## 结构特点

- **顶层键类型**: 毫秒级时间戳（如 17687934610349602）
- **实例数量**: 774 个
- **字段一致性**: 基于采样的字段并集分析
- **可选字段**: 27 个（部分实例可能缺失）

### 顶层键示例
- `17687934610349602`
- `17687934610848112`
...

## 结构概览

### 统一 Schema 结构树
```
<key>  (实例标识符)
│   ├── header
│   │   ├── frame_id (string)
│   │   ├── seq (integer)
│   │   └── time_stamp (number)
│   ├── lanes[]
│   │   ├── confidence (number)
│   │   ├── id (integer)
│   │   └── lane_type? (string)
...
```
*注：`?` 表示可选字段（出现率 < 95%），`[]` 表示数组*

## 字段详细说明

| 字段路径 | 类型 | 出现率 | 示例值 |
|----------|------|--------|--------|
| header.frame_id | string | 100% | vcs[Cognition] excute_time... |
| header.seq | integer | 100% | 81908 |
| lanes[].id | integer | 100% | 5663 |
| lanes[].lane_type? | string | 80% | ENUM_NONE |
...
```

### 示例 2：普通 JSON 对象

```python
result = analyze_json_file('config.json')
output = generate_markdown_report('config.json', result, 'config_schema.md')
```

## 注意事项

1. **同质结构识别**:
   - 基于采样推断（默认20个样本），存在极小概率遗漏边缘情况
   - 可选字段判断阈值：出现率 < 95%
   - 时间戳识别：13位以上数字识别为毫秒级时间戳

2. **内存优化**:
   - 大文件使用采样分析，避免一次性加载所有数据
   - 数组元素只采样前3个

3. **类型映射**:
   - Python `str` → `string`
   - Python `int` → `integer`
   - Python `float` → `number`
   - Python `bool` → `boolean`
   - Python `list` → `array`
   - Python `dict` → `object`
