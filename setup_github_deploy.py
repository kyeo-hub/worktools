# -*- coding: utf-8 -*-

"""
GitHub自动部署设置脚本
一键配置GitHub Actions自动部署
"""

import os
import sys
import json

print("🚀 GitHub自动部署设置向导")
print("=" * 50)

# 检查必要文件
if not os.path.exists('.git'):
    print("❌ 错误: 当前目录不是Git仓库")
    print("请先运行: git init")
    sys.exit(1)

print("\n1️⃣ 配置版本信息")
print("-" * 50)

# 读取当前版本
current_version = "1.0.0"
if os.path.exists('version.json'):
    with open('version.json', 'r') as f:
        info = json.load(f)
        current_version = info.get('version', '1.0.0')

version = input(f"请输入版本号 [{current_version}]: ").strip() or current_version

# 更新版本文件
version_config = {
    "version": version,
    "app_name": "WorkTools",
    "update_url": "",  # 将自动填充
    "download_url": ""
}

with open('version.json', 'w', encoding='utf-8') as f:
    json.dump(version_config, f, indent=2)

print(f"✅ 版本号已设置为: {version}")

print("\n2️⃣ 配置服务器信息")
print("-" * 50)

print("""
请选择部署方式:
[1] GitHub Pages (推荐，免费，全球访问)
[2] Gitee Pages (国内访问快)
[3] 自定义服务器
""")

choice = input("请选择 [1]: ").strip() or "1"

if choice == "1":
    # GitHub Pages
    username = input("请输入GitHub用户名: ").strip()
    repo = input("请输入仓库名 [worktools]: ").strip() or "worktools"
    
    pages_url = f"https://{username}.github.io/{repo}"
    
    version_config["update_url"] = f"{pages_url}/updates/version.json"
    version_config["download_url"] = f"{pages_url}/updates/"
    
    # 更新服务器版本文件
    server_config = {
        "version": version,
        "app_name": "WorkTools",
        "changelog": ["初始版本"],
        "download_url": f"{pages_url}/updates/WorkTools_v{version}.zip",
        "mandatory": False,
        "published_at": "2024-02-05",
        "min_version": "1.0.0"
    }
    
    with open('server/version.json', 'w', encoding='utf-8') as f:
        json.dump(server_config, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ GitHub Pages 地址: {pages_url}")
    print(f"✅ 版本检查URL: {version_config['update_url']}")
    
elif choice == "2":
    # Gitee Pages
    username = input("请输入Gitee用户名: ").strip()
    repo = input("请输入仓库名 [worktools]: ").strip() or "worktools"
    
    pages_url = f"https://{username}.gitee.io/{repo}"
    
    version_config["update_url"] = f"{pages_url}/updates/version.json"
    version_config["download_url"] = f"{pages_url}/updates/"
    
    server_config = {
        "version": version,
        "app_name": "WorkTools",
        "changelog": ["初始版本"],
        "download_url": f"{pages_url}/updates/WorkTools_v{version}.zip",
        "mandatory": False,
        "published_at": "2024-02-05",
        "min_version": "1.0.0"
    }
    
    with open('server/version.json', 'w', encoding='utf-8') as f:
        json.dump(server_config, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Gitee Pages 地址: {pages_url}")
    
else:
    # 自定义服务器
    url = input("请输入服务器基础URL (如: https://your-server.com/updates): ").strip()
    
    version_config["update_url"] = f"{url}/version.json"
    version_config["download_url"] = f"{url}/"

# 保存配置
with open('version.json', 'w', encoding='utf-8') as f:
    json.dump(version_config, f, indent=2)

print(f"✅ 配置已保存到 version.json")

print("\n3️⃣ GitHub Actions配置")
print("-" * 50)

if os.path.exists('.github/workflows/deploy.yml'):
    print("✅ GitHub Actions工作流已配置")
else:
    print("❌ GitHub Actions工作流文件不存在")
    sys.exit(1)

print("""
📋 接下来需要完成的步骤:

1. 创建GitHub仓库:
   - 访问 https://github.com/new
   - 创建仓库（不要初始化README）

2. 推送代码到GitHub:
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/用户名/仓库名.git
   git push -u origin main

3. 启用GitHub Pages:
   - 访问仓库 Settings -> Pages
   - Source 选择 "GitHub Actions"

4. 发布新版本:
   - 每次推送代码会自动部署
   - 或者创建tag: git tag v1.0.0 && git push origin v1.0.0

""")

input("按回车键继续...")
print("\n✨ 设置完成!")
print(f"🌐 部署后访问地址: {version_config['update_url'].replace('/version.json', '')}")
