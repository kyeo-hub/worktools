# -*- coding: utf-8 -*-

"""
打包脚本
使用PyInstaller打包应用程序
"""

import os
import sys
import shutil
import json

# 版本信息 - 优先从环境变量读取，用于CI/CD
import os
VERSION = os.environ.get('VERSION', '1.0.0')
APP_NAME = "WorkTools"

def clean_build():
    """清理构建目录"""
    dirs_to_remove = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_remove:
        if os.path.exists(dir_name):
            print(f"[Clean] Removing {dir_name}...")
            shutil.rmtree(dir_name)
    
    # 删除.spec文件
    for file in os.listdir('.'):
        if file.endswith('.spec'):
            print(f"[Clean] Removing {file}...")
            os.remove(file)

def write_version_file():
    """写入版本信息文件"""
    # 读取现有的 version.json，保留 changelog 等信息
    if os.path.exists('version.json'):
        try:
            with open('version.json', 'r', encoding='utf-8') as f:
                version_info = json.load(f)
        except:
            version_info = {}
    else:
        version_info = {}

    # 更新版本和 URL，保留其他字段（如 changelog）
    version_info["version"] = VERSION
    version_info["app_name"] = APP_NAME
    version_info["update_url"] = "https://tools.kyeo.top/updates/version.json"
    version_info["download_url"] = f"https://tools.kyeo.top/updates/WorkTools_v{VERSION}.zip"

    with open('version.json', 'w', encoding='utf-8') as f:
        json.dump(version_info, f, indent=2, ensure_ascii=False)

    print(f"[Version] Written: {VERSION}")

def build():
    """执行打包"""
    print("[Build] Starting build...")
    
    # 确保版本文件存在
    write_version_file()
    
    # PyInstaller参数
    args = [
        'main.py',
        '--name=%s' % APP_NAME,
        '--windowed',
        '--onefile',  # 打包成单个exe
        '--clean',
        '--noconfirm',
        # 图标
        '--icon=worktools/resources/icons/app.ico' if os.path.exists('worktools/resources/icons/app.ico') else '',
        # 添加数据文件 (Windows使用; Linux/Mac使用:)
        # 排除 plugins 目录的具体插件文件，只保留 plugin_manager_tool 和 base_plugin
        # 这样插件可以按需下载和安装
        '--add-data=worktools/base_plugin.py;worktools' if sys.platform == 'win32' else '--add-data=worktools/base_plugin.py:worktools',
        '--add-data=worktools/plugin_manager.py;worktools' if sys.platform == 'win32' else '--add-data=worktools/plugin_manager.py:worktools',
        '--add-data=worktools/plugins/__init__.py;worktools/plugins' if sys.platform == 'win32' else '--add-data=worktools/plugins/__init__.py:worktools/plugins',
        '--add-data=worktools/plugins/plugin_manager_tool.py;worktools/plugins' if sys.platform == 'win32' else '--add-data=worktools/plugins/plugin_manager_tool.py:worktools/plugins',
        '--add-data=worktools/plugins/local_plugins.json;worktools/plugins' if sys.platform == 'win32' else '--add-data=worktools/plugins/local_plugins.json:worktools/plugins',
        '--add-data=worktools/api_settings_dialog.py;worktools' if sys.platform == 'win32' else '--add-data=worktools/api_settings_dialog.py:worktools',
        '--add-data=worktools/updater.py;worktools' if sys.platform == 'win32' else '--add-data=worktools/updater.py:worktools',
        '--add-data=version.json;.' if sys.platform == 'win32' else '--add-data=version.json:.',
        '--add-data=worktools/navigation.py;worktools' if sys.platform == 'win32' else '--add-data=worktools/navigation.py:worktools',
        '--add-data=worktools/workspace.py;worktools' if sys.platform == 'win32' else '--add-data=worktools/workspace.py:worktools',
        '--add-data=worktools/main_window.py;worktools' if sys.platform == 'win32' else '--add-data=worktools/main_window.py:worktools',
        '--add-data=worktools/app.py;worktools' if sys.platform == 'win32' else '--add-data=worktools/app.py:worktools',
        # 添加resources目录
        '--add-data=worktools/resources;worktools/resources' if sys.platform == 'win32' else '--add-data=worktools/resources:worktools/resources',
        # 隐藏导入
        '--hidden-import=PyQt5.sip',
        '--hidden-import=PyQt5.QtCore',
        '--hidden-import=PyQt5.QtGui',
        '--hidden-import=PyQt5.QtWidgets',
        '--hidden-import=PIL',
        '--hidden-import=PIL.Image',
        '--hidden-import=PIL.ImageDraw',
        '--hidden-import=PIL.ImageFont',
        '--hidden-import=pandas',
        '--hidden-import=pandas.core',
        '--hidden-import=pandas.io',
        '--hidden-import=numpy',
        '--hidden-import=numpy.core',
        '--hidden-import=numpy.core.multiarray',
        '--hidden-import=openpyxl',
        '--hidden-import=psutil',
        '--hidden-import=pyqtgraph',
        '--hidden-import=requests',
        # 插件相关导入（不包含具体插件，只包含框架）
        '--hidden-import=worktools.plugin_manager',
        '--hidden-import=worktools.plugins.plugin_manager_tool',
        '--hidden-import=worktools.base_plugin',
        # 排除不需要的库（减少打包体积）
        '--exclude-module=matplotlib',
        '--exclude-module=pytest',
        '--exclude-module=PyQt6',
        '--exclude-module=PyQt6-Qt6',
    ]
    
    # 过滤空参数
    args = [arg for arg in args if arg]
    
    # 执行打包
    import PyInstaller.__main__
    PyInstaller.__main__.run(args)
    
    print("[Build] Build completed!")
    print(f"[Build] Output: dist/{APP_NAME}.exe")

def create_update_package():
    """创建更新包"""
    import zipfile

    print("[Package] Creating update package...")

    # 创建更新目录
    update_dir = 'update_package'
    if os.path.exists(update_dir):
        shutil.rmtree(update_dir)
    os.makedirs(update_dir)

    # 复制主程序
    exe_path = f'dist/{APP_NAME}.exe'
    if os.path.exists(exe_path):
        shutil.copy2(exe_path, update_dir)

    # 复制版本文件
    shutil.copy2('version.json', update_dir)

    # 创建ZIP包
    zip_name = f'{APP_NAME}_v{VERSION}.zip'
    with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(update_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, update_dir)
                zf.write(file_path, arcname)

    print(f"[Package] Created: {zip_name}")

    # 清理临时目录
    shutil.rmtree(update_dir)

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='打包工具')
    parser.add_argument('command', choices=['clean', 'build', 'update'], 
                       help='命令: clean=清理, build=打包, update=创建更新包')
    
    args = parser.parse_args()
    
    if args.command == 'clean':
        clean_build()
    elif args.command == 'build':
        clean_build()
        build()
    elif args.command == 'update':
        create_update_package()
