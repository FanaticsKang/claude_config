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

## 使用方法

### 命令行方式

```bash
python scripts/analyze_json.py <json文件路径> [输出路径] [采样大小]
```

### 参数说明

- **json文件路径**（必需）：要分析的 JSON 文件路径
- **输出路径**（可选）：生成的 Markdown 报告路径，默认 `<文件名>_analysis_report.md`
- **采样大小**（可选）：同质结构分析时的采样数，默认 20

### 使用示例

```bash
# 基本用法
python scripts/analyze_json.py data.json

# 指定输出路径
python scripts/analyze_json.py data.json report.md

# 指定采样大小（大文件建议增加采样）
python scripts/analyze_json.py data.json report.md 50
```

### Python API 方式

```python
from scripts.analyze_json import analyze_json_file, generate_markdown_report

# 分析文件
result = analyze_json_file('algo_env.json', sample_size=20)

# 生成报告
generate_markdown_report(
    'algo_env.json',
    result,
    'algo_env_schema.md'
)

print(f"总记录数: {result['total_count']}")
print(f"字段数: {len(result['properties'])}")
```

## 输出示例

生成的报告包含：

```markdown
# JSON 文件结构分析报告

**源文件**: `algo_env.json`
**文件大小**: 154.27 MB
**总记录数**: 774
**分析字段数**: 456

## 结构特点

- **顶层键类型**: 毫秒级时间戳（如 17687934610349602）
- **实例数量**: 774 个
- **可选字段**: 27 个（部分实例可能缺失）

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

## 字段详细说明

| 字段路径 | 类型 | 出现率 | 示例值 |
|----------|------|--------|--------|
| `header.frame_id` | string | 100% | vcs[Cognition] excute_time... |
| `header.seq` | integer | 100% | 81908 |
| `lanes[].id` | integer | 100% | 5663 |
| `lanes[].lane_type?` | string | 80% | ENUM_NONE |
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
