# 插件管理器使用指南

## 概述

插件管理器是一个基于插件架构的远程插件管理工具，允许用户从远程仓库按需下载和安装插件。

## 功能特性

- **浏览插件**：查看所有可用的远程插件
- **搜索筛选**：按名称、描述搜索，按分类筛选
- **安装插件**：一键下载并安装插件
- **卸载插件**：卸载不需要的插件
- **依赖检查**：自动检查插件依赖是否满足
- **本地测试**：支持本地测试仓库，无需服务器

## 使用方法

### 1. 打开插件管理器

启动应用程序后，在左侧导航面板中点击"插件管理"即可打开插件管理器。

### 2. 浏览插件

插件管理器会自动加载插件列表，显示以下信息：
- **名称**：插件名称
- **分类**：插件所属分类（数据工具、图片工具、系统工具、其他）
- **版本**：插件版本号
- **大小**：插件文件大小
- **操作**：安装或卸载按钮

### 3. 搜索和筛选

- **搜索**：在搜索框中输入插件名称或描述关键词
- **分类筛选**：从下拉菜单中选择分类进行筛选

### 4. 安装插件

1. 在插件列表中找到要安装的插件
2. 点击"安装"按钮
3. 确认安装信息（版本、大小、作者等）
4. 系统自动下载并安装插件
5. 安装完成后，**重启应用程序**使插件生效

**注意事项**：
- 安装前会检查依赖库是否满足
- 如果缺少依赖库，需要先安装依赖
- 插件下载到 `worktools/plugins/` 目录

### 5. 卸载插件

1. 在插件列表中找到已安装的插件（显示为灰色）
2. 点击"卸载"按钮
3. 确认卸载操作
4. **重启应用程序**使更改生效

### 6. 配置插件仓库

#### 6.1 打开设置

点击插件管理器右上角的"设置"按钮。

#### 6.2 配置仓库URL

**方式1：使用本地测试仓库**
- 点击"使用本地测试仓库"按钮
- 用于本地测试，无需服务器

**方式2：使用远程仓库**
- 点击"使用远程仓库"按钮
- 默认远程仓库：`https://tools.kyeo.top/plugins/plugins.json`
- 也可以手动输入其他仓库URL

#### 6.3 保存设置

点击"确定"保存设置，插件管理器会自动刷新插件列表。

## 部署远程插件仓库

### 1. 创建插件仓库文件

参考 `docs/plugins.json.example` 创建插件仓库文件：

```json
{
  "version": "1.0",
  "update_url": "https://your-server.com/plugins/versions.json",
  "plugins": [
    {
      "id": "plugin_id",
      "name": "插件名称",
      "description": "插件描述",
      "version": "1.0.0",
      "author": "作者名称",
      "category": "分类",
      "url": "https://your-server.com/plugins/plugin_id.zip",
      "dependencies": ["lib_name>=1.0.0"],
      "icon": "https://your-server.com/plugins/icons/plugin_id.png",
      "file_size": 10240,
      "download_count": 100,
      "rating": 4.5,
      "release_date": "2025-12-10",
      "min_app_version": "1.0.0"
    }
  ]
}
```

### 2. 打包插件

将插件文件打包成 `.zip` 格式：

```bash
cd worktools/plugins
zip plugin_id.zip plugin_id.py
```

### 3. 上传文件

将以下文件上传到服务器：
- `plugins.json` - 插件仓库索引文件
- `plugin_id.zip` - 插件压缩包
- `icons/` - 插件图标目录（可选）
- `screenshots/` - 插件截图目录（可选）

### 4. 配置访问权限

确保插件仓库文件可以通过HTTP/HTTPS访问。

### 5. 测试

1. 在插件管理器中输入仓库URL
2. 点击"刷新"按钮
3. 查看是否能正常加载插件列表
4. 尝试安装插件

## 开发自己的插件

### 1. 创建插件文件

在 `worktools/plugins/` 目录下创建新的插件文件，例如 `my_plugin.py`：

```python
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from worktools.base_plugin import BasePlugin

class MyPlugin(BasePlugin):
    """我的插件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._name = "我的插件"
        self._description = "这是我的第一个插件"
        self._setup_ui()
    
    def get_name(self) -> str:
        return self._name
    
    def get_description(self) -> str:
        return self._description
    
    def get_icon(self):
        return None
    
    def _setup_ui(self):
        """设置用户界面"""
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("我的插件内容"))
        layout.addWidget(QPushButton("点击我"))
```

### 2. 测试插件

重启应用程序，插件会自动加载并显示在导航面板中。

### 3. 发布插件

1. 打包插件为 `.zip` 文件
2. 在 `plugins.json` 中添加插件信息
3. 上传到服务器

## 常见问题

### Q1: 安装插件后看不到新插件？

A: 安装插件后需要**重启应用程序**才能使插件生效。

### Q2: 安装失败提示缺少依赖？

A: 根据提示安装缺少的依赖库，例如：
```bash
pip install openpyxl>=3.0.0
```

### Q3: 如何查看已安装的插件？

A: 在插件管理器中，已安装的插件名称会显示为灰色。

### Q4: 卸载插件后插件还在？

A: 卸载插件后需要**重启应用程序**才能使更改生效。

### Q5: 本地测试仓库是什么？

A: 本地测试仓库是用于测试的本地文件，无需部署到服务器。默认位置：`worktools/plugins/local_plugins.json`

### Q6: 如何切换到远程仓库？

A: 点击插件管理器右上角的"设置"按钮，然后选择"使用远程仓库"。

### Q7: 插件无法下载怎么办？

A: 请检查：
1. 网络连接是否正常
2. 仓库URL是否正确
3. 服务器是否正常运行

## 技术支持

如有问题或建议，请联系开发团队或提交Issue。
