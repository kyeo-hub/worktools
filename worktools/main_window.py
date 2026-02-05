# -*- coding: utf-8 -*-

"""
主窗口实现
负责整体布局和功能模块间的协调
"""

import os
import json
import logging
from typing import Dict, Optional
from PyQt5.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
                           QSplitter, QMenuBar, QMenu, QAction, QStatusBar,
                           QMessageBox, QFileDialog, QToolBar)
from PyQt5.QtCore import Qt, QSize, QTimer, pyqtSignal, QSettings
from PyQt5.QtGui import QIcon, QKeySequence, QFont

from .plugin_manager import PluginManager
from .navigation import NavigationPanel
from .workspace import Workspace
from .api_settings_dialog import APISettingsDialog
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
        
        # 恢复窗口状态
        self._restore_state()
        
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
        
        # 文件菜单
        file_menu = menubar.addMenu("文件(&F)")
        
        # 保存状态动作
        save_state_action = QAction("保存状态(&S)", self)
        save_state_action.setShortcut(QKeySequence("Ctrl+S"))
        save_state_action.setStatusTip("保存当前应用状态")
        save_state_action.triggered.connect(self._save_state)
        file_menu.addAction(save_state_action)
        
        # 恢复状态动作
        restore_state_action = QAction("恢复状态(&R)", self)
        restore_state_action.setShortcut(QKeySequence("Ctrl+R"))
        restore_state_action.setStatusTip("恢复上次保存的应用状态")
        restore_state_action.triggered.connect(self._restore_saved_state)
        file_menu.addAction(restore_state_action)
        
        file_menu.addSeparator()
        
        # 退出动作
        exit_action = QAction("退出(&X)", self)
        exit_action.setShortcut(QKeySequence("Ctrl+Q"))
        exit_action.setStatusTip("退出应用程序")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 视图菜单
        view_menu = menubar.addMenu("视图(&V)")
        
        # 切换主题动作
        toggle_theme_action = QAction("切换主题(&T)", self)
        toggle_theme_action.setStatusTip("切换应用主题")
        toggle_theme_action.triggered.connect(self._toggle_theme)
        view_menu.addAction(toggle_theme_action)
        
        # 重置布局动作
        reset_layout_action = QAction("重置布局(&L)", self)
        reset_layout_action.setStatusTip("重置窗口布局")
        reset_layout_action.triggered.connect(self._reset_layout)
        view_menu.addAction(reset_layout_action)
        
        # 工具菜单
        tools_menu = menubar.addMenu("工具(&T)")
        
        # 重新加载插件动作
        reload_plugins_action = QAction("重新加载插件(&R)", self)
        reload_plugins_action.setStatusTip("重新加载所有插件")
        reload_plugins_action.triggered.connect(self._reload_plugins)
        tools_menu.addAction(reload_plugins_action)
        
        # 设置菜单
        settings_menu = menubar.addMenu("设置(&S)")
        
        # API配置动作
        api_settings_action = QAction("API配置(&A)...", self)
        api_settings_action.setStatusTip("配置百度/高德地图API Key")
        api_settings_action.triggered.connect(self._show_api_settings)
        settings_menu.addAction(api_settings_action)
        
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
        # 获取插件目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        plugin_dir = os.path.join(current_dir, "plugins")
        
        # 加载插件
        self.plugin_manager.load_plugins(plugin_dir)
        
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
        
    def _save_state(self):
        """保存应用状态"""
        try:
            # 保存窗口状态
            self.settings.setValue("geometry", self.saveGeometry())
            self.settings.setValue("windowState", self.saveState())
            
            # 保存插件状态
            plugin_states = self.plugin_manager.save_all_plugin_states()
            self.settings.setValue("pluginStates", json.dumps(plugin_states))
            
            # 保存当前激活的插件
            current_plugin = self.plugin_manager.get_active_plugin_name()
            if current_plugin:
                self.settings.setValue("currentPlugin", current_plugin)
                
            self.status_bar.showMessage("状态已保存", 3000)
            logger.info("应用状态已保存")
        except Exception as e:
            logger.error(f"保存状态失败: {str(e)}")
            QMessageBox.warning(self, "保存失败", f"保存状态时发生错误: {str(e)}")
            
    def _restore_state(self):
        """恢复应用状态"""
        try:
            # 恢复窗口状态
            geometry = self.settings.value("geometry")
            if geometry:
                self.restoreGeometry(geometry)
                
            window_state = self.settings.value("windowState")
            if window_state:
                self.restoreState(window_state)
                
            # 恢复插件状态
            plugin_states_json = self.settings.value("pluginStates")
            if plugin_states_json:
                plugin_states = json.loads(plugin_states_json)
                self.plugin_manager.restore_all_plugin_states(plugin_states)
                
            # 恢复当前激活的插件
            current_plugin = self.settings.value("currentPlugin")
            if current_plugin:
                QTimer.singleShot(100, lambda: self.activate_plugin(current_plugin))
                
            logger.info("应用状态已恢复")
        except Exception as e:
            logger.error(f"恢复状态失败: {str(e)}")
            
    def _restore_saved_state(self):
        """从文件恢复保存的状态"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择状态文件", "", "JSON文件 (*.json)")
        if not file_path:
            return
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                state_data = json.load(f)
                
            # 恢复插件状态
            if "pluginStates" in state_data:
                self.plugin_manager.restore_all_plugin_states(state_data["pluginStates"])
                
            # 恢复当前激活的插件
            if "currentPlugin" in state_data:
                self.activate_plugin(state_data["currentPlugin"])
                
            self.status_bar.showMessage("状态已恢复", 3000)
            logger.info(f"从文件 {file_path} 恢复状态")
        except Exception as e:
            logger.error(f"从文件恢复状态失败: {str(e)}")
            QMessageBox.warning(self, "恢复失败", f"从文件恢复状态时发生错误: {str(e)}")
            
    def _toggle_theme(self):
        """切换主题"""
        # 这里可以实现主题切换逻辑
        self.status_bar.showMessage("主题切换功能待实现", 3000)
        
    def _reset_layout(self):
        """重置布局"""
        # 重置窗口大小和位置
        self.resize(1000, 700)
        self.move(100, 100)
        
        # 重置分割器比例
        central_widget = self.centralWidget()
        if isinstance(central_widget, QWidget):
            splitter = central_widget.findChild(QSplitter)
            if splitter:
                splitter.setSizes([200, 800])
                
        self.status_bar.showMessage("布局已重置", 3000)
        
    def _reload_plugins(self):
        """重新加载插件"""
        # 清除当前插件
        self.plugin_manager = PluginManager(self)
        self.workspace = Workspace()
        
        # 重新连接信号
        self._connect_signals()
        
        # 重新加载插件
        self._load_plugins()
        
        # 更新中央控件
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        splitter.addWidget(self.navigation_panel)
        splitter.addWidget(self.workspace)
        
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 4)
        
        self.setCentralWidget(central_widget)
        
        self.status_bar.showMessage("插件已重新加载", 3000)
        
    def _show_about(self):
        """显示关于对话框"""
        QMessageBox.about(
            self,
            "关于",
            "PyQt工作工具 v0.1.0\n\n"
            "一个基于PyQt的模块化工作工具集合\n"
            "支持插件式架构，可动态扩展功能"
        )

    def _check_update(self):
        """检查更新"""
        self.status_bar.showMessage("正在检查更新...", 3000)
        self.auto_updater.check_update(silent=False)

    def _show_api_settings(self):
        """显示API设置对话框"""
        dialog = APISettingsDialog(self)
        dialog.exec_()
        
    def closeEvent(self, event):
        """窗口关闭事件"""
        # 保存状态
        self._save_state()
        
        # 清理更新线程
        if hasattr(self, 'auto_updater') and self.auto_updater:
            self.auto_updater.cleanup()
        
        # 停用所有插件
        self.plugin_manager.deactivate_plugin(
            self.plugin_manager.get_active_plugin_name())
            
        # 接受关闭事件
        event.accept()
        
        logger.info("应用程序关闭")