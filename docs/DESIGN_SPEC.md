# WorkTools 设计规范

## 1. 项目概述

WorkTools 是一个基于 PyQt5 的模块化工作工具，采用插件式架构，支持功能的动态扩展。

### 核心设计原则

1. **插件化**：每个功能都是独立的插件，可以独立安装、卸载、启用、禁用
2. **简单直观**：用户一眼就能看懂每个功能是干什么的，怎么用
3. **统一入口**：插件的设置都通过工作区右上角的"设置"按钮打开
4. **自包含**：插件内部处理所有相关逻辑，不依赖其他插件

### 项目架构

```
WorkTools/
├── worktools/           # 核心框架
│   ├── base_plugin.py      # 插件基类
│   ├── plugin_manager.py   # 插件管理器
│   ├── navigation.py       # 导航面板
│   ├── workspace.py        # 工作区
│   └── plugins/          # 插件目录
│       └── *.py          # 各个插件
├── main.py              # 程序入口
├── version.json         # 版本信息
└── docs/               # 文档目录
```

---

## 2. 插件开发规范

### 2.1 插件基类

所有插件必须继承 `BasePlugin` 类，并实现必要的方法：

```python
from worktools.base_plugin import BasePlugin

class MyPlugin(BasePlugin):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._name = "插件名称"
        self._description = "插件描述"

    def get_name(self) -> str:
        return self._name

    def get_description(self) -> str:
        return self._description

    def get_icon(self):
        return None  # 或返回 QIcon 对象

    def get_category(self) -> str:
        return "工具分类"  # 如：数据工具、图片工具等

    def _setup_ui(self):
        """创建插件界面"""
        pass

    def _connect_signals(self):
        """连接信号和槽"""
        pass
```

### 2.2 必须实现的方法

| 方法 | 说明 | 必须实现 |
|------|------|----------|
| `get_name()` | 返回插件显示名称 | ✅ 是 |
| `get_description()` | 返回插件描述信息 | ✅ 是 |
| `get_icon()` | 返回插件图标 | ✅ 是（可返回None） |
| `get_category()` | 返回插件分类 | ✅ 是 |
| `_setup_ui()` | 创建插件用户界面 | ✅ 是 |
| `_connect_signals()` | 连接信号和槽 | ✅ 是 |

### 2.3 可选实现的方法

#### 2.3.1 插件设置接口

插件如果有设置选项，必须实现以下两种方式之一：

**方式1：实现 `_show_settings_dialog()` 方法（推荐）**

```python
def _show_settings_dialog(self):
    """显示插件设置对话框"""
    dialog = MySettingsDialog(self)
    dialog.exec_()
```

**方式2：实现 `get_settings_widget()` 方法**

```python
def get_settings_widget(self) -> QWidget:
    """返回插件设置界面控件"""
    return MySettingsWidget()
```

**注意**：
- 实现任一方法后，工作区右上角的"设置"按钮会自动启用
- 推荐使用方式1（对话框），更符合用户体验
- 未实现任何设置接口的插件，"设置"按钮显示为灰色不可用

#### 2.3.2 状态保存和恢复

```python
def save_state(self) -> dict:
    """保存插件状态"""
    return {
        'key1': value1,
        'key2': value2
    }

def restore_state(self, state: dict):
    """恢复插件状态"""
    self.key1 = state.get('key1')
    self.key2 = state.get('key2')
```

#### 2.3.3 生命周期钩子

```python
def on_activate(self):
    """当插件被激活时调用"""
    pass

def on_deactivate(self):
    """当插件被停用时调用"""
    pass
```

### 2.4 插件命名规范

1. **文件名**：使用小写字母和下划线，如 `my_plugin.py`
2. **类名**：使用大驼峰命名，如 `MyPluginPlugin`
3. **显示名称**：简洁明了，如"Excel合并工具"
4. **分类名称**：使用通用分类，如"数据工具"、"图片工具"

### 2.5 插件目录结构

```
worktools/plugins/
├── __init__.py           # 插件包初始化
├── my_plugin.py          # 插件主文件
└── my_plugin_resources/  # 插件资源目录（可选）
    └── icons/           # 插件图标
```

---

## 3. UI 设计规范

### 3.1 界面布局原则

1. **标题明确**：每个控件要有清晰的标签，用户一看就知道是干什么的
2. **分组合理**：相关功能放在一个组里，用 QGroupBox 分组
3. **间距一致**：统一使用 5px 的间距
4. **尺寸合适**：窗口最小尺寸不小于 800x600

### 3.2 控件使用规范

| 控件类型 | 使用场景 | 示例 |
|----------|----------|------|
| QPushButton | 触发操作 | "选择文件"、"开始处理" |
| QLineEdit | 输入文本 | 文件路径、水印文字 |
| QSpinBox | 输入数字 | 字体大小、跳过行数 |
| QComboBox | 选择选项 | 水印类型、导出格式 |
| QCheckBox | 是/否选项 | "覆盖原图"、"添加后缀" |
| QGroupBox | 功能分组 | "图片选择"、"输出设置" |
| QProgressBar | 显示进度 | 处理进度 |

### 3.3 按钮使用规范

1. **主操作按钮**：放在底部，突出显示
2. **次要操作按钮**：放在主操作按钮旁边
3. **浏览按钮**：放在输入框旁边

```python
# 正确的按钮布局
button_layout = QHBoxLayout()
button_layout.addWidget(self.process_btn)    # 主操作
button_layout.addWidget(self.clear_btn)       # 次要操作
main_layout.addLayout(button_layout)
```

### 3.4 消息提示规范

| 场景 | 使用方法 | 示例 |
|--------|----------|------|
| 提示信息 | `QMessageBox.information()` | 处理完成 |
| 警告信息 | `QMessageBox.warning()` | 文件不存在 |
| 错误信息 | `QMessageBox.critical()` | 处理失败 |
| 确认操作 | `QMessageBox.question()` | 确认删除 |
| 状态提示 | `QStatusBar.showMessage()` | "已加载 3 个插件" |

---

## 4. 功能设计原则

### 4.1 功能可见性原则

**原则**：用户一眼就能看出这个功能是干什么的

**实现方式**：
1. **插件名称要明确**：如"Excel合并工具"而不是"MergeTool"
2. **描述要具体**：如"合并多个Excel文件的数据"而不是"处理Excel"
3. **界面标签要清晰**：如"跳过顶部标题行数"而不是"Skip Header"

### 4.2 操作简单性原则

**原则**：用户用最少的步骤完成操作

**实现方式**：
1. **提供默认值**：合理的默认配置，用户可直接使用
2. **批量操作**：支持一次处理多个文件
3. **实时预览**：处理前让用户看到结果预览

### 4.3 错误友好性原则

**原则**：出错时告诉用户为什么、怎么解决

**实现方式**：
```python
try:
    # 处理逻辑
    pass
except Exception as e:
    # 友好的错误提示
    QMessageBox.warning(
        self, 
        "处理失败", 
        f"处理文件时出错：{filename}\n\n"
        f"错误原因：{str(e)}\n\n"
        f"建议：\n"
        f"1. 检查文件是否被其他程序打开\n"
        f"2. 确认文件格式是否正确"
    )
```

### 4.4 设置跟随插件原则

**原则**：插件的设置通过工作区的"设置"按钮打开

**实现方式**：
```python
class MyPlugin(BasePlugin):
    def _show_settings_dialog(self):
        """显示插件设置对话框"""
        dialog = MySettingsDialog(self)
        dialog.exec_()
```

**系统级配置**：如果多个插件共享的配置（如API Key），放在"设置 > 系统设置"

---

## 5. 代码规范

### 5.1 文件编码

所有Python文件必须使用UTF-8编码，在文件开头声明：

```python
# -*- coding: utf-8 -*-
```

### 5.2 导入顺序

```python
# 1. 标准库
import os
import json
import logging

# 2. 第三方库
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PIL import Image

# 3. 本地模块
from worktools.base_plugin import BasePlugin
from worktools.api_settings_dialog import APISettingsDialog
```

### 5.3 类和函数命名

```python
# 类名：大驼峰
class ExcelMergerPlugin(BasePlugin):
    pass

# 方法名：下划线开头（私有方法）
def _setup_ui(self):
    pass

def _connect_signals(self):
    pass

# 公开方法：不以下划线开头
def get_name(self) -> str:
    pass
```

### 5.4 注释规范

```python
def _merge_files(self):
    """合并文件
    
    Args:
        无
        
    Returns:
        无
    """
    pass
```

### 5.5 日志规范

```python
import logging

logger = logging.getLogger(__name__)

# 信息级别：正常运行信息
logger.info("插件加载成功")

# 警告级别：不影响运行的错误
logger.warning("配置文件不存在，使用默认值")

# 错误级别：严重错误
logger.error(f"处理失败: {str(e)}", exc_info=True)
```

---

## 6. 多线程处理规范

### 6.1 为什么使用多线程

**原因**：耗时操作会阻塞UI，导致程序"假死"

**使用场景**：
- 处理大文件
- 网络请求
- 批量操作

### 6.2 多线程实现方式

```python
from PyQt5.QtCore import QThread, pyqtSignal

class Worker(QThread):
    """工作线程"""
    
    # 定义信号
    progress_updated = pyqtSignal(int, int)  # 当前进度, 总进度
    finished = pyqtSignal(bool, str)         # 是否成功, 消息
    error_occurred = pyqtSignal(str)          # 错误信息
    
    def run(self):
        """执行耗时操作"""
        try:
            for i in range(100):
                # 执行任务
                self.progress_updated.emit(i, 100)
            
            self.finished.emit(True, "处理完成")
        except Exception as e:
            self.error_occurred.emit(str(e))

class MyPlugin(BasePlugin):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker = None
        
    def _start_processing(self):
        """开始处理"""
        # 创建工作线程
        self.worker = Worker()
        
        # 连接信号
        self.worker.progress_updated.connect(self._on_progress_updated)
        self.worker.finished.connect(self._on_finished)
        self.worker.error_occurred.connect(self._on_error)
        
        # 禁用按钮
        self.process_btn.setEnabled(False)
        
        # 启动线程
        self.worker.start()
    
    def _on_progress_updated(self, current, total):
        """进度更新"""
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
    
    def _on_finished(self, success, message):
        """处理完成"""
        self.process_btn.setEnabled(True)
        if success:
            QMessageBox.information(self, "完成", message)
        else:
            QMessageBox.warning(self, "警告", message)
    
    def _on_error(self, error_msg):
        """发生错误"""
        self.process_btn.setEnabled(True)
        QMessageBox.critical(self, "错误", f"处理失败：{error_msg}")
```

### 6.3 多线程注意事项

1. **不要在子线程中操作UI**：所有UI操作必须通过信号在主线程执行
2. **线程结束后清理**：释放资源，防止内存泄漏
3. **处理线程中断**：响应取消操作

---

## 7. 插件发布规范

### 7.1 插件元数据

每个插件应包含以下元数据：

```python
class MyPlugin(BasePlugin):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._name = "插件名称"
        self._description = "插件描述"
        self._version = "1.0.0"      # 插件版本
        self._author = "作者名称"      # 插件作者
        self._dependencies = []         # 依赖的库
```

### 7.2 插件依赖管理

```python
# 在插件文件顶部声明依赖
# 依赖库：openpyxl, pandas, Pillow

import os
import logging
from PyQt5.QtWidgets import QWidget

try:
    import openpyxl
    import pandas
    import PIL
except ImportError as e:
    logging.error(f"缺少依赖库: {str(e)}")
    raise ImportError("请安装插件所需的依赖库")
```

### 7.3 插件配置文件

插件可以在 `worktools/plugins/` 目录下创建配置文件 `plugin_config.json`：

```json
{
  "my_plugin": {
    "enabled": true,
    "version": "1.0.0",
    "description": "插件描述",
    "author": "作者",
    "dependencies": ["openpyxl", "pandas"]
  }
}
```

---

## 8. 远程插件管理

### 8.1 插件仓库格式

远程插件仓库使用 JSON 格式定义所有可用插件：

```json
{
  "version": "1.0",
  "update_url": "https://tools.kyeo.top/plugins/versions.json",
  "plugins": [
    {
      "id": "excel_to_pdf",
      "name": "Excel转PDF",
      "description": "将Excel文件转换为PDF格式，支持批量转换",
      "version": "1.0.0",
      "author": "作者名称",
      "category": "数据工具",
      "url": "https://tools.kyeo.top/plugins/excel_to_pdf.zip",
      "dependencies": ["openpyxl>=3.0.0", "fpdf>=1.7.0"],
      "icon": "https://tools.kyeo.top/plugins/icons/excel_to_pdf.png",
      "file_size": 15360,
      "download_count": 1234,
      "rating": 4.5,
      "release_date": "2025-12-10",
      "min_app_version": "1.0.0",
      "screenshot": "https://tools.kyeo.top/plugins/screenshots/excel_to_pdf.png"
    }
  ]
}
```

### 8.2 插件管理器

插件管理器插件负责从远程仓库下载和安装插件：

**核心功能**：
1. **插件列表**：显示所有可用插件，包括名称、分类、版本、大小等信息
2. **搜索和筛选**：按名称、描述搜索，按分类筛选
3. **安装插件**：下载插件文件并安装到 `worktools/plugins/` 目录
4. **卸载插件**：从本地删除已安装的插件
5. **依赖检查**：安装前检查依赖是否满足

**实现要点**：
```python
class PluginManagerTool(BasePlugin):
    """插件管理工具"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._name = "插件管理"
        self._description = "查看、下载和管理远程插件"
        self.remote_plugins = []
        self.local_plugins = []
        self.plugin_repo_url = "https://tools.kyeo.top/plugins/plugins.json"
        
    def _refresh_plugins(self):
        """刷新插件列表"""
        # 1. 从远程仓库获取插件列表
        # 2. 获取本地已安装插件列表
        # 3. 填充表格
        
    def _install_plugin(self, plugin: dict):
        """安装插件"""
        # 1. 检查依赖
        # 2. 确认安装
        # 3. 下载插件文件
        # 4. 解压到 plugins/ 目录
        # 5. 提示重启应用
        
    def _uninstall_plugin(self, plugin_id: str):
        """卸载插件"""
        # 1. 确认卸载
        # 2. 删除插件文件
        # 3. 提示重启应用
```

### 8.3 插件安装流程

```
1. 用户在插件管理器中选择插件
        ↓
2. 点击"安装"按钮
        ↓
3. 检查依赖是否满足
        ├─ 依赖满足 → 继续
        └─ 依赖不满足 → 提示安装依赖 → 退出
        ↓
4. 确认安装对话框
        ├─ 用户确认 → 继续
        └─ 用户取消 → 退出
        ↓
5. 下载插件文件（显示进度）
        ↓
6. 解压插件到 plugins/ 目录
        ↓
7. 提示重启应用使插件生效
```

### 8.4 插件卸载流程

```
1. 用户在插件管理器中选择已安装插件
        ↓
2. 点击"卸载"按钮
        ↓
3. 确认卸载对话框
        ├─ 用户确认 → 继续
        └─ 用户取消 → 退出
        ↓
4. 删除插件文件
        ↓
5. 提示重启应用使更改生效
```

### 8.5 安全性考虑

1. **插件来源验证**：只从可信的插件仓库下载插件
2. **依赖检查**：安装前检查所有依赖是否满足
3. **文件验证**：验证下载的插件文件完整性
4. **沙箱隔离**：限制插件的权限范围
5. **用户确认**：安装和卸载前都需要用户确认

---

## 9. 常见问题

### Q1: 插件设置按钮为什么不启用？

**A**: 检查是否实现了 `_show_settings_dialog()` 或 `get_settings_widget()` 方法。

### Q2: 如何添加全局配置？

**A**: 全局配置（如API Key）放在 "设置 > 系统设置" 中，通过 `APISettingsDialog` 实现。

### Q3: 插件之间如何通信？

**A**: 使用信号和槽机制，避免直接调用其他插件。

### Q4: 如何处理耗时操作？

**A**: 使用 QThread 创建工作线程，避免阻塞UI。

---

## 9. 更新日志

### v1.1.0 (2025-12-11)
- 增加远程插件管理章节
- 定义插件仓库JSON格式
- 定义插件管理器功能规范
- 定义插件安装/卸载流程
- 添加安全性考虑

### v1.0.10 (2025-12-11)
- 砍掉菜单栏的文件菜单（只有关闭功能）
- 砍掉菜单栏的设置菜单（与插件设置重复）
- 砍掉菜单栏的工具菜单（重新加载插件功能无用）
- 砍掉菜单栏的视图菜单（暂无功能）
- 精简菜单栏，只保留帮助菜单
- 更新功能设计原则：取消不必要的菜单项

### v1.0.9 (2025-12-11)
- 初始版本发布
- 建立插件化架构规范
- 定义UI设计规范
- 定义功能设计原则
