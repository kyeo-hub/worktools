"""
插件管理工具
支持从远程仓库下载和安装插件
"""

import os
import sys
import json
import zipfile
import logging
from typing import List, Dict
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                               QLabel, QPushButton, QProgressBar, QMessageBox,
                               QTableWidget, QTableWidgetItem, QHeaderView,
                               QLineEdit, QComboBox, QDialog, QDialogButtonBox)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QSettings
from PyQt5.QtGui import QIcon
import requests

from worktools.base_plugin import BasePlugin

logger = logging.getLogger(__name__)


def get_user_plugins_dir():
    """获取用户插件目录"""
    # Windows: %APPDATA%/WorkTools/plugins
    # Mac: ~/Library/Application Support/WorkTools/plugins
    # Linux: ~/.config/WorkTools/plugins
    if sys.platform == 'win32':
        base_dir = os.environ.get('APPDATA', os.path.expanduser('~'))
    elif sys.platform == 'darwin':
        base_dir = os.path.expanduser('~/Library/Application Support')
    else:
        base_dir = os.path.expanduser('~/.config')

    plugins_dir = os.path.join(base_dir, 'WorkTools', 'plugins')

    # 确保目录存在
    if not os.path.exists(plugins_dir):
        os.makedirs(plugins_dir)

    return plugins_dir


class PluginManagerSettingsDialog(QDialog):
    """插件管理器设置对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("插件管理器设置")
        self.setMinimumSize(500, 200)
        self.settings = QSettings("WorkTools", "PyQtWorkTools")
        
        self._setup_ui()
        self._load_settings()
        
    def _setup_ui(self):
        """设置界面"""
        layout = QVBoxLayout(self)
        
        # 插件仓库URL
        url_layout = QHBoxLayout()
        url_layout.addWidget(QLabel("插件仓库URL:"))
        self.repo_url_edit = QLineEdit()
        self.repo_url_edit.setPlaceholderText("输入插件仓库的JSON文件URL")
        url_layout.addWidget(self.repo_url_edit)
        layout.addLayout(url_layout)
        
        # 快捷按钮
        buttons_layout = QHBoxLayout()
        
        local_btn = QPushButton("使用本地测试仓库")
        local_btn.clicked.connect(self._use_local_repo)
        buttons_layout.addWidget(local_btn)
        
        remote_btn = QPushButton("使用远程仓库")
        remote_btn.clicked.connect(self._use_remote_repo)
        buttons_layout.addWidget(remote_btn)
        
        layout.addLayout(buttons_layout)
        
        # 说明
        info_label = QLabel(
            "\n说明:\n"
            "• 本地测试仓库: 用于本地测试，无需服务器\n"
            "• 远程仓库: 从服务器下载插件，需要先部署插件到服务器\n"
            "\n如何部署远程仓库:\n"
            "1. 参考 docs/plugins.json.example 创建插件仓库文件\n"
            "2. 将插件打包成 .zip 文件\n"
            "3. 上传仓库文件和插件包到服务器\n"
            "4. 在上方输入插件仓库的URL地址"
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: gray;")
        layout.addWidget(info_label)
        
        # 对话框按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
    def _load_settings(self):
        """加载设置"""
        repo_url = self.settings.value("plugin_repo_url", "")
        if repo_url:
            self.repo_url_edit.setText(repo_url)
            
    def save_settings(self):
        """保存设置"""
        self.settings.setValue("plugin_repo_url", self.repo_url_edit.text())
        
    def get_repo_url(self):
        """获取仓库URL"""
        return self.repo_url_edit.text()
        
    def _use_local_repo(self):
        """使用本地测试仓库"""
        local_repo_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 
            'local_plugins.json'
        )
        self.repo_url_edit.setText(f"file://{local_repo_path}")
        
    def _use_remote_repo(self):
        """使用远程仓库"""
        self.repo_url_edit.setText("https://tools.kyeo.top/plugins/plugins.json")


class PluginDownloadWorker(QThread):
    """插件下载工作线程"""
    
    progress_updated = pyqtSignal(int, int)  # 已下载, 总大小
    finished = pyqtSignal(bool, str, str)     # 是否成功, 插件文件路径, 插件ID
    error_occurred = pyqtSignal(str)          # 错误信息
    
    def __init__(self, plugin_url: str, plugin_id: str, save_dir: str):
        super().__init__()
        self.plugin_url = plugin_url
        self.plugin_id = plugin_id
        self.save_dir = save_dir
        
    def run(self):
        """下载插件"""
        try:
            logger.info(f"开始下载插件: {self.plugin_id} from {self.plugin_url}")
            
            # 检查是否是本地文件
            if self.plugin_url.startswith('file://'):
                # 复制本地文件
                src_path = self.plugin_url[7:]  # 去掉 "file://" 前缀
                file_name = os.path.basename(src_path)
                file_path = os.path.join(self.save_dir, file_name)
                
                import shutil
                total_size = os.path.getsize(src_path)
                self.progress_updated.emit(total_size, total_size)
                
                shutil.copy2(src_path, file_path)
            else:
                # 使用 requests 下载
                response = requests.get(self.plugin_url, stream=True, timeout=30)
                response.raise_for_status()
                
                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0
                
                file_name = os.path.basename(self.plugin_url)
                file_path = os.path.join(self.save_dir, file_name)
                
                with open(file_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            self.progress_updated.emit(downloaded, total_size)
            
            logger.info(f"插件下载完成: {self.plugin_id}")
            self.finished.emit(True, file_path, self.plugin_id)
            
        except Exception as e:
            logger.error(f"下载插件失败: {str(e)}")
            self.error_occurred.emit(f"下载失败: {str(e)}")
            self.finished.emit(False, "", self.plugin_id)


class PluginManagerTool(BasePlugin):
    """插件管理工具"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._name = "插件管理"
        self._description = "查看、下载和管理远程插件"
        self.remote_plugins: List[Dict] = []  # 远程插件列表
        self.local_plugins: List[str] = []  # 本地已安装插件
        # 默认使用本地测试仓库
        self.plugin_repo_url = "file://d:/work-tools/test_server/plugins/plugins.json"
        self.download_worker = None
        self._is_first_load = True  # 标记是否是首次加载
        # 注意：不要在这里调用 _setup_ui()，由 BasePlugin.initialize() 统一调用
        
    def get_name(self) -> str:
        return self._name
        
    def get_description(self) -> str:
        return self._description
        
    def get_icon(self):
        return None
        
    def get_category(self) -> str:
        return "系统工具"
        
    def on_activate(self):
        """当插件被激活时调用"""
        super().on_activate()
        # 只在首次激活时刷新，避免重复刷新
        if self._is_first_load:
            logger.info("插件管理器首次被激活，刷新列表")
            self._is_first_load = False
            self._refresh_plugins()
        
    def _setup_ui(self):
        """设置用户界面"""
        # 检查是否已经有布局，避免重复设置
        if self.layout() is not None:
            logger.warning("PluginManagerTool 已经有布局，跳过 _setup_ui")
            return
            
        main_layout = QVBoxLayout(self)
        
        # 搜索栏
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("搜索:"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("输入插件名称或描述...")
        self.search_edit.textChanged.connect(self._on_search_changed)
        search_layout.addWidget(self.search_edit)
        
        self.category_combo = QComboBox()
        self.category_combo.addItems(["全部", "数据工具", "图片工具", "系统工具", "其他"])
        self.category_combo.currentTextChanged.connect(self._on_category_changed)
        search_layout.addWidget(self.category_combo)
        
        self.refresh_btn = QPushButton("刷新")
        self.refresh_btn.clicked.connect(self._refresh_plugins)
        search_layout.addWidget(self.refresh_btn)
        
        main_layout.addLayout(search_layout)
        
        # 插件列表表格
        self.plugins_table = QTableWidget()
        self.plugins_table.setColumnCount(6)
        self.plugins_table.setHorizontalHeaderLabels(["名称", "描述", "分类", "版本", "大小", "操作"])
        self.plugins_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)  # 名称
        self.plugins_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)  # 描述自适应
        self.plugins_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)  # 分类
        self.plugins_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)  # 版本
        self.plugins_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)  # 大小
        self.plugins_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Fixed)  # 操作固定宽度
        self.plugins_table.setColumnWidth(5, 140)  # 操作列宽140像素，容纳更大按钮
        self.plugins_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.plugins_table.setEditTriggers(QTableWidget.NoEditTriggers)
        # 设置表格最小高度，确保能显示内容
        self.plugins_table.setMinimumHeight(300)
        # 设置默认行高，让按钮和文字更清晰
        self.plugins_table.verticalHeader().setDefaultSectionSize(45)
        # 设置表格样式，使其更明显
        self.plugins_table.setStyleSheet("""
            QTableWidget {
                border: 2px solid #cccccc;
                gridline-color: #dddddd;
                background-color: white;
                alternate-background-color: #f5f5f5;
            }
            QTableWidget::item {
                padding: 5px;
                border-bottom: 1px solid #eeeeee;
            }
            QHeaderView::section {
                background-color: #e0e0e0;
                padding: 8px;
                border: 1px solid #cccccc;
                font-weight: bold;
            }
        """)
        self.plugins_table.setAlternatingRowColors(True)
        main_layout.addWidget(self.plugins_table, 1)  # 添加拉伸因子，让表格占据主要空间
        
        # 操作区域 - 显示安装进度和结果
        from PyQt5.QtWidgets import QFrame
        self.operation_panel = QFrame()
        self.operation_panel.setStyleSheet("""
            QFrame {
                border: 1px solid #cccccc;
                background-color: #f9f9f9;
                border-radius: 4px;
                padding: 5px;
            }
        """)
        self.operation_panel.setVisible(False)  # 默认隐藏
        operation_layout = QVBoxLayout(self.operation_panel)
        operation_layout.setContentsMargins(10, 10, 10, 10)
        
        # 操作标题
        self.operation_title = QLabel()
        self.operation_title.setStyleSheet("font-weight: bold; font-size: 12px; border: none; background: transparent;")
        operation_layout.addWidget(self.operation_title)
        
        # 进度条
        self.progress_bar = QProgressBar()
        operation_layout.addWidget(self.progress_bar)
        
        # 操作详情
        self.operation_detail = QLabel()
        self.operation_detail.setStyleSheet("color: #666; border: none; background: transparent;")
        self.operation_detail.setWordWrap(True)
        operation_layout.addWidget(self.operation_detail)
        
        # 重启提示（安装成功后显示）
        self.restart_hint = QLabel("⚠️ 插件安装成功，请重启应用使插件生效")
        self.restart_hint.setStyleSheet("color: #ff6600; font-weight: bold; border: none; background: transparent;")
        self.restart_hint.setVisible(False)
        operation_layout.addWidget(self.restart_hint)
        
        # 关闭按钮
        close_btn_layout = QHBoxLayout()
        close_btn_layout.addStretch()
        self.close_operation_btn = QPushButton("关闭")
        self.close_operation_btn.setFixedWidth(80)
        self.close_operation_btn.clicked.connect(self._hide_operation_panel)
        close_btn_layout.addWidget(self.close_operation_btn)
        operation_layout.addLayout(close_btn_layout)
        
        main_layout.addWidget(self.operation_panel)
        
        # 调试信息标签
        self.debug_label = QLabel("等待加载插件...")
        self.debug_label.setStyleSheet("color: red; font-weight: bold;")
        main_layout.addWidget(self.debug_label)
        
        # 状态标签
        self.status_label = QLabel()
        main_layout.addWidget(self.status_label)
        
        # 加载设置
        self._load_settings()
        
        # 初始加载
        QTimer.singleShot(500, self._refresh_plugins)
        
    def _load_settings(self):
        """加载设置"""
        settings = QSettings("WorkTools", "PyQtWorkTools")
        repo_url = settings.value("plugin_repo_url", "")
        if repo_url:
            self.plugin_repo_url = repo_url
            
    def _show_settings_dialog(self):
        """显示设置对话框"""
        dialog = PluginManagerSettingsDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            dialog.save_settings()
            self.plugin_repo_url = dialog.get_repo_url()
            self._refresh_plugins()
        
    def _refresh_plugins(self):
        """刷新插件列表"""
        self.debug_label.setText("正在刷新插件列表...")
        self.debug_label.setStyleSheet("color: blue; font-weight: bold;")
        self.status_label.setText("正在获取插件列表...")
        self.plugins_table.setRowCount(0)
        self.remote_plugins = []
        
        # 强制更新UI
        from PyQt5.QtWidgets import QApplication
        QApplication.processEvents()
        
        try:
            logger.info(f"从远程仓库获取插件列表: {self.plugin_repo_url}")
            
            # 检查是否是本地文件
            if self.plugin_repo_url.startswith('file://'):
                # 读取本地文件
                file_path = self.plugin_repo_url[7:]  # 去掉 "file://" 前缀
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                # 读取远程文件
                response = requests.get(self.plugin_repo_url, timeout=10)
                response.raise_for_status()
                data = response.json()
            
            self.remote_plugins = data.get('plugins', [])
            logger.info(f"获取到 {len(self.remote_plugins)} 个插件")
            
            # 获取已安装插件列表
            self.local_plugins = self._get_installed_plugins()
            
            # 填充表格
            self._fill_plugin_table()
            
            self.status_label.setText(f"共找到 {len(self.remote_plugins)} 个插件，已安装 {len(self.local_plugins)} 个")
            
        except Exception as e:
            logger.error(f"获取插件列表失败: {str(e)}")
            self.status_label.setText(f"获取插件列表失败: {str(e)}")
            # 不显示警告对话框，只显示状态标签
            
    def _get_installed_plugins(self) -> List[str]:
        """获取已安装的插件，返回插件ID列表（文件名即插件ID）"""
        plugin_dir = get_user_plugins_dir()
        installed = []

        if not os.path.exists(plugin_dir):
            return installed

        for file in os.listdir(plugin_dir):
            if file.endswith('.py') and file != '__init__.py':
                # 文件名（不含扩展名）即插件ID
                plugin_id = os.path.splitext(file)[0]
                installed.append(plugin_id)

        return installed
        
    def _fill_plugin_table(self):
        """填充插件表格"""
        self.plugins_table.setRowCount(0)
        
        search_text = self.search_edit.text().lower().strip()
        category_filter = self.category_combo.currentText()
        
        logger.info(f"填充表格，搜索文本: '{search_text}', 分类过滤: '{category_filter}'")
        logger.info(f"远程插件数量: {len(self.remote_plugins)}")
        
        for plugin in self.remote_plugins:
            # 获取插件信息，处理可能的空值
            plugin_name = plugin.get('name', '')
            plugin_desc = plugin.get('description', '')
            plugin_category = plugin.get('category', '其他')
            
            # 搜索过滤
            if search_text:
                name_match = search_text in plugin_name.lower()
                desc_match = search_text in plugin_desc.lower()
                if not name_match and not desc_match:
                    logger.debug(f"插件 '{plugin_name}' 被搜索过滤")
                    continue
            
            # 分类过滤
            if category_filter != "全部" and category_filter != plugin_category:
                logger.debug(f"插件 '{plugin_name}' 被分类过滤")
                continue
            
            # 检查是否已安装
            plugin_id = plugin.get('id', '')
            is_installed = self._is_plugin_installed(plugin_id)
            
            # 添加行
            row = self.plugins_table.rowCount()
            self.plugins_table.insertRow(row)
            
            logger.info(f"添加插件到表格 [{row}]: {plugin_name}")
            
            # 名称
            name_item = QTableWidgetItem(plugin_name)
            if is_installed:
                name_item.setForeground(Qt.gray)
            self.plugins_table.setItem(row, 0, name_item)
            
            # 描述
            desc_item = QTableWidgetItem(plugin_desc)
            desc_item.setToolTip(plugin_desc)  # 鼠标悬停显示完整描述
            self.plugins_table.setItem(row, 1, desc_item)
            
            # 分类
            self.plugins_table.setItem(row, 2, QTableWidgetItem(plugin_category))
            
            # 版本
            plugin_version = plugin.get('version', '1.0.0')
            self.plugins_table.setItem(row, 3, QTableWidgetItem(plugin_version))
            
            # 大小
            file_size = plugin.get('file_size', 0)
            size_kb = file_size // 1024
            size_str = f"{size_kb} KB" if size_kb < 1024 else f"{size_kb//1024} MB"
            self.plugins_table.setItem(row, 4, QTableWidgetItem(size_str))
            
            # 操作按钮
            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(5, 2, 5, 2)
            btn_layout.setSpacing(5)
            
            if is_installed:
                # 已安装，显示卸载按钮
                uninstall_btn = QPushButton("卸载")
                uninstall_btn.setMinimumWidth(90)
                uninstall_btn.setMinimumHeight(32)
                uninstall_btn.setStyleSheet("""
                    QPushButton {
                        padding: 6px 16px;
                        font-size: 13px;
                        font-weight: bold;
                    }
                """)
                uninstall_btn.clicked.connect(lambda checked, pid=plugin_id: self._uninstall_plugin(pid))
                btn_layout.addWidget(uninstall_btn)
            else:
                # 未安装，显示安装按钮
                install_btn = QPushButton("安装")
                install_btn.setMinimumWidth(90)
                install_btn.setMinimumHeight(32)
                install_btn.setStyleSheet("""
                    QPushButton {
                        padding: 6px 16px;
                        font-size: 13px;
                        font-weight: bold;
                    }
                """)
                install_btn.clicked.connect(lambda checked, p=plugin: self._install_plugin(p))
                btn_layout.addWidget(install_btn)
            
            btn_layout.addStretch()
            self.plugins_table.setCellWidget(row, 5, btn_widget)
        
        # 强制刷新表格显示
        self.plugins_table.viewport().update()
        self.plugins_table.show()  # 确保表格显示
        self.plugins_table.repaint()  # 强制重绘
        
        # 验证表格数据
        actual_rows = self.plugins_table.rowCount()
        actual_cols = self.plugins_table.columnCount()
        
        # 更新调试信息
        debug_text = f"表格: {actual_rows} 行 x {actual_cols} 列 | 可见: {self.plugins_table.isVisible()}"
        self.debug_label.setText(debug_text)
        self.debug_label.setStyleSheet("color: green; font-weight: bold;")
        
        # 打印第一行数据用于调试
        if actual_rows > 0:
            first_item = self.plugins_table.item(0, 0)
            if first_item:
                logger.info(f"第一行数据: {first_item.text()}")
        
        logger.info(f"表格填充完成，共 {actual_rows} 行")
            
    def _is_plugin_installed(self, plugin_id: str) -> bool:
        """检查插件是否已安装（文件名即插件ID）"""
        return plugin_id in self.local_plugins
        
    def _install_plugin(self, plugin: dict):
        """安装插件"""
        self.current_install_plugin = plugin
        
        # 显示操作面板
        self.operation_panel.setVisible(True)
        self.restart_hint.setVisible(False)
        self.operation_title.setText(f"准备安装插件: {plugin['name']}")
        self.operation_detail.setText(f"版本: {plugin['version']} | 作者: {plugin.get('author', '未知')}")
        self.progress_bar.setValue(0)
        
        # 检查依赖
        dependencies = plugin.get('dependencies', [])
        missing_deps = self._check_dependencies(dependencies)
        
        if missing_deps:
            # 自动安装缺失的依赖
            logger.info(f"检测到缺失的依赖: {missing_deps}")
            self.operation_title.setText(f"正在安装依赖...")
            self.operation_detail.setText(f"需要安装: {', '.join(missing_deps)}")
            
            from PyQt5.QtWidgets import QApplication
            QApplication.processEvents()
            
            if not self._auto_install_dependencies(missing_deps):
                self.operation_title.setText("❌ 依赖安装失败")
                self.operation_detail.setText(f"以下依赖安装失败，请手动安装:\n" + "\n".join(missing_deps))
                return
        
        # 开始下载
        self.operation_title.setText(f"正在下载 {plugin['name']}...")
        self.operation_detail.setText(f"来源: {plugin['url']}")

        plugin_dir = get_user_plugins_dir()

        self.download_worker = PluginDownloadWorker(
            plugin['url'],
            plugin['id'],
            plugin_dir
        )
        
        self.download_worker.progress_updated.connect(self._on_download_progress)
        self.download_worker.finished.connect(self._on_download_finished)
        self.download_worker.error_occurred.connect(self._on_download_error)
        
        self.download_worker.start()
        
    def _uninstall_plugin(self, plugin_id: str):
        """卸载插件"""
        # 显示操作面板
        self.operation_panel.setVisible(True)
        self.restart_hint.setVisible(False)
        self.operation_title.setText(f"正在卸载插件: {plugin_id}...")
        self.operation_detail.setText("正在删除插件文件...")
        self.progress_bar.setValue(0)
        
        from PyQt5.QtWidgets import QApplication
        QApplication.processEvents()

        try:
            plugin_dir = get_user_plugins_dir()
            plugin_file = os.path.join(plugin_dir, f"{plugin_id}.py")
            
            self.progress_bar.setValue(30)
            QApplication.processEvents()
            
            if os.path.exists(plugin_file):
                # 尝试删除文件，如果失败可能是文件被占用
                try:
                    os.remove(plugin_file)
                    logger.info(f"插件文件已删除: {plugin_file}")
                except PermissionError:
                    # 文件可能被占用，尝试重命名标记删除
                    import time
                    temp_name = plugin_file + f".deleted_{int(time.time())}"
                    os.rename(plugin_file, temp_name)
                    logger.info(f"插件文件已标记删除: {plugin_id}")
                
                self.progress_bar.setValue(70)
                QApplication.processEvents()
                
                logger.info(f"插件已卸载: {plugin_id}")
                
                # 从列表中移除
                if plugin_id in self.local_plugins:
                    self.local_plugins.remove(plugin_id)
                
                # 刷新表格
                self._fill_plugin_table()
                
                self.progress_bar.setValue(100)
                self.operation_title.setText(f"[OK] {plugin_id} 已卸载")
                self.operation_detail.setText("插件已成功卸载，请重启应用生效")
                self.status_label.setText(f"插件 {plugin_id} 已卸载")
            else:
                self.progress_bar.setValue(100)
                self.operation_title.setText(f"[WARN] {plugin_id} 不存在")
                self.operation_detail.setText("插件文件已经不存在")
                
        except Exception as e:
            logger.error(f"卸载插件失败: {str(e)}")
            self.progress_bar.setValue(0)
            self.operation_title.setText("[ERROR] 卸载失败")
            self.operation_detail.setText(f"卸载失败: {str(e)}")
            
    def _check_dependencies(self, dependencies: list) -> list:
        """检查依赖是否满足"""
        missing = []
        
        for dep in dependencies:
            try:
                import importlib
                
                # 解析依赖名称
                if '>=' in dep:
                    lib_name = dep.split('>=')[0]
                elif '==' in dep:
                    lib_name = dep.split('==')[0]
                else:
                    lib_name = dep
                
                importlib.import_module(lib_name.replace('-', '_'))
            except ImportError:
                missing.append(dep)
        
        return missing
        
    def _auto_install_dependencies(self, dependencies: list) -> bool:
        """自动使用 pip 安装依赖"""
        import subprocess
        import sys
        
        for dep in dependencies:
            try:
                logger.info(f"正在安装依赖: {dep}")
                self.status_label.setText(f"正在安装 {dep}...")
                
                # 使用 pip 安装
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "install", dep],
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                
                if result.returncode != 0:
                    logger.error(f"安装 {dep} 失败: {result.stderr}")
                    return False
                
                logger.info(f"安装 {dep} 成功")
                
            except subprocess.TimeoutExpired:
                logger.error(f"安装 {dep} 超时")
                return False
            except Exception as e:
                logger.error(f"安装 {dep} 出错: {str(e)}")
                return False
        
        self.status_label.setText("依赖安装完成")
        return True
        
    def _on_download_progress(self, downloaded: int, total: int):
        """下载进度更新"""
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(downloaded)
        if total > 0:
            percent = int(downloaded * 100 / total)
            self.operation_detail.setText(f"下载进度: {percent}% ({downloaded}/{total} 字节)")
        
    def _on_download_finished(self, success: bool, file_path: str, plugin_id: str):
        """下载完成"""
        if not success:
            self.operation_title.setText("❌ 下载失败")
            self.operation_detail.setText("插件下载失败，请检查网络连接")
            return
        
        try:
            # 解压插件文件
            extract_dir = os.path.dirname(file_path)
            
            if file_path.endswith('.zip'):
                self.operation_title.setText("正在解压插件...")
                from PyQt5.QtWidgets import QApplication
                QApplication.processEvents()
                
                with zipfile.ZipFile(file_path, 'r') as zipf:
                    zipf.extractall(extract_dir)
                
                # 删除压缩包
                os.remove(file_path)
            
            # 更新已安装列表
            if plugin_id not in self.local_plugins:
                self.local_plugins.append(plugin_id)
            
            # 刷新表格
            self._fill_plugin_table()
            
            plugin_name = self.current_install_plugin.get('name', plugin_id) if hasattr(self, 'current_install_plugin') else plugin_id
            logger.info(f"插件安装成功: {plugin_id}")
            
            self.operation_title.setText(f"✅ {plugin_name} 安装成功")
            self.operation_detail.setText("插件已成功安装到本地")
            self.restart_hint.setVisible(True)
            self.status_label.setText(f"插件 {plugin_id} 安装成功")
            
        except Exception as e:
            logger.error(f"安装插件失败: {str(e)}")
            self.operation_title.setText("❌ 安装失败")
            self.operation_detail.setText(f"安装插件时出错: {str(e)}")
            
    def _on_download_error(self, error_msg: str):
        """下载错误"""
        self.operation_title.setText("❌ 下载失败")
        self.operation_detail.setText(error_msg)
        
    def _on_search_changed(self):
        """搜索文本变化"""
        QTimer.singleShot(300, self._fill_plugin_table)
        
    def _on_category_changed(self):
        """分类变化"""
        self._fill_plugin_table()
        
    def _hide_operation_panel(self):
        """隐藏操作面板"""
        self.operation_panel.setVisible(False)
