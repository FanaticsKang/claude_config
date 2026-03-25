#!/usr/bin/env python3
"""
gen_plugin_commands.py: 读取 remote_config.json 并生成 Claude 插件安装命令
"""

import json
import subprocess
import sys
from pathlib import Path

# 颜色定义
class Colors:
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    CYAN = '\033[0;36m'
    BOLD = '\033[1m'
    NC = '\033[0m'

    @staticmethod
    def enable():
        if sys.platform == 'win32':
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)

Colors.enable()

def get_script_dir():
    return Path(__file__).parent.resolve()

def load_config():
    """加载配置文件"""
    config_file = get_script_dir() / 'remote_config.json'
    if not config_file.exists():
        print(f"{Colors.RED}错误: 配置文件不存在: {config_file}{Colors.NC}")
        sys.exit(1)
    with open(config_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_all_official_plugins():
    """通过 GitHub API 获取所有官方插件列表"""
    try:
        # 使用 GitHub API 获取 plugins 目录
        result = subprocess.run(
            ['curl', '-s', 'https://api.github.com/repos/anthropics/claude-plugins-official/contents/plugins'],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            if isinstance(data, list):
                return [item['name'] for item in data if item['type'] == 'dir']
    except Exception as e:
        print(f"{Colors.YELLOW}警告: 无法获取官方插件列表: {e}{Colors.NC}")
        print(f"{Colors.YELLOW}将使用预定义的插件列表{Colors.NC}")

    # 预定义的官方插件列表（作为后备）
    return [
        'agent-sdk-dev',
        'clangd-lsp',
        'claude-code-setup',
        'claude-md-management',
        'code-review',
        'code-simplifier',
        'commit-commands',
        'csharp-lsp',
        'example-plugin',
        'explanatory-output-style',
        'feature-dev',
        'frontend-design',
        'gopls-lsp',
        'hookify',
        'jdtls-lsp',
        'kotlin-lsp',
        'learning-output-style',
        'lua-lsp',
        'math-olympiad',
        'mcp-server-dev',
        'php-lsp',
        'playground',
        'plugin-dev',
        'pr-review-toolkit'
    ]

def generate_commands(config):
    """生成 Claude 插件安装命令"""
    commands = []
    info = []

    if config.get('version') != '3.0':
        print(f"{Colors.YELLOW}警告: 配置版本不是 3.0，可能不兼容{Colors.NC}")

    for plugin in config.get('plugins', []):
        plugin_type = plugin.get('type')
        name = plugin.get('name')

        if plugin_type == 'official':
            # 官方插件 - 生成 /plugin install 命令
            plugins_list = plugin.get('plugins', [])
            if not plugins_list:
                plugins_list = get_all_official_plugins()
                info.append(f"{Colors.CYAN}官方插件 (全部 {len(plugins_list)} 个):{Colors.NC}")
            else:
                info.append(f"{Colors.CYAN}官方插件 (选中 {len(plugins_list)} 个):{Colors.NC}")

            for p in plugins_list:
                commands.append(f"/plugin install {p}@claude-plugins-official")

        elif plugin_type == 'marketplace':
            # Marketplace 插件 - 生成 /plugin marketplace add 命令
            repo = plugin.get('repo', '')
            if repo:
                commands.append(f"/plugin marketplace add {repo}")
                info.append(f"{Colors.CYAN}Marketplace: {repo}{Colors.NC}")

    return commands, info

def main():
    print("=" * 60)
    print(f"  {Colors.BOLD}Claude 插件安装命令生成器{Colors.NC}")
    print("=" * 60)
    print()

    # 加载配置
    config = load_config()

    # 生成命令
    commands, info = generate_commands(config)

    # 显示信息
    print(f"{Colors.BOLD}配置内容:{Colors.NC}")
    for line in info:
        print(f"  {line}")
    print()

    # 显示命令
    print(f"{Colors.BOLD}生成的 Claude 命令:{Colors.NC}")
    print(f"{Colors.YELLOW}请复制以下命令到 Claude 中执行:{Colors.NC}")
    print()

    for i, cmd in enumerate(commands, 1):
        print(f"{Colors.GREEN}{i:2}.{Colors.NC} {cmd}")

    print()
    print("=" * 60)
    print(f"  {Colors.BOLD}共 {len(commands)} 条命令{Colors.NC}")
    print("=" * 60)
    print()

    # 保存到文件
    output_file = get_script_dir() / 'plugin_commands.txt'
    with open(output_file, 'w', encoding='utf-8') as f:
        for cmd in commands:
            f.write(cmd + '\n')
    print(f"{Colors.BLUE}提示: 命令已保存到: {output_file}{Colors.NC}")
    print()

if __name__ == '__main__':
    main()
