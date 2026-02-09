# -*- coding: utf-8 -*-

"""
主窗口实现
负责整体布局和功能模块间的协调
"""

import os
import logging
from PyQt5.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
                           QSplitter, QMenuBar, QMenu, QAction, QStatusBar,
                           QMessageBox)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QSettings
from PyQt5.QtGui import QIcon, QKeySequence, QFont

from .plugin_manager import PluginManager
from .navigation import NavigationPanel
from .workspace import Workspace
from .updater import AutoUpdater

logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    """
    主窗口类
    
    负责整体布局管理和功能模块间的协调
    """
    
    def __init__(self):
        """初始化主窗口"""
        super().__init__()
        
        # 窗口设置
        self.setWindowTitle("PyQt工作工具")
        self.setMinimumSize(1000, 700)
        
        # 核心组件
        self.plugin_manager = PluginManager(self)
        self.navigation_panel = NavigationPanel()
        self.workspace = Workspace()
        
        # 设置
        self.settings = QSettings("WorkTools", "PyQtWorkTools")
        
        # 自动更新管理器
        self.auto_updater = AutoUpdater(self)
        
        # 设置UI
        self._setup_ui()
        self._setup_menu()
        self._setup_status_bar()
        self._connect_signals()
        
        # 加载插件
        self._load_plugins()
        
    def _setup_ui(self):
        """设置用户界面"""
        # 创建中央控件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # 添加导航面板和工作区
        splitter.addWidget(self.navigation_panel)
        splitter.addWidget(self.workspace)
        
        # 设置分割比例 (左侧20%，右侧80%)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 4)
        
        # 设置导航面板宽度
        self.navigation_panel.setMaximumWidth(300)
        self.navigation_panel.setMinimumWidth(200)
        
    def _setup_menu(self):
        """设置菜单栏"""
        menubar = self.menuBar()
        
        # 帮助菜单
        help_menu = menubar.addMenu("帮助(&H)")
        
        # 检查更新动作
        check_update_action = QAction("检查更新(&U)", self)
        check_update_action.setStatusTip("检查是否有新版本")
        check_update_action.triggered.connect(self._check_update)
        help_menu.addAction(check_update_action)
        
        help_menu.addSeparator()
        
        # 关于动作
        about_action = QAction("关于(&A)", self)
        about_action.setStatusTip("显示关于信息")
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
        
    def _setup_status_bar(self):
        """设置状态栏"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # 添加永久消息
        self.status_bar.showMessage("就绪")
        
    def _connect_signals(self):
        """连接信号和槽"""
        # 导航面板选择插件信号
        self.navigation_panel.plugin_selected.connect(self._on_plugin_selected)
        
        # 插件管理器信号
        self.plugin_manager.plugin_loaded.connect(self._on_plugin_loaded)
        self.plugin_manager.plugin_activated.connect(self._on_plugin_activated)
        self.plugin_manager.plugin_deactivated.connect(self._on_plugin_deactivated)
        self.plugin_manager.plugin_error.connect(self._on_plugin_error)
        
        # 工作区信号
        self.workspace.plugin_changed.connect(self._on_workspace_plugin_changed)
        
    def _load_plugins(self):
        """加载插件"""
        from .plugins.plugin_manager_tool import get_user_plugins_dir

        # 获取用户插件目录
        user_plugin_dir = get_user_plugins_dir()
        current_dir = os.path.dirname(os.path.abspath(__file__))
        dev_plugin_dir = os.path.join(current_dir, "plugins")

        # 清空现有插件
        self.plugin_manager.clear_plugins()

        # 从两个目录加载插件
        # 1. 先从开发目录加载（包含plugin_manager_tool.py等内置插件）
        if os.path.exists(dev_plugin_dir):
            logger.info(f"从开发目录加载插件: {dev_plugin_dir}")
            self.plugin_manager.load_plugins(dev_plugin_dir)

        # 2. 再从用户目录加载（用户下载的插件）
        if os.path.exists(user_plugin_dir):
            logger.info(f"从用户目录加载插件: {user_plugin_dir}")
            self.plugin_manager.load_plugins(user_plugin_dir)

        # 清空工作区
        self.workspace.clear_plugins()

        # 更新导航面板
        plugins = self.plugin_manager.get_all_plugins()
        plugin_categories = self.plugin_manager.get_plugin_categories()
        self.navigation_panel.update_plugins(plugins, plugin_categories)

        # 将插件添加到工作区
        for plugin_name, plugin in plugins.items():
            self.workspace.add_plugin(plugin_name, plugin)

        # 如果有默认插件，激活它
        if plugins:
            first_plugin_name = next(iter(plugins.keys()))
            self.activate_plugin(first_plugin_name)
            
    def _on_plugin_selected(self, plugin_name: str):
        """
        处理插件选择事件
        
        Args:
            plugin_name: 选择的插件名
        """
        self.activate_plugin(plugin_name)
        
    def _on_plugin_loaded(self, plugin_name: str):
        """
        处理插件加载事件
        
        Args:
            plugin_name: 插件名
        """
        self.status_bar.showMessage(f"插件 {plugin_name} 已加载", 3000)
        
    def _on_plugin_activated(self, plugin_name: str):
        """
        处理插件激活事件
        
        Args:
            plugin_name: 插件名
        """
        self.status_bar.showMessage(f"插件 {plugin_name} 已激活", 3000)
        
    def _on_plugin_deactivated(self, plugin_name: str):
        """
        处理插件停用事件
        
        Args:
            plugin_name: 插件名
        """
        self.status_bar.showMessage(f"插件 {plugin_name} 已停用", 3000)
        
    def _on_plugin_error(self, plugin_name: str, error_msg: str):
        """
        处理插件错误事件
        
        Args:
            plugin_name: 插件名
            error_msg: 错误信息
        """
        self.status_bar.showMessage(f"插件 {plugin_name} 错误: {error_msg}", 5000)
        
    def _on_workspace_plugin_changed(self, plugin_name: str):
        """
        处理工作区插件变化事件
        
        Args:
            plugin_name: 新的插件名
        """
        # 更新导航面板的选中状态
        self.navigation_panel.set_active_plugin(plugin_name)
        
        # 激活插件
        self.plugin_manager.activate_plugin(plugin_name)
        
    def activate_plugin(self, plugin_name: str) -> bool:
        """
        激活指定插件
        
        Args:
            plugin_name: 插件名
            
        Returns:
            是否成功激活
        """
        # 激活插件
        if not self.plugin_manager.activate_plugin(plugin_name):
            return False
            
        # 在工作区显示插件
        if not self.workspace.show_plugin(plugin_name):
            return False
            
        # 更新导航面板选中状态
        self.navigation_panel.set_active_plugin(plugin_name)
        
        return True
        
    def _show_about(self):
        """显示关于对话框"""
        QMessageBox.about(
            self,
            "关于",
            "WorkTools v1.0.9\n\n"
            "一个基于PyQt的模块化工作工具集合\n"
            "支持插件式架构，可动态扩展功能\n\n"
            "当前功能模块：\n"
            "• 文本处理工具\n"
            "• 文件管理器\n"
            "• 系统工具\n"
            "• 月汇总工具\n"
            "• Excel合并工具\n"
            "• Excel去重工具\n"
            "• 图片水印工具"
        )

    def _check_update(self):
        """检查更新"""
        self.status_bar.showMessage("正在检查更新...", 3000)
        self.auto_updater.check_update(silent=False)
        
    def closeEvent(self, event):
        """窗口关闭事件"""
        # 清理更新线程
        if hasattr(self, 'auto_updater') and self.auto_updater:
            self.auto_updater.cleanup()
        
        # 停用所有插件
        self.plugin_manager.deactivate_plugin(
            self.plugin_manager.get_active_plugin_name())
            
        # 接受关闭事件
        event.accept()
        
        logger.info("应用程序关闭")