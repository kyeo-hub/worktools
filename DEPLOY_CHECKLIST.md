# 插件分离部署清单

## 已完成的工作

### 1. 插件打包 ✅

- [x] 创建 `build_plugins.py` 打包脚本
- [x] 打包所有 7 个插件为 .zip 文件
- [x] 生成 `plugins.json` 插件仓库索引文件
- [x] 总插件包大小：45.41 KB

**生成的文件** (`plugin_packages/`):
```
plugin_packages/
├── plugins.json                 (4.43 KB)
├── text_processor.zip          (3.51 KB)
├── file_manager.zip            (6.49 KB)
├── system_tools.zip            (6.63 KB)
├── monthly_summary.zip         (5.60 KB)
├── excel_merger.zip            (6.76 KB)
├── excel_deduplication.zip     (5.06 KB)
└── image_watermark.zip         (11.37 KB)
```

### 2. 创建精简版本 ✅

- [x] 移除内置插件（保留插件管理器）
- [x] 创建 `builtin_backup/` 备份目录
- [x] 测试精简版本运行正常

**当前插件目录** (`worktools/plugins/`):
```
worktools/plugins/
├── __init__.py                 (608 B)
├── local_plugins.json          (104 B)
├── plugin_manager_tool.py      (19.92 KB)
└── builtin_backup/             (备份目录)
```

### 3. 体积对比 ✅

| 版本 | 目录大小 | ZIP包大小 | 减少 |
|------|----------|-----------|------|
| 完整版 | 90.99 KB | 27.56 KB | - |
| 精简版 | 86.37 KB | 26.32 KB | 4.5% |

**说明**：
- 插件代码本身不大（约 45KB）
- 主要体积在依赖库（PyQt、Pandas等）
- 使用 PyInstaller 打包成 exe 后效果更明显

### 4. 本地测试环境 ✅

- [x] 创建 `test_server/plugins/` 本地测试目录
- [x] 复制插件包到测试目录
- [x] 配置本地测试仓库 `plugins.json`
- [x] 测试成功加载 7 个插件

### 5. 文档创建 ✅

- [x] `docs/DEPLOY_PLUGINS.md` - 插件部署指南
- [x] `docs/PLUGIN_MANAGER_GUIDE.md` - 插件管理器使用指南
- [x] `build_plugins.py` - 插件打包脚本
- [x] `compare_package_size.py` - 体积对比脚本

## 下一步操作

### 步骤 1: 推送到远程服务器

**需要上传的文件**：
```
plugin_packages/
├── plugins.json
├── text_processor.zip
├── file_manager.zip
├── system_tools.zip
├── monthly_summary.zip
├── excel_merger.zip
├── excel_deduplication.zip
└── image_watermark.zip
```

**上传到**：`https://tools.kyeo.top/plugins/`

**上传方式**（选择一种）：
- [ ] FTP/SFTP 工具（FileZilla、WinSCP）
- [ ] 服务器控制面板文件管理器
- [ ] 命令行 scp: `scp plugin_packages/* user@tools.kyeo.top:/var/www/tools.kyeo.top/plugins/`

### 步骤 2: 更新插件仓库 URL

修改 `plugin_packages/plugins.json` 中的 URL：

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

然后重新上传 `plugins.json`。

### 步骤 3: 配置应用使用远程仓库

修改 `worktools/plugins/plugin_manager_tool.py` 第 40 行：

```python
# 修改前
self.plugin_repo_url = "file://d:/work-tools/test_server/plugins/plugins.json"

# 修改后
self.plugin_repo_url = "https://tools.kyeo.top/plugins/plugins.json"
```

### 步骤 4: 测试部署

1. [ ] 打开应用程序
2. [ ] 进入"插件管理"
3. [ ] 点击"刷新"按钮
4. [ ] 确认显示 7 个可用插件
5. [ ] 点击"安装"安装一个插件
6. [ ] 观察下载进度
7. [ ] 确认安装成功提示
8. [ ] 重启应用程序
9. [ ] 确认新插件已加载

### 步骤 5: 验证功能

- [ ] 测试每个插件的基本功能
- [ ] 测试卸载插件功能
- [ ] 测试插件设置功能
- [ ] 测试搜索和筛选功能

## 回滚方案

如果部署出现问题，可以快速回滚：

### 回滚到内置插件版本

```bash
# 恢复备份的插件
copy worktools/plugins/builtin_backup/*.py worktools/plugins/
```

### 回滚到本地测试版本

修改 `worktools/plugins/plugin_manager_tool.py`：
```python
self.plugin_repo_url = "file://d:/work-tools/test_server/plugins/plugins.json"
```

## 注意事项

1. **服务器要求**：
   - 支持 HTTPS（推荐）
   - 支持静态文件访问
   - 文件 MIME 类型正确设置

2. **插件安全**：
   - 只从可信来源下载插件
   - 检查插件依赖是否安全
   - 定期更新插件版本

3. **用户体验**：
   - 插件安装后需要重启应用
   - 缺少依赖时会提示用户
   - 提供清晰的错误信息

## 总结

通过本次改造，实现了：

1. ✅ 插件分离：核心应用与功能插件分离
2. ✅ 远程部署：支持从远程仓库下载插件
3. ✅ 按需加载：用户只下载需要的插件
4. ✅ 独立更新：插件可以独立更新
5. ✅ 体积优化：基础应用体积减小 4.5%

**效果**：
- 用户首次安装时只需下载核心应用（约 26KB）
- 用户按需下载功能插件（每个 3-11KB）
- 插件更新无需重新安装整个应用
- 第三方开发者可以发布自己的插件

**下一步**：
请按照上面的"下一步操作"步骤，将插件推送到远程服务器并测试完整流程。
