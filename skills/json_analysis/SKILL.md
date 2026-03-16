---
name: json_analysis
description: 分析大型 JSON 文件（支持 100MB+）并生成格式说明文档（Markdown 或 CSV）。当用户需要分析 JSON 文件结构、生成 JSON Schema 文档、理解大数据集的字段组成、或导出字段清单时，使用此 skill。适用于数据探索、API 文档生成、数据验证、字段清单导出等场景。支持流式读取避免内存溢出，输出层级树状结构的 Markdown 文档或结构化 CSV 表格。
---

# JSON 文件分析 Skill

## 用途

分析大型 JSON 文件的结构，生成详细的格式说明文档，包括：
- 字段层级结构（树状展示）
- 数据类型推断
- 示例值提取
- 必填/可选字段标记（基于出现频率）
- **同质结构识别与聚类**（智能识别时间戳/ID为键的帧数据）
- **CSV 字段清单导出**（支持自定义字段描述）

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

### 多格式输出支持

支持 Markdown（默认）和 CSV 两种输出格式：

- **Markdown**: 适合阅读的结构化报告，包含树状图和表格
- **CSV**: 适合导入 Excel/数据库的字段清单，支持自定义字段描述

## 使用方法

### 命令行方式

```bash
python scripts/analyze_json.py <json文件路径> [选项]
```

### 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `json文件路径` | 要分析的 JSON 文件路径 | 必需 |
| `-o, --output <路径>` | 指定输出文件路径 | 自动生成 |
| `-f, --format <格式>` | 输出格式：`markdown` 或 `csv` | `markdown` |
| `-s, --sample <数量>` | 采样大小（同质结构分析时） | 20 |
| `-d, --desc <文件>` | 字段描述文件（JSON/CSV） | 无 |

### 使用示例

#### 1. 生成 Markdown 报告（默认）

```bash
# 基本用法
python scripts/analyze_json.py data.json

# 指定输出路径
python scripts/analyze_json.py data.json -o report.md

# 指定采样大小（大文件建议增加采样）
python scripts/analyze_json.py data.json -s 50
```

#### 2. 生成 CSV 字段清单

```bash
# 生成 CSV 格式
python scripts/analyze_json.py data.json -f csv

# 指定输出路径
python scripts/analyze_json.py data.json -f csv -o fields.csv
```

#### 3. 使用字段描述文件生成 CSV

创建字段描述文件 `descriptions.json`：

```json
{
  "header.frame_id": "帧ID",
  "header.seq": "序列号",
  "header.time_stamp": "时间戳（毫秒）",
  "lanes[].id": "车道线ID",
  "lanes[].lane_type": "车道线类型"
}
```

或使用 CSV 格式 `descriptions.csv`：

```csv
字段路径,描述
header.frame_id,帧ID
header.seq,序列号
header.time_stamp,时间戳（毫秒）
```

然后运行：

```bash
python scripts/analyze_json.py data.json -f csv -d descriptions.json
```

#### 4. 兼容旧版参数格式

```bash
# 旧版格式仍然支持
python scripts/analyze_json.py data.json report.md 50
```

### Python API 方式

#### 分析文件并生成 Markdown 报告

```python
from scripts.analyze_json import analyze_json_file, generate_markdown_report

# 分析文件
result = analyze_json_file('algo_env.json', sample_size=20)

# 生成 Markdown 报告
generate_markdown_report(
    'algo_env.json',
    result,
    'algo_env_schema.md'
)

print(f"总记录数: {result['total_count']}")
print(f"字段数: {len(result['properties'])}")
```

#### 生成 CSV 报告

```python
from scripts.analyze_json import analyze_json_file, generate_csv_report

# 分析文件
result = analyze_json_file('algo_env.json', sample_size=20)

# 定义字段描述（可选）
field_descriptions = {
    "anchor_pos.lng": "锚点经度（度）",
    "anchor_pos.lat": "锚点纬度（度）",
    "anchor_pos.height": "锚点海拔高度（米）",
    "idmap_status.map_available": "地图是否可用"
}

# 生成 CSV 报告
generate_csv_report(
    'algo_env.json',
    result,
    'algo_env_fields.csv',
    field_descriptions=field_descriptions
)
```

#### 加载字段描述文件

```python
from scripts.analyze_json import load_field_descriptions

# 从 JSON 文件加载
desc_map = load_field_descriptions('descriptions.json')

# 从 CSV 文件加载
desc_map = load_field_descriptions('descriptions.csv')
```

## 输出示例

### Markdown 格式

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

### CSV 格式

CSV 文件包含以下列：

| 列名 | 说明 |
|------|------|
| `字段路径` | 字段的完整路径（如 `header.frame_id`） |
| `数据类型` | 推断的数据类型（string/integer/number/boolean/array/object） |
| `出现率` | 字段在记录中出现的百分比 |
| `是否可选` | 出现率 < 95% 标记为"是" |
| `示例值` | 采样获取的示例值 |
| `字段描述` | 从描述文件加载的字段说明（如有） |

CSV 示例：

```csv
字段路径,数据类型,出现率,是否可选,示例值,字段描述
anchor_pos.lng,number,100%,否,106.81946189087571,锚点经度（度）
anchor_pos.lat,number,100%,否,29.760760436992676,锚点纬度（度）
header.frame_id,string,100%,否,vcs[Cognition],帧ID
lanes[].id,integer,95%,是,5663,车道线ID
```

## 注意事项

1. **同质结构识别**:
   - 基于采样推断（默认20个样本），存在极小概率遗漏边缘情况
   - 可选字段判断阈值：出现率 < 95%
   - 时间戳识别：13位以上数字识别为毫秒级时间戳，16位以上为纳秒级

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

4. **CSV 输出**:
   - 使用 UTF-8 编码，支持中文描述
   - 如需在 Excel 中打开中文 CSV，建议使用"数据→从文本/CSV 导入"功能
