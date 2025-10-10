# check your new code and make sure AI follow your coding style

## custom coding style

### 1. 优先检查与尽早返回（Prioritize Checks and Return Early）​​
本条规则强调，在编写函数或代码块时，​应首先验证前置条件、参数有效性和可能的错误情况。一旦发现不满足条件或出现错误，​立即通过 return、exit、continue、break 或抛出异常等方式终止当前流程。这使得代码的主体逻辑能够保持最少的嵌套层级，清晰且直接地呈现其主要任务。比如
```
# 应减少下面的逻辑
if condition:
    main_process
else
    print/continue/return/exit

## 应将其改为下述逻辑，减少嵌套
if not condition:
    print/continue/return/exit
main_process
```

## TODO
1. 使用 `git diff` 查看新的代码；
2. 检查并修改使得这些代码遵守了上述的`custom coding style`；
3. 检查运行；