"""
打包体积对比脚本
对比完整版和精简版的打包体积
"""

import os
import zipfile
import tempfile
import shutil

def create_minimal_app():
    """创建精简版应用目录"""
    temp_dir = tempfile.mkdtemp()
    app_dir = os.path.join(temp_dir, "WorkTools_Minimal")
    
    # 创建目录结构
    os.makedirs(os.path.join(app_dir, "worktools", "plugins"))
    os.makedirs(os.path.join(app_dir, "worktools", "resources", "icons"))
    
    # 复制主程序文件
    files_to_copy = [
        ("main.py", ""),
        ("requirements.txt", ""),
        ("version.json", ""),
        ("worktools/__init__.py", "worktools/"),
        ("worktools/app.py", "worktools/"),
        ("worktools/main_window.py", "worktools/"),
        ("worktools/navigation.py", "worktools/"),
        ("worktools/workspace.py", "worktools/"),
        ("worktools/plugin_manager.py", "worktools/"),
        ("worktools/base_plugin.py", "worktools/"),
        ("worktools/updater.py", "worktools/"),
        ("worktools/plugins/__init__.py", "worktools/plugins/"),
        ("worktools/plugins/plugin_manager_tool.py", "worktools/plugins/"),
        ("worktools/resources/icons/app.png", "worktools/resources/icons/"),
    ]
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    for src_file, dest_dir in files_to_copy:
        src_path = os.path.join(base_dir, src_file)
        dest_path = os.path.join(app_dir, dest_dir, os.path.basename(src_file))
        
        if os.path.exists(src_path):
            shutil.copy2(src_path, dest_path)
            print(f"[OK] 复制: {src_file}")
        else:
            print(f"[SKIP] 文件不存在: {src_file}")
    
    return app_dir

def create_full_app():
    """创建完整版应用目录"""
    temp_dir = tempfile.mkdtemp()
    app_dir = os.path.join(temp_dir, "WorkTools_Full")
    
    # 复制整个 worktools 目录
    base_dir = os.path.dirname(os.path.abspath(__file__))
    src_worktools = os.path.join(base_dir, "worktools")
    dest_worktools = os.path.join(app_dir, "worktools")
    
    # 只复制必要的文件
    for root, dirs, files in os.walk(src_worktools):
        # 排除备份目录和测试文件
        if 'builtin_backup' in root or 'local_plugins.json' in root:
            continue
        
        for file in files:
            if file.endswith('.py'):
                src_file = os.path.join(root, file)
                rel_path = os.path.relpath(src_file, src_worktools)
                dest_file = os.path.join(dest_worktools, rel_path)
                
                os.makedirs(os.path.dirname(dest_file), exist_ok=True)
                shutil.copy2(src_file, dest_file)
                print(f"[OK] 复制: worktools/{rel_path}")
    
    # 复制其他必要文件
    files_to_copy = [
        "main.py",
        "requirements.txt",
        "version.json"
    ]
    
    for file in files_to_copy:
        src_path = os.path.join(base_dir, file)
        dest_path = os.path.join(app_dir, file)
        if os.path.exists(src_path):
            shutil.copy2(src_path, dest_path)
            print(f"[OK] 复制: {file}")
    
    return app_dir

def calculate_directory_size(directory):
    """计算目录大小"""
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(directory):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            total_size += os.path.getsize(filepath)
    return total_size

def create_zip_package(directory, zip_filename):
    """创建 zip 包"""
    zip_path = os.path.join(os.path.dirname(directory), zip_filename)
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, os.path.dirname(directory))
                zipf.write(file_path, arcname)
    
    return zip_path

def main():
    print("=" * 70)
    print("打包体积对比工具")
    print("=" * 70)
    print()
    
    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    
    try:
        # 创建精简版
        print("创建精简版应用...")
        print("-" * 70)
        minimal_dir = create_minimal_app()
        print()
        
        # 创建完整版
        print("创建完整版应用...")
        print("-" * 70)
        full_dir = create_full_app()
        print()
        
        # 计算目录大小
        minimal_size = calculate_directory_size(minimal_dir)
        full_size = calculate_directory_size(full_dir)
        
        # 创建 zip 包
        print("创建 ZIP 包...")
        print("-" * 70)
        minimal_zip = create_zip_package(minimal_dir, "WorkTools_Minimal.zip")
        full_zip = create_zip_package(full_dir, "WorkTools_Full.zip")
        
        minimal_zip_size = os.path.getsize(minimal_zip)
        full_zip_size = os.path.getsize(full_zip)
        
        # 显示结果
        print()
        print("=" * 70)
        print("对比结果")
        print("=" * 70)
        print()
        print(f"目录大小对比:")
        print(f"  精简版: {minimal_size:,} bytes ({minimal_size/1024:.2f} KB)")
        print(f"  完整版: {full_size:,} bytes ({full_size/1024:.2f} KB)")
        print(f"  减少: {full_size - minimal_size:,} bytes ({((full_size - minimal_size)/full_size)*100:.1f}%)")
        print()
        print(f"ZIP 包大小对比:")
        print(f"  精简版: {minimal_zip_size:,} bytes ({minimal_zip_size/1024:.2f} KB)")
        print(f"  完整版: {full_zip_size:,} bytes ({full_zip_size/1024:.2f} KB)")
        print(f"  减少: {full_zip_size - minimal_zip_size:,} bytes ({((full_zip_size - minimal_zip_size)/full_zip_size)*100:.1f}%)")
        print()
        print(f"ZIP 包位置:")
        print(f"  精简版: {minimal_zip}")
        print(f"  完整版: {full_zip}")
        print()
        
        # 复制到项目目录方便查看
        output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "package_comparison")
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        shutil.copy2(minimal_zip, os.path.join(output_dir, "WorkTools_Minimal.zip"))
        shutil.copy2(full_zip, os.path.join(output_dir, "WorkTools_Full.zip"))
        
        print(f"ZIP 包已复制到: {output_dir}")
        print()
        
    finally:
        # 清理临时目录
        shutil.rmtree(temp_dir)
    
    print("=" * 70)
    print("对比完成！")
    print("=" * 70)

if __name__ == "__main__":
    main()
