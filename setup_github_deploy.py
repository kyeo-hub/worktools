# -*- coding: utf-8 -*-

"""
GitHub自动部署设置脚本（简化版）
使用自定义域名 tools.kyeo.top
推送tag自动发布新版本
"""

import os
import sys

print("GitHub自动部署设置向导")
print("=" * 50)

# 检查必要文件
if not os.path.exists('.git'):
    print("[错误] 当前目录不是Git仓库")
    print("请先运行: git init")
    sys.exit(1)

print("""
配置信息:
   域名: tools.kyeo.top
   自动版本: 从git tag读取
   触发条件: 推送 v* 格式的tag

使用流程:
   1. 修改代码
   2. git add . && git commit -m "xxx"
   3. git tag v1.0.1
   4. git push origin v1.0.1
   5. 自动部署到 tools.kyeo.top
""")

print("\n" + "=" * 50)
print("检查必要文件...")

# 检查GitHub Actions配置
if not os.path.exists('.github/workflows/deploy.yml'):
    print("❌ GitHub Actions工作流不存在!")
    sys.exit(1)

print("[OK] GitHub Actions工作流已配置")

# 检查版本文件
if not os.path.exists('version.json'):
    # 创建初始版本文件
    import json
    version_config = {
        "version": "1.0.0",
        "app_name": "WorkTools",
        "update_url": "https://tools.kyeo.top/updates/version.json",
        "download_url": "https://tools.kyeo.top/updates/"
    }
    with open('version.json', 'w', encoding='utf-8') as f:
        json.dump(version_config, f, indent=2)
    print("[OK] 创建 version.json")

print("[OK] version.json 存在")

# 创建CNAME文件（用于GitHub Pages自定义域名）
with open('CNAME', 'w') as f:
    f.write('tools.kyeo.top')
print("[OK] 创建 CNAME 文件 (tools.kyeo.top)")

print("\n" + "=" * 50)
print("接下来需要完成的步骤:\n")

print("[1] 创建GitHub仓库:")
print("   访问 https://github.com/new")
print("   创建仓库（不要初始化README）\n")

print("[2] 推送代码到GitHub:")
print("""
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/你的用户名/仓库名.git
   git push -u origin main
""")

print("[3] 启用GitHub Pages:")
print("   访问仓库 Settings → Pages")
print("   Source 选择 GitHub Actions\n")

print("[4] 配置自定义域名:")
print("   Settings → Pages → Custom domain")
print("   输入: tools.kyeo.top")
print("   勾选 Enforce HTTPS\n")

print("[5] 配置DNS解析:")
print("   在你的域名服务商添加CNAME记录:")
print("   主机记录: tools")
print("   记录值: 你的用户名.github.io")
print("   例如: kyeo.github.io\n")

print("[6] 发布新版本:")
print("""
   # 本地打tag并推送，自动触发部署
   git tag v1.0.0
   git push origin v1.0.0
   
   # 或者删除旧tag重新发布
   git tag -d v1.0.0
   git push origin :refs/tags/v1.0.0
   git tag v1.0.0
   git push origin v1.0.0
""")

print("=" * 50)
input("\n按回车键继续...")

print("\n设置完成!")
print("部署后访问地址: https://tools.kyeo.top/")
print("版本检查地址: https://tools.kyeo.top/updates/version.json")
print("\n提示: 只需推送tag即可自动发布，无需手动修改任何文件！")
