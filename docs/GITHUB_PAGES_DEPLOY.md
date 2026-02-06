# GitHub Pages 部署说明

## 部署架构

WorkTools 使用 **GitHub Pages** 作为远程服务器，域名：`tools.kyeo.top`

部署流程完全通过 **GitHub Actions** 自动化完成，无需手动上传文件。

## 自动部署流程

### 触发条件
推送以 `v` 开头的标签到 GitHub 时自动触发：
```bash
git tag v1.2.0 -m "Release v1.2.0"
git push origin v1.2.0
```

### 自动执行步骤

#### 1. 构建应用程序
- 在 Windows 环境中运行 `build.py`
- 生成 `WorkTools.exe`
- 创建更新包 `WorkTools_v1.2.0.zip`

#### 2. 打包插件
- 运行 `build_plugins.py`
- 生成 7 个插件包到 `plugin_packages/`
- 生成 `plugins.json` 配置文件

#### 3. 准备 Pages 文件
- 创建 `_site/` 目录结构：
  ```
  _site/
  ├── CNAME
  ├── index.html
  ├── updates/
  │   ├── version.json
  │   └── WorkTools_v1.2.0.zip
  └── plugins/
      ├── plugins.json
      ├── text_processor.zip
      ├── file_manager.zip
      ├── system_tools.zip
      ├── monthly_summary.zip
      ├── excel_merger.zip
      ├── excel_deduplication.zip
      └── image_watermark.zip
  ```

#### 4. 部署到 GitHub Pages
- 自动上传 `_site/` 到 `gh-pages` 分支
- 通过 Cloudflare DNS 解析到 GitHub Pages

## 访问地址

### 主站
- **网站**: https://tools.kyeo.top
- **更新检查**: https://tools.kyeo.top/updates/version.json
- **更新下载**: https://tools.kyeo.top/updates/WorkTools_v1.2.0.zip

### 插件仓库
- **插件列表**: https://tools.kyeo.top/plugins/plugins.json
- **插件下载**: https://tools.kyeo.top/plugins/{plugin_id}.zip

### Git 仓库
- **主仓库**: https://github.com/kyeo-hub/worktools
- **Pages 分支**: gh-pages
- **Actions**: https://github.com/kyeo-hub/worktools/actions

## 本地测试

### 使用本地文件测试插件管理器
```python
# 在 worktools/plugins/local_plugins.json 中使用 file:// 协议
"url": "file://d:/work-tools/plugin_packages/text_processor.zip"
```

### 切换到远程测试
```python
# 在插件管理器设置中配置远程 URL
"https://tools.kyeo.top/plugins/plugins.json"
```

## 插件包格式

每个插件包包含：
```
{plugin_id}.zip
└── {plugin_id}.py  # 插件主文件
```

### 插件信息 (plugins.json)
```json
{
  "version": "1.0",
  "plugins": [
    {
      "id": "system_tools",
      "name": "系统工具",
      "description": "常用系统工具集合",
      "version": "1.0.0",
      "author": "WorkTools Team",
      "category": "系统工具",
      "url": "https://tools.kyeo.top/plugins/system_tools.zip",
      "dependencies": [],
      "file_size": 6799
    }
  ]
}
```

## 手动部署（仅用于调试）

### 创建插件包
```bash
python build_plugins.py
```

### 本地测试
1. 启动 WorkTools
2. 打开插件管理器
3. 设置使用本地仓库：`worktools/plugins/local_plugins.json`
4. 测试安装和卸载插件

## 版本管理

### 版本号规则
- 主版本.次版本.修订版本 (如 1.2.0)
- Git 标签格式：v{version} (如 v1.2.0)

### 版本文件
- **客户端版本**: `version.json`
- **服务器版本**: `updates/version.json`
- **插件仓库**: `plugins/plugins.json`

## 域名配置

### DNS 设置
- **记录类型**: CNAME
- **记录值**: `kyeo-hub.github.io`
- **TTL**: 3600

### CNAME 文件
位于仓库根目录，内容：
```
tools.kyeo.top
```

## 故障排查

### 部署失败
1. 检查 GitHub Actions 日志
2. 确认标签格式正确 (v1.2.0)
3. 检查 `.github/workflows/deploy.yml` 语法

### 访问失败
1. 检查 DNS 解析是否正确
2. 确认 Cloudflare 配置
3. 检查 GitHub Pages 设置

### 插件下载失败
1. 检查 URL 是否正确
2. 确认插件包存在
3. 检查网络连接

## 相关文档

- **项目 README**: `README.md`
- **部署总结**: `DEPLOYMENT_SUMMARY.md`
- **版本发布**: `docs/RELEASE_v1.2.0.md`
- **插件打包**: `build_plugins.py`
- **部署流程**: `.github/workflows/deploy.yml`

---
**更新时间**: 2025-12-11
