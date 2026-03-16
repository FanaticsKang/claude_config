---
name: python-test-builder
description: |
  分析 Python 代码并自动生成全面的测试用例。

  **触发条件：**
  - 用户说"为这段代码生成测试"、"帮我写测试用例"
  - 用户提供了 Python 文件并希望得到测试
  - 用户要求验证代码的正确性
  - 用户提到 pytest、unittest、测试覆盖等关键词

  **核心原则：**
  1. 必须优先使用真实数据（如果用户能提供）
  2. 先写测试代码，运行验证后再生成报告
  3. 覆盖8大测试维度：功能性、边界条件、异常容错、数据完整性、性能压力、安全权限、兼容性、用户体验
---

# Python 测试生成器

## 工作流程

```
1. 读取代码 ────────────────────────┐
     │                              │
     ▼                              │
2. 询问用户是否有真实数据文件 ───────┤
     │                              │
     ▼                              │
3. 分析代码逻辑（8个维度）            │
     │                              │
     ▼                              │
4. 生成测试代码（使用真实数据）───────┤
     │                              │
     ▼                              │
5. 运行测试验证 ◄───────────────────┘
     │
     ▼
6. 根据实际运行结果编写测试报告
```

## 第1步：代码分析

读取用户提供的 Python 文件，识别：
- 类定义和方法
- 函数签名和参数
- 输入输出数据结构
- 关键业务逻辑
- 外部依赖（文件、网络、数据库等）
- 异常处理逻辑
- 状态机或条件分支

## 第2步：询问真实数据

**必须询问用户以下问题：**

1. "您是否有用于测试的真实数据文件？如果有，请提供文件路径。"
   - 如果有：记录文件路径，后续测试直接使用
   - 如果没有：询问"您希望我基于什么数据模式来构造测试数据？"

2. "您希望测试覆盖哪些特定场景？"
   - 让用户指出关键的业务逻辑或容易出错的点

3. "是否有特定的边界值或异常情况需要重点关注？"

**重要提醒：**
- 优先使用真实数据，这是最佳实践
- 构造数据可能导致测试不准确
- 如果用户提供了数据文件路径，直接在测试代码中使用该路径加载

## 第3步：测试维度分析（8大维度）

基于代码逻辑，从以下8个维度思考测试用例：

### 1. 功能性维度（Functional）
- **正向路径**：标准输入下的预期输出（Golden Path）
- **反向路径**：用户取消、中途退出、流程回退
- **等价类划分**：有效/无效等价类的代表值
- **状态转换**：状态机的各种转换条件

### 2. 边界与极端条件（Boundary & Edge Cases）
- **数值边界**：0、-1、最大值、最小值、空值（None）
- **容量边界**：空数组、单条数据、满容量、容量溢出
- **时间边界**：跨年、闰年、时区切换、超时临界点
- **长度边界**：空字符串、1字符、超长字符串

### 3. 异常与容错（Exception & Fault Tolerance）
- **输入异常**：乱码、特殊字符（\n, \0）、格式错误
- **资源异常**：文件不存在、权限不足、内存不足
- **依赖异常**：外部服务超时、返回格式错误
- **并发异常**：竞态条件、资源争抢（如适用）

### 4. 数据完整性与一致性（Data Integrity）
- **CRUD操作**：创建、读取、更新、删除的影响
- **数据精度**：浮点数精度、货币计算、四舍五入
- **事务一致性**：部分失败时的回滚、幂等性
- **编码问题**：中文字符、特殊字符处理

### 5. 性能与压力（Performance）
- **基准测试**：正常负载下的响应时间
- **负载测试**：数据量逐步增加时的表现
- **压力测试**：超出设计极限时的优雅降级
- **稳定性测试**：长时间运行的资源泄漏

### 6. 安全与权限（Security）
- **身份认证**：未授权访问、Token过期
- **权限控制**：越权访问、敏感数据暴露
- **敏感数据**：密码加密、日志脱敏
- **攻击防护**：注入攻击、暴力破解

### 7. 兼容性与集成（Compatibility）
- **版本兼容**：数据格式向前/向后兼容
- **环境兼容**：不同Python版本、操作系统
- **集成测试**：上下游接口契约

### 8. 用户体验与业务逻辑（UX & Business Logic）
- **场景化测试**：模拟真实用户的完整操作流程
- **误操作防护**：重复操作、异常输入处理
- **默认值处理**：参数省略时的行为

## 第4步：生成测试代码

### 4.1 测试框架选择

优先使用 **pytest**，按以下顺序选择：

1. **首选 pytest**：如果项目中已有 pytest 或没有测试框架
2. **次选 unittest**：如果项目中已有 unittest 测试
3. **兼容现有**：保持与项目现有测试框架一致

### 4.2 文件命名规范

```
被测文件: my_module.py
测试文件: test_my_module.py

被测文件: my_class.py (包含类 MyClass)
测试文件: test_my_class.py
```

### 4.3 测试代码结构

```python
import pytest
from pathlib import Path
import json

# 如果有真实数据文件，直接使用
REAL_DATA_FILE = Path("/path/to/real/data.json")

class TestMyClass:
    """MyClass 的测试类"""

    @pytest.fixture
    def real_data(self):
        """加载真实数据的 fixture"""
        if REAL_DATA_FILE.exists():
            with open(REAL_DATA_FILE, 'r') as f:
                return json.load(f)
        return None

    @pytest.fixture
    def instance(self):
        """创建被测实例的 fixture"""
        from my_module import MyClass
        return MyClass()

    # ===== 功能性测试 =====
    def test_normal_case(self, instance, real_data):
        """TC-001: 正常场景 - 标准输入应返回预期输出"""
        if real_data is None:
            pytest.skip("无真实数据")

        result = instance.process(real_data)
        # 不预设断言，先观察实际结果
        assert result is not None

    # ===== 边界条件测试 =====
    def test_empty_input(self, instance):
        """TC-B-001: 边界 - 空输入处理"""
        result = instance.process({})
        # 观察实际行为

    def test_none_input(self, instance):
        """TC-B-002: 边界 - None 输入处理"""
        result = instance.process(None)
        # 观察实际行为

    def test_single_item(self, instance):
        """TC-B-003: 边界 - 单条数据处理"""
        single_data = {"key": "value"}
        result = instance.process(single_data)
        # 观察实际行为

    # ===== 异常容错测试 =====
    def test_invalid_file_path(self, instance):
        """TC-E-001: 异常 - 文件不存在"""
        with pytest.raises((FileNotFoundError, Exception)):
            instance.load_from_file("/nonexistent/file.json")

    def test_malformed_data(self, instance):
        """TC-E-002: 异常 - 格式错误的数据"""
        bad_data = "not valid json"
        # 观察实际行为
        try:
            result = instance.process(bad_data)
        except Exception as e:
            # 记录实际抛出的异常类型
            pass

    # ===== 数据完整性测试 =====
    def test_data_preservation(self, instance, real_data):
        """TC-D-001: 数据 - 处理后数据完整性"""
        if real_data is None:
            pytest.skip("无真实数据")

        original_keys = set(real_data.keys()) if isinstance(real_data, dict) else set()
        result = instance.process(real_data)
        # 验证关键数据是否保留

    # ===== 性能测试（如适用） =====
    @pytest.mark.slow
    def test_large_data_performance(self, instance):
        """TC-P-001: 性能 - 大数据量处理"""
        import time
        large_data = {str(i): i for i in range(10000)}
        start = time.time()
        result = instance.process(large_data)
        elapsed = time.time() - start
        # 记录处理时间，不做硬性断言
```

### 4.4 关键原则

1. **真实数据优先**：
   ```python
   # 正确做法：直接使用真实文件
   with open("/path/to/real/data.json", 'r') as f:
       data = json.load(f)

   # 避免：手动构造数据
   data = {"fake_key": "fake_value"}  # 可能遗漏真实特征
   ```

2. **先观察，后断言**：
   ```python
   # 第一轮：不预设预期结果
   def test_normal_case(self, instance, real_data):
       result = instance.process(real_data)
       print(f"实际结果: {result}")  # 观察

   # 第二轮：基于实际运行结果添加断言
   def test_normal_case(self, instance, real_data):
       result = instance.process(real_data)
       assert result["count"] == 10  # 基于实际观察
   ```

3. **注释记录观察**：
   ```python
   def test_edge_case(self, instance):
       """TC-B-005: 边界测试

       观察记录：
       - 输入: None
       - 实际行为: 返回空字典
       - 是否预期: 是/否
       """
       result = instance.process(None)
       assert result == {}
   ```

## 第5步：运行测试验证

**必须执行以下步骤：**

1. 安装依赖（如需要）：
   ```bash
   pip install pytest pytest-asyncio
   ```

2. 运行测试：
   ```bash
   pytest test_xxx.py -v
   ```

3. 记录实际结果：
   - 哪些测试通过了
   - 哪些测试失败了
   - 实际的返回值是什么
   - 抛出了什么异常

4. 根据实际结果调整测试：
   - 如果测试失败是因为预期错误 → 修正预期
   - 如果测试失败是因为代码 bug → 记录问题

## 第6步：生成测试报告

**重要：测试报告必须基于实际运行结果！**

### 报告结构

```markdown
# 测试报告

## 测试概览

- **被测文件**: `my_module.py`
- **测试文件**: `test_my_module.py`
- **测试框架**: pytest
- **运行时间**: YYYY-MM-DD HH:MM:SS
- **真实数据**: 是/否 (文件路径: xxx)

## 测试结果摘要

| 维度 | 用例数 | 通过 | 失败 | 跳过 |
|------|--------|------|------|------|
| 功能性 | 3 | 3 | 0 | 0 |
| 边界条件 | 4 | 3 | 1 | 0 |
| 异常容错 | 3 | 2 | 1 | 0 |
| 数据完整性 | 2 | 2 | 0 | 0 |
| 性能 | 1 | 0 | 0 | 1 |
| 总计 | 13 | 10 | 2 | 1 |

## 详细测试用例

### 功能性测试

#### TC-F-001: 正常场景 - 标准输入
- **目的**: 验证正常输入下的预期输出
- **输入**: 使用真实数据 `data.json`
- **实际结果**: [基于测试运行的实际输出]
- **状态**: ✅ 通过 / ❌ 失败
- **备注**: [如有]

#### TC-F-002: 反向路径 - 空输入
- **目的**: 验证空输入的处理
- **输入**: `{}`
- **实际结果**: [实际观察]
- **状态**: ✅ 通过 / ❌ 失败

### 边界条件测试

#### TC-B-001: 数值边界 - 零值处理
- **目的**: 验证输入为 0 时的行为
- **输入**: `{"count": 0}`
- **实际结果**: [实际观察]
- **状态**: ✅ 通过 / ❌ 失败

[... 其他测试用例 ...]

## 发现的问题

### 问题 1
- **用例**: TC-E-001
- **描述**: 文件不存在时没有抛出预期异常
- **实际行为**: 返回空字典而非抛出 FileNotFoundError
- **建议**: [是否需要修复代码]

## 测试覆盖率分析

- **代码行覆盖率**: XX%
- **分支覆盖率**: XX%
- **未覆盖代码**: [列出关键未覆盖逻辑]

## 建议

1. [...]
2. [...]
```

### 关键提醒

1. **不要编造预期结果**：报告中的"实际结果"必须来自测试运行
2. **区分预期和实际**：明确标注哪些是代码的预期行为，哪些是测试观察到的实际行为
3. **失败不一定是坏事**：测试失败可能揭示了代码的 bug 或边界情况
4. **记录真实数据的使用**：注明使用了哪些真实数据文件

## 完整示例流程

### 用户输入

"请为我的数据处理器生成测试用例，文件是 `data_processor.py`，真实数据在 `/data/sample.json`"

### 执行步骤

1. **读取代码**: 分析 `data_processor.py` 的结构
2. **确认数据**: 确认使用 `/data/sample.json` 作为真实数据
3. **分析维度**: 从8个维度思考测试点
4. **生成测试**: 创建 `test_data_processor.py`
5. **运行验证**: 执行 `pytest test_data_processor.py -v`
6. **编写报告**: 基于实际运行结果生成测试报告

### 生成的测试代码示例

```python
import pytest
from pathlib import Path
import json
from data_processor import DataProcessor

# 使用用户提供的真实数据
REAL_DATA_FILE = Path("/data/sample.json")

class TestDataProcessor:
    """DataProcessor 全面测试"""

    @pytest.fixture
    def processor(self):
        return DataProcessor()

    @pytest.fixture
    def real_data(self):
        """加载真实数据"""
        if REAL_DATA_FILE.exists():
            with open(REAL_DATA_FILE, 'r') as f:
                return json.load(f)
        return None

    # ========== 功能性测试 ==========

    def test_process_with_real_data(self, processor, real_data):
        """TC-F-001: 使用真实数据的正常处理流程"""
        if real_data is None:
            pytest.skip("真实数据文件不存在")

        result = processor.process(real_data)
        # 先记录实际结果，不做断言
        print(f"处理结果类型: {type(result)}")
        print(f"处理结果: {result}")
        assert result is not None

    # ========== 边界条件测试 ==========

    def test_process_empty_dict(self, processor):
        """TC-B-001: 空字典输入"""
        result = processor.process({})
        # 观察实际行为
        print(f"空字典处理结果: {result}")

    def test_process_none(self, processor):
        """TC-B-002: None 输入"""
        result = processor.process(None)
        print(f"None 处理结果: {result}")

    def test_process_single_record(self, processor):
        """TC-B-003: 单条记录输入"""
        single = {"id": 1, "value": "test"}
        result = processor.process(single)
        print(f"单条记录处理结果: {result}")

    # ========== 异常容错测试 ==========

    def test_process_invalid_json(self, processor):
        """TC-E-001: 无效的 JSON 字符串输入"""
        invalid = "not valid json {"
        try:
            result = processor.process(invalid)
            print(f"无效输入的处理结果: {result}")
        except Exception as e:
            print(f"无效输入抛出异常: {type(e).__name__}: {e}")

    def test_load_nonexistent_file(self, processor):
        """TC-E-002: 加载不存在的文件"""
        try:
            result = processor.load_from_file("/nonexistent/file.json")
            print(f"文件不存在时的结果: {result}")
        except Exception as e:
            print(f"文件不存在时抛出: {type(e).__name__}: {e}")

    # ========== 数据完整性测试 ==========

    def test_data_preservation(self, processor, real_data):
        """TC-D-001: 验证处理后关键数据保留"""
        if real_data is None:
            pytest.skip("无真实数据")

        original_keys = set(real_data.keys())
        result = processor.process(real_data)

        if isinstance(result, dict):
            result_keys = set(result.keys())
            # 检查是否有数据丢失
            lost_keys = original_keys - result_keys
            if lost_keys:
                print(f"处理过程中丢失的键: {lost_keys}")

    # ========== 性能测试 ==========

    @pytest.mark.slow
    def test_large_dataset_performance(self, processor):
        """TC-P-001: 大数据集处理性能"""
        import time

        # 生成大测试数据
        large_data = {str(i): {"value": i} for i in range(10000)}

        start = time.time()
        result = processor.process(large_data)
        elapsed = time.time() - start

        print(f"处理 10000 条记录耗时: {elapsed:.3f}s")
        # 记录性能，不做硬性断言
```

### 运行测试后的报告

```markdown
# DataProcessor 测试报告

## 测试概览

- **被测文件**: `data_processor.py`
- **测试文件**: `test_data_processor.py`
- **真实数据**: `/data/sample.json` (存在)
- **运行时间**: 2024-01-15 10:30:00

## 测试结果

| 维度 | 用例数 | 通过 | 失败 | 跳过 |
|------|--------|------|------|------|
| 功能性 | 1 | 1 | 0 | 0 |
| 边界条件 | 3 | 3 | 0 | 0 |
| 异常容错 | 2 | 1 | 1 | 0 |
| 数据完整性 | 1 | 1 | 0 | 0 |
| 性能 | 1 | 0 | 0 | 1 |
| **总计** | **8** | **6** | **1** | **1** |

## 详细结果

### TC-F-001: 正常处理流程 ✅
- **输入**: 真实数据 (320KB JSON)
- **实际输出**: 处理后返回 dict，包含 15 个键
- **处理时间**: 0.045s

### TC-E-002: 文件不存在处理 ❌
- **问题**: 代码没有检查文件存在性，直接抛出 FileNotFoundError
- **建议**: 添加文件存在性检查或提供更友好的错误信息

### TC-P-001: 性能测试 ⏭️
- **状态**: 跳过 (标记为 slow)
- **说明**: 需要 `pytest -m slow` 运行

## 建议

1. 为文件操作添加异常处理
2. 考虑添加输入数据验证
3. 性能测试显示处理速度良好
```

## 注意事项

1. **始终先问真实数据**：这是最关键的步骤
2. **不要预设预期结果**：先运行，后断言
3. **记录观察**：用注释记录测试过程中的发现
4. **区分测试维度和测试用例**：维度是思考框架，用例是具体测试
5. **保持灵活**：不是所有维度都适用于所有代码，根据代码特点选择