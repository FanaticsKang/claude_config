#!/usr/bin/env python3
"""
主执行脚本：整合代码简化流程
"""
import os
import sys
import json
import subprocess
import shutil
from pathlib import Path

# 脚本目录
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = Path.cwd()


def run_command(cmd: list, capture=True) -> tuple:
    """运行命令并返回结果"""
    try:
        if capture:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=PROJECT_ROOT
            )
            return result.returncode, result.stdout, result.stderr
        else:
            result = subprocess.run(cmd, cwd=PROJECT_ROOT)
            return result.returncode, "", ""
    except Exception as e:
        return 1, "", str(e)


def step1_validate(file_path: str) -> bool:
    """验证输入"""
    print("\n" + "="*60)
    print("Step 1: 验证输入")
    print("="*60)

    if not file_path:
        print("错误: 未提供文件路径")
        return False

    if not os.path.exists(file_path):
        print(f"错误: 文件不存在: {file_path}")
        return False

    if not file_path.endswith('.py'):
        print(f"错误: 不是Python文件: {file_path}")
        return False

    print(f"✓ 目标文件: {file_path}")
    return True


def step2_instrument(file_path: str) -> tuple:
    """代码插桩"""
    print("\n" + "="*60)
    print("Step 2: 代码插桩")
    print("="*60)

    instrument_script = SCRIPT_DIR / "instrument.py"

    # 检查依赖
    try:
        import astor
    except ImportError:
        print("安装依赖: astor...")
        subprocess.run([sys.executable, "-m", "pip", "install", "astor", "-q"])

    # 运行插桩
    cmd = [sys.executable, str(instrument_script), file_path]
    returncode, stdout, stderr = run_command(cmd)

    if returncode != 0:
        print(f"插桩失败: {stderr}")
        return None, 0

    # 解析输出获取备份路径和插桩数量
    backup_path = file_path + ".bak"
    count = 0
    for line in stdout.split('\n'):
        if 'Instrumented' in line:
            try:
                count = int(line.split()[1])
            except:
                pass
        if 'Backup saved to:' in line:
            backup_path = line.split(': ')[1].strip()

    print(f"✓ 插桩完成: {count} 个跟踪点")
    print(f"✓ 备份文件: {backup_path}")

    return backup_path, count


def step3_run_main() -> str:
    """运行主程序收集日志"""
    print("\n" + "="*60)
    print("Step 3: 运行主程序收集日志")
    print("="*60)

    main_script = PROJECT_ROOT / "main.py"
    if not main_script.exists():
        print(f"错误: 未找到 main.py")
        return None

    cmd = [sys.executable, str(main_script)]
    returncode, stdout, stderr = run_command(cmd)

    # 合并stdout和stderr
    full_output = stdout + "\n" + stderr

    # 保存日志
    log_file = PROJECT_ROOT / ".deep_simplify_logs.txt"
    with open(log_file, 'w', encoding='utf-8') as f:
        f.write(full_output)

    # 统计日志条目
    log_count = full_output.count('[DEEP_SIMPLIFY]')
    print(f"✓ 程序执行完成 (返回码: {returncode})")
    print(f"✓ 收集到 {log_count} 条执行日志")
    print(f"✓ 日志保存至: {log_file}")

    return str(log_file)


def step4_analyze(file_path: str, log_file: str) -> dict:
    """分析日志"""
    print("\n" + "="*60)
    print("Step 4: 分析代码覆盖")
    print("="*60)

    # 提取插桩点
    from instrument import extract_instrumentation_points
    points = extract_instrumentation_points(file_path)

    # 保存插桩点记录
    inst_log = PROJECT_ROOT / ".deep_simplify_inst.txt"
    with open(inst_log, 'w') as f:
        for line, func, tag in points:
            f.write(f"{line}:{func}:{tag}\n")

    # 读取日志
    with open(log_file, 'r') as f:
        log_content = f.read()

    # 解析执行日志
    from analyze import parse_logs, analyze_coverage

    executed = parse_logs(log_content)
    file_name = os.path.basename(file_path)
    exec_points = executed.get(file_name, set())

    # 读取源代码
    with open(file_path, 'r', encoding='utf-8') as f:
        source_lines = f.readlines()

    # 分析
    analysis = analyze_coverage(points, exec_points, source_lines)

    # 打印报告
    from analyze import generate_report
    report = generate_report(analysis, file_name)
    print(report)

    return analysis


def step5_identify_dead_code(analysis: dict) -> tuple:
    """确定死代码"""
    print("\n" + "="*60)
    print("Step 5: 确定可移除的死代码")
    print("="*60)

    dead_functions = analysis.get('unused_functions', [])
    dead_branches = analysis.get('unused_branches', [])

    # 过滤测试相关的
    filtered_funcs = [
        f for f in dead_functions
        if not f['function'].startswith('test_')
    ]

    print(f"可移除的函数 ({len(filtered_funcs)}个):")
    for f in filtered_funcs:
        print(f"  - 第{f['line']}行: {f['function']}")

    print(f"\n可移除的分支 ({len(dead_branches)}个):")
    for b in dead_branches:
        print(f"  - 第{b['line']}行 ({b['function']}): {b['type']}")

    return filtered_funcs, dead_branches


def step6_simplify(file_path: str, dead_funcs: list, dead_branches: list) -> dict:
    """执行简化"""
    print("\n" + "="*60)
    print("Step 6: 执行代码简化")
    print("="*60)

    if not dead_funcs and not dead_branches:
        print("没有检测到可移除的死代码")
        return {'removed_count': 0, 'removed_items': []}

    from simplify import remove_dead_code

    result = remove_dead_code(
        file_path,
        dead_funcs,
        dead_branches,
        file_path  # 直接覆盖
    )

    print(f"✓ 移除了 {result['removed_count']} 个代码项")
    for item in result['removed_items']:
        name = item.get('name', '')
        print(f"  - {item['type']} at line {item.get('line', 'N/A')} {name}")

    return result


def step7_verify() -> bool:
    """验证"""
    print("\n" + "="*60)
    print("Step 7: 验证简化后的代码")
    print("="*60)

    main_script = PROJECT_ROOT / "main.py"
    cmd = [sys.executable, str(main_script)]
    returncode, stdout, stderr = run_command(cmd)

    if returncode == 0:
        print("✓ 程序运行正常")
        return True
    else:
        print(f"✗ 程序运行失败 (返回码: {returncode})")
        print(f"错误: {stderr}")
        return False


def cleanup(log_file: str = None):
    """清理临时文件"""
    temp_files = [
        PROJECT_ROOT / ".deep_simplify_logs.txt",
        PROJECT_ROOT / ".deep_simplify_inst.txt",
    ]
    for f in temp_files:
        if f.exists():
            f.unlink()


def restore(file_path: str, backup_path: str):
    """从备份恢复"""
    print(f"\n从备份恢复: {backup_path} -> {file_path}")
    shutil.copy2(backup_path, file_path)


def main():
    if len(sys.argv) < 2:
        print("Usage: runner.py <file_path>")
        print("\n深度简化代码 - 通过运行时分析识别并移除死代码")
        sys.exit(1)

    file_path = sys.argv[1]
    backup_path = None

    try:
        # Step 1: 验证
        if not step1_validate(file_path):
            sys.exit(1)

        # Step 2: 插桩
        result = step2_instrument(file_path)
        if result is None:
            sys.exit(1)
        backup_path, inst_count = result

        if inst_count == 0:
            print("没有可插桩的代码点，退出")
            sys.exit(0)

        # Step 3: 运行主程序
        log_file = step3_run_main()
        if not log_file:
            print("运行主程序失败，恢复原始文件")
            restore(file_path, backup_path)
            sys.exit(1)

        # Step 4: 分析
        analysis = step4_analyze(file_path, log_file)

        # Step 5: 确定死代码
        dead_funcs, dead_branches = step5_identify_dead_code(analysis)

        # Step 6: 简化
        result = step6_simplify(file_path, dead_funcs, dead_branches)

        # Step 7: 验证
        if result['removed_count'] > 0:
            if not step7_verify():
                print("\n验证失败，是否恢复原始文件?")
                print("运行: python scripts/simplify.py restore")
                sys.exit(1)

        print("\n" + "="*60)
        print("代码简化完成!")
        print("="*60)
        print(f"原始备份: {backup_path}")

    except KeyboardInterrupt:
        print("\n\n用户中断")
        if backup_path:
            restore(file_path, backup_path)
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        if backup_path:
            restore(file_path, backup_path)
    finally:
        cleanup()


if __name__ == "__main__":
    main()
