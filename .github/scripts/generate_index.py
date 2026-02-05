# -*- coding: utf-8 -*-
"""
生成更新服务器首页
"""

import os
import json
import glob
from datetime import datetime

def generate_index():
    """生成HTML索引页面"""
    
    # 读取版本信息
    version_file = 'server/version.json'
    if os.path.exists(version_file):
        with open(version_file, 'r', encoding='utf-8') as f:
            version_info = json.load(f)
    else:
        version_info = {
            "version": "1.0.0",
            "app_name": "WorkTools",
            "changelog": [],
            "published_at": datetime.now().strftime("%Y-%m-%d")
        }
    
    # 查找更新包
    zip_files = glob.glob('WorkTools_*.zip')
    download_link = ""
    if zip_files:
        zip_name = os.path.basename(zip_files[0])
        download_link = f'<a href="updates/{zip_name}" class="btn">下载最新版本</a>'
    
    # 生成HTML
    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{version_info['app_name']} - 更新服务器</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }}
        .container {{
            background: white;
            border-radius: 20px;
            padding: 40px;
            max-width: 600px;
            width: 100%;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }}
        h1 {{
            color: #333;
            margin-bottom: 10px;
            font-size: 2em;
        }}
        .version {{
            color: #667eea;
            font-size: 1.2em;
            font-weight: bold;
            margin-bottom: 20px;
        }}
        .info {{
            color: #666;
            margin-bottom: 30px;
            line-height: 1.6;
        }}
        .changelog {{
            background: #f8f9fa;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 30px;
        }}
        .changelog h3 {{
            color: #333;
            margin-bottom: 15px;
            font-size: 1.1em;
        }}
        .changelog ul {{
            list-style: none;
            padding-left: 0;
        }}
        .changelog li {{
            padding: 8px 0;
            padding-left: 25px;
            position: relative;
            color: #555;
        }}
        .changelog li:before {{
            content: "✓";
            position: absolute;
            left: 0;
            color: #28a745;
            font-weight: bold;
        }}
        .btn {{
            display: inline-block;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 40px;
            border-radius: 30px;
            text-decoration: none;
            font-weight: bold;
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        .btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.4);
        }}
        .footer {{
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #eee;
            color: #999;
            font-size: 0.9em;
        }}
        .api-info {{
            background: #e3f2fd;
            border-left: 4px solid #2196f3;
            padding: 15px;
            margin-top: 20px;
            border-radius: 5px;
        }}
        .api-info code {{
            background: rgba(0,0,0,0.1);
            padding: 2px 6px;
            border-radius: 3px;
            font-family: monospace;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🛠️ {version_info['app_name']}</h1>
        <div class="version">最新版本: {version_info['version']}</div>
        <div class="info">
            发布日期: {version_info.get('published_at', '未知')}
        </div>
        
        <div class="changelog">
            <h3>📝 更新日志</h3>
            <ul>
                {''.join(f'<li>{item}</li>' for item in version_info.get('changelog', ['无更新说明']))}
            </ul>
        </div>
        
        <center>
            {download_link if download_link else '<p style="color: #999;">暂无下载包</p>'}
        </center>
        
        <div class="api-info">
            <strong>📡 API 端点</strong><br>
            版本检查: <code>updates/version.json</code>
        </div>
        
        <div class="footer">
            © 2024 {version_info['app_name']} - 自动更新服务器
        </div>
    </div>
</body>
</html>'''
    
    # 写入文件
    with open('_site/index.html', 'w', encoding='utf-8') as f:
        f.write(html)
    
    print("[OK] Index page generated: _site/index.html")

if __name__ == '__main__':
    generate_index()
