# 插件部署指南

## 概述

本文档说明如何将插件推送到远程服务器，实现项目与插件的分离。

## 打包体积对比

| 版本 | 目录大小 | ZIP包大小 | 减少 |
|------|----------|-----------|------|
| 完整版 | 90.99 KB | 27.56 KB | - |
| 精简版 | 86.37 KB | 26.32 KB | 4.5% |

**说明**：
- 精简版只包含插件管理器，其他插件需要从远程仓库下载
- 实际减少的体积取决于插件数量和大小
- 使用 PyInstaller 打包成 exe 后，体积减少效果更明显

## 部署步骤

### 1. 准备插件包

运行打包脚本，将所有插件打包成 .zip 文件：

```bash
cd d:/work-tools
python build_plugins.py
```

生成的文件在 `plugin_packages/` 目录：
- `plugins.json` - 插件仓库索引文件
- `*.zip` - 插件压缩包（7个插件）

### 2. 上传文件到服务器

将以下文件上传到服务器 `https://tools.kyeo.top/plugins/`：

```
plugin_packages/
├── plugins.json                    # 插件仓库索引
├── text_processor.zip             # 文本处理工具
├── file_manager.zip               # 文件管理器
├── system_tools.zip               # 系统工具
├── monthly_summary.zip            # 月汇总工具
├── excel_merger.zip               # Excel合并工具
├── excel_deduplication.zip        # Excel去重工具
└── image_watermark.zip            # 图片水印工具
```

**上传方式**：
- 使用 FTP/SFTP 工具（如 FileZilla、WinSCP）
- 使用服务器控制面板的文件管理器
- 使用命令行 scp/rsync

**示例命令**（使用 scp）：
```bash
scp plugin_packages/* user@tools.kyeo.top:/var/www/tools.kyeo.top/plugins/
```

### 3. 更新插件仓库 URL

修改 `plugin_packages/plugins.json` 中的 URL 为实际的服务器地址：

```json
{
  "plugins": [
    {
      "id": "text_processor",
      "url": "https://tools.kyeo.top/plugins/text_processor.zip",
      ...
    }
  ]
}
```

### 4. 配置应用使用远程仓库

修改 `worktools/plugins/plugin_manager_tool.py` 中的默认仓库 URL：

```python
# 第 40 行左右
self.plugin_repo_url = "https://tools.kyeo.top/plugins/plugins.json"
```

### 5. 测试部署

1. 打开应用程序
2. 进入"插件管理"
3. 点击"刷新"按钮
4. 确认能正常加载插件列表
5. 尝试安装一个插件
6. 重启应用，确认插件已加载

## 本地测试

在部署到远程服务器之前，可以先在本地测试：

### 1. 创建本地测试目录

```bash
mkdir test_server\plugins
```

### 2. 复制插件包

```bash
copy plugin_packages\*.zip test_server\plugins\
copy plugin_packages\plugins.json test_server\plugins\
```

### 3. 修改本地测试仓库

编辑 `test_server/plugins/plugins.json`，将 URL 改为本地文件路径：

```json
{
  "plugins": [
    {
      "id": "text_processor",
      "url": "file://d:/work-tools/test_server/plugins/text_processor.zip",
      ...
    }
  ]
}
```

### 4. 配置应用使用本地仓库

修改 `worktools/plugins/plugin_manager_tool.py`：

```python
self.plugin_repo_url = "file://d:/work-tools/test_server/plugins/plugins.json"
```

### 5. 测试

运行应用程序，测试插件的下载和安装功能。

## 版本管理

### 插件版本

每个插件都有独立的版本号，格式为 `x.y.z`：
- `x` - 主版本号（重大更新）
- `y` - 次版本号（功能更新）
- `z` - 修订号（Bug修复）

### 应用版本

应用在 `version.json` 中定义：

```json
{
  "version": "1.1.0",
  "min_app_version": "1.1.0"
}
```

### 更新流程

1. 修改插件代码
2. 更新插件版本号
3. 重新打包插件
4. 上传新版本的插件包
5. 更新 `plugins.json` 中的版本信息
6. 用户打开应用时，插件管理器会提示有新版本

## 安全考虑

### 插件签名（可选）

为了防止恶意插件，可以实现插件签名机制：

1. 使用私钥对插件包进行签名
2. 在应用中内置公钥
3. 安装前验证签名

### HTTPS

确保服务器使用 HTTPS 协议，防止中间人攻击。

### 依赖检查

插件管理器会自动检查插件依赖，缺少依赖时会提示用户安装。

## 常见问题

### Q1: 插件下载失败怎么办？

A: 检查以下几点：
- 网络连接是否正常
- 插件仓库 URL 是否正确
- 服务器是否正常运行
- 防火墙是否阻止了连接

### Q2: 安装插件后看不到新插件？

A: 安装插件后需要重启应用程序才能加载新插件。

### Q3: 如何更新已安装的插件？

A: 在插件管理器中，如果远程仓库有新版本，会显示"更新"按钮，点击即可更新。

### Q4: 插件体积太小，减少不明显？

A: 当前插件代码本身不大（约 45KB），主要体积在依赖库（PyQt、Pandas等）。
如果要显著减小体积，可以：
- 将依赖库也改为按需下载
- 使用更轻量级的 UI 框架
- 延迟加载大型库

### Q5: 如何回滚到之前的版本？

A: 在服务器上保留旧版本的插件包，修改 `plugins.json` 中的 URL 指向旧版本。

## 总结

通过插件分离和远程部署：

1. **减小安装包体积**：基础应用只包含核心功能
2. **按需加载**：用户只下载需要的插件
3. **独立更新**：插件可以独立更新，无需重新安装整个应用
4. **灵活扩展**：用户和第三方开发者可以发布自己的插件

下一步建议：
1. 部署插件到远程服务器
2. 测试完整下载和安装流程
3. 收集用户反馈，优化插件管理器体验
