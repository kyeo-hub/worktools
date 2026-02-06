"""
插件打包脚本
将插件打包成独立的 .zip 文件
"""

import os
import zipfile
import json

# 插件列表
PLUGINS = [
    {
        "id": "text_processor",
        "name": "文本处理工具",
        "description": "提供常用文本处理功能，包括文本格式化、编码转换、正则表达式匹配等",
        "version": "1.0.0",
        "author": "WorkTools Team",
        "category": "其他",
        "file": "plugin1.py"
    },
    {
        "id": "file_manager",
        "name": "文件管理器",
        "description": "增强的文件管理和操作工具，支持批量重命名、搜索、属性查看等",
        "version": "1.0.0",
        "author": "WorkTools Team",
        "category": "系统工具",
        "file": "plugin2.py"
    },
    {
        "id": "system_tools",
        "name": "系统工具",
        "description": "常用系统工具集合，包括进程管理、系统信息查看等",
        "version": "1.0.0",
        "author": "WorkTools Team",
        "category": "系统工具",
        "file": "plugin3.py"
    },
    {
        "id": "monthly_summary",
        "name": "月汇总工具",
        "description": "运输数据汇总和分析工具，自动识别车牌号并判断运输方式",
        "version": "1.0.0",
        "author": "WorkTools Team",
        "category": "数据工具",
        "file": "monthly_summary.py",
        "dependencies": ["pandas>=1.3.0", "openpyxl>=3.0.0"]
    },
    {
        "id": "excel_merger",
        "name": "Excel合并工具",
        "description": "用于处理具有多层级结构的Excel表格合并，支持多文件合并和单文件多工作表合并",
        "version": "1.0.0",
        "author": "WorkTools Team",
        "category": "数据工具",
        "file": "excel_merger.py",
        "dependencies": ["pandas>=1.3.0", "openpyxl>=3.0.0"]
    },
    {
        "id": "excel_deduplication",
        "name": "Excel去重工具",
        "description": "用于Excel表格数据的去重处理，支持全行匹配或指定列去重",
        "version": "1.0.0",
        "author": "WorkTools Team",
        "category": "数据工具",
        "file": "excel_deduplication.py",
        "dependencies": ["pandas>=1.3.0", "openpyxl>=3.0.0"]
    },
    {
        "id": "image_watermark",
        "name": "图片水印工具",
        "description": "为图片添加水印的工具，支持文字水印和图片水印",
        "version": "1.0.0",
        "author": "WorkTools Team",
        "category": "图片工具",
        "file": "image_watermark.py",
        "dependencies": ["Pillow>=9.0.0"]
    }
]

# 基础路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PLUGINS_DIR = os.path.join(BASE_DIR, "worktools", "plugins")
OUTPUT_DIR = os.path.join(BASE_DIR, "plugin_packages")

# 服务器配置
SERVER_BASE_URL = "https://tools.kyeo.top/plugins"

def build_plugin(plugin_info):
    """打包单个插件"""
    plugin_id = plugin_info["id"]
    file_name = plugin_info["file"]
    plugin_file = os.path.join(PLUGINS_DIR, file_name)
    
    # 创建输出目录
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    
    # 压缩文件名
    zip_file = os.path.join(OUTPUT_DIR, f"{plugin_id}.zip")
    
    # 打包插件
    with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(plugin_file, file_name)
    
    # 获取文件大小
    file_size = os.path.getsize(zip_file)
    
    print(f"[OK] {plugin_id}.zip ({file_size} bytes)")
    
    return file_size

def create_plugins_json():
    """创建插件仓库的 plugins.json 文件"""
    plugins_data = []
    
    for plugin_info in PLUGINS:
        # 打包插件
        file_size = build_plugin(plugin_info)
        
        # 构建插件数据
        plugin_data = {
            "id": plugin_info["id"],
            "name": plugin_info["name"],
            "description": plugin_info["description"],
            "version": plugin_info["version"],
            "author": plugin_info["author"],
            "category": plugin_info["category"],
            "url": f"{SERVER_BASE_URL}/{plugin_info['id']}.zip",
            "dependencies": plugin_info.get("dependencies", []),
            "icon": f"{SERVER_BASE_URL}/icons/{plugin_info['id']}.png",
            "file_size": file_size,
            "download_count": 0,
            "rating": 4.5,
            "release_date": "2025-12-11",
            "min_app_version": "1.1.0"
        }
        
        plugins_data.append(plugin_data)
    
    # 创建 plugins.json
    plugins_json_file = os.path.join(OUTPUT_DIR, "plugins.json")
    with open(plugins_json_file, 'w', encoding='utf-8') as f:
        json.dump({
            "version": "1.0",
            "update_url": f"{SERVER_BASE_URL}/versions.json",
            "plugins": plugins_data
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n[OK] plugins.json 已创建")
    
    # 计算总大小
    total_size = sum(os.path.getsize(os.path.join(OUTPUT_DIR, f"{p['id']}.zip")) for p in PLUGINS)
    print(f"\n插件包总大小: {total_size:,} bytes ({total_size / 1024:.2f} KB)")
    
    return plugins_json_file

if __name__ == "__main__":
    print("=" * 60)
    print("插件打包工具")
    print("=" * 60)
    print()
    
    # 创建插件仓库
    plugins_json_file = create_plugins_json()
    
    print()
    print("=" * 60)
    print("打包完成！")
    print("=" * 60)
    print(f"\n输出目录: {OUTPUT_DIR}")
    print(f"插件仓库文件: {plugins_json_file}")
    print(f"\n下一步:")
    print("1. 将 plugin_packages 目录中的所有文件上传到服务器")
    print("2. 将文件上传到 https://tools.kyeo.top/plugins/")
    print("3. 使用插件管理器测试下载和安装")
