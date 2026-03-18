---
name: deep-simplify
description: |
  深度简化Python代码，通过运行时日志分析识别并移除死代码。
  当用户需要简化代码、清理未使用的代码、优化代码结构、移除死代码时使用此skill。
  适用于：代码清理、死代码检测、代码重构前的分析、代码库瘦身。
  使用方法：/deep-simplify <file_path>
---

# 深度简化代码 (Deep Simplify)

通过运行时日志分析，识别并移除Python代码中未被实际执行的"死代码"。

## 触发条件

当用户有以下请求时触发此skill：
- "简化这个文件"
- "清理死代码"
- "移除未使用的代码"
- "分析代码覆盖率"
- "/deep-simplify <文件路径>"

## 工作流程

1. **验证输入**：检查文件路径是否有效
2. **代码插桩**：在目标文件的所有函数、循环、if-else分支中插入日志标记
3. **运行收集**：执行主程序，收集代码覆盖日志
4. **日志分析**：分析哪些代码路径被执行，哪些从未被执行
5. **死代码识别**：确定未被访问的代码区域（排除测试用例）
6. **代码简化**：安全地移除确认的死代码
7. **验证**：再次运行确保程序正常工作

## 执行步骤

### 前提检查
- 确保项目根目录存在 `main.py` 作为主程序入口
- 确保已安装 `astor` 库（用于AST代码生成）

### Step 1: 验证输入
检查用户提供的文件路径：
- 路径不能为空
- 文件必须存在
- 必须是 `.py` 文件
- 一次只能处理一个文件

如果不满足条件，向用户说明原因并退出。

### Step 2: 代码插桩
使用 `scripts/instrument.py` 对目标文件进行插桩：

```bash
python /Users/kang/.claude/skills/deep-simplify/scripts/instrument.py <file_path>
```

插桩位置包括：
- 函数定义的第一行（`func_entry`）
- for/while循环体内部（`loop_entry`）
- if/elif/else分支内部（`if_branch`/`elif_branch`/`else_branch`）
- try/except/finally块内部（`try_block`/`except_block`/`finally_block`）

插桩后的日志格式：
```python
print(f"[DEEP_SIMPLIFY] {file_name}:{line_number}:{function_name}:{tag_type}")
```

原文件会被备份为 `.bak` 文件。

### Step 3: 运行主程序收集日志
执行项目主程序：

```bash
cd /Users/kang/Documents/workspace/rebuild_data_flow && python main.py
```

捕获所有输出（stdout和stderr），筛选包含 `[DEEP_SIMPLIFY]` 的日志行。

### Step 4: 分析代码覆盖
解析收集到的日志，与插桩点对比：

1. 提取所有插桩点（使用 `extract_instrumentation_points` 函数）
2. 解析执行日志，获取实际执行的代码点
3. 计算覆盖率：`已执行点数 / 总插桩点数`
4. 识别死代码：
   - 从未执行的函数
   - 从未执行的分支
   - 从未执行的循环

### Step 5: 确定可移除的死代码
过滤死代码列表：
- 排除测试函数（以 `test_` 开头）
- 分析上下文依赖，确认移除是安全的
- 生成死代码报告，包含：
  - 文件位置（行号）
  - 代码类型（函数/分支/循环）
  - 代码内容预览

### Step 6: 执行代码简化
使用 `scripts/simplify.py` 移除确认的死代码：

```bash
python /Users/kang/.claude/skills/deep-simplify/scripts/simplify.py <file_path> <analysis_json> <output_path>
```

简化规则：
- 移除整个死函数定义
- 简化if语句：如果if分支死亡但else存活，用else内容替换整个if
- 如果整个if-else都死亡，移除整个块

### Step 7: 验证简化结果
再次运行主程序：

```bash
cd /Users/kang/Documents/workspace/rebuild_data_flow && python main.py
```

- 如果程序正常执行（返回码0），简化成功
- 如果程序失败，从备份恢复原始文件，并报告错误

### 清理
删除临时文件：
- `.deep_simplify_logs.txt`
- `.deep_simplify_inst.txt`

保留备份文件 `.bak` 供用户需要时手动恢复。

## 输出报告格式

执行完成后输出简洁报告：

```
============================================================
代码简化完成!
============================================================
文件: <file_path>
总插桩点: <count>
已执行: <count> (<rate>%)
死代码: <count> 个
  - 未使用函数: <count>
  - 未执行分支: <count>
已移除: <count> 个代码项
验证: 通过
原始备份: <file_path>.bak
```

## 注意事项

1. **单次只能处理一个文件**：确保专注分析，避免复杂依赖问题
2. **需要main.py**：项目必须有可执行的main.py作为主入口
3. **备份原文件**：简化前会自动创建 `.bak` 备份
4. **测试用例排除**：分析时会排除测试代码对主代码的访问
5. **保守策略**：不确定是否可移除的代码会保留，由用户决定

## 依赖安装

如果缺少 `astor` 库，自动安装：
```bash
pip install astor
```

## 手动恢复

如果简化后出现问题，手动恢复：
```bash
cp <file_path>.bak <file_path>
```
