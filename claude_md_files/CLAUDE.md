# CLAUDE.md

## 1. 项目约定
1. 设计新类时以简洁高效为原则，不引入多余功能；若需要扩展功能，必须先询问用户确认。
2. 所有程序的注释和可读文件均使用中文，但是注意所有在程序中`print`或者绘制（`plot`）的文字均使用英文。

## 2. 代码风格
### 2.1 命名规范

**变量和函数名**
- 格式：小写字母 + 下划线
- 示例：`user_name`、`get_user_info()`

**常量**
- 格式：全大写字母 + 下划线
- 示例：`MAX_RETRY_COUNT`、`DEFAULT_TIMEOUT`

**类名**
- 格式：大驼峰（每个单词首字母大写，无分隔符）
- 示例：`UserManager`、`HttpRequestHandler`

**文件名**
- 格式：小写字母 + 下划线，与文件内核心类名对应
- 转换规则（PascalCase → snake_case）：
  - `EgoMsgMapNode` → `ego_msg_map_node.py`
  - `HttpRequestHandler` → `http_request_handler.py`
  - `UserManager` → `user_manager.py`
  - `APIGateway` → `api_gateway.py`
  - `XMLParser` → `xml_parser.py`

### 2.2 优先检查与尽早返回（Prioritize Checks and Return Early）

本条规则强调，在编写函数或代码块时，应首先验证前置条件、参数有效性和可能的错误情况。一旦发现不满足条件或出现错误，立即通过 return、exit、continue、break 或抛出异常等方式终止当前流程。这使得代码的主体逻辑能够保持最少的嵌套层级，清晰且直接地呈现其主要任务。

```python
# 应减少下面的逻辑
if condition:
    main_process()
else:
    print("Invalid condition")
    return

# 应将其改为下述逻辑，减少嵌套
if not condition:
    print("Invalid condition")
    return
main_process()
```

## 3. 编码原则
### 3.1 防止过度设计
1. **只改请求的文件**：用户让改 A，就只改 A，不衍生出 B、C、D；
2. **保持 API 兼容**：除非明确要求，否则不改变原有接口；
3. **解决具体问题**：只解决用户明确指出的问题，不为"未来可能"的需求编码；
4. **简洁优先**：能不加的类就不加，能不拆的文件就不拆；
5. **询问确认**：超出明确范围的改动，先询问用户再执行。

### 3.2 不要添加未被要求的内容
1. **不添加额外的成员变量**：如用户未要求字段；
2. **不使用命名空间**：除非用户要求或现有代码已使用，否则不主动包裹 `namespace`；
3. **不添加构造函数/方法**：除非用户要求，不添加 `Reset()`、`构造函数` 等方法；
4. **严格按需求实现**：用户要求做什么就做什么，不多做一步。

### 3.3 重构代码规则
1. 当你修改一个文件的代码超过50%的时候，触发重构代码；
2. 当你重构代码的时候，不要在原有代码上进行修改，你应该将原有代码进行备份，然后完全重写这个代码，在验证功能通过后，删除原有备份。·

## 4. 工作流程

- 修改前，简要说明**打算做什么**；
- 修改后，简要说明**改了什么**；
- 遇到不确定的需求，先提问，再动手。
