# -*- coding: utf-8 -*-

"""
工作区管理
管理功能插件界面的显示和切换
"""

import logging
from typing import Dict, Optional
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget, 
                           QLabel, QFrame, QPushButton, QScrollArea)
from PyQt5.QtCore import Qt, QSize, pyqtSignal
from PyQt5.QtGui import QFont, QPalette, QColor

logger = logging.getLogger(__name__)

class Workspace(QWidget):
    """
    工作区类
    
    负责管理功能插件界面的显示和切换
    """
    
    # 信号定义
    plugin_changed = pyqtSignal(str)  # 插件切换
    plugin_state_changed = pyqtSignal(str, dict)  # 插件状态变化
    
    def __init__(self, parent=None):
        """
        初始化工作区
        
        Args:
            parent: 父控件
        """
        super().__init__(parent)
        self._plugins: Dict[str, QWidget] = {}  # 插件名到插件实例的映射
        self._current_plugin: Optional[str] = None  # 当前显示的插件
        
        self._setup_ui()
        
    def _setup_ui(self):
        """设置用户界面"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        # 标题栏
        self._setup_title_bar(main_layout)
        
        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(line)
        
        # 插件显示区域
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setMinimumHeight(400)  # 设置最小高度
        main_layout.addWidget(self.stacked_widget, 1)  # 添加拉伸因子
        
        # 初始状态显示
        self._show_empty_state()
        
    def _setup_title_bar(self, parent_layout: QVBoxLayout):
        """设置标题栏"""
        title_layout = QHBoxLayout()
        
        # 当前功能标题
        self.title_label = QLabel("请选择功能")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(14)
        self.title_label.setFont(title_font)
        title_layout.addWidget(self.title_label)
        
        # 弹性空间
        title_layout.addStretch()
        
        # 设置按钮（如果有设置界面）
        self.settings_button = QPushButton("设置")
        self.settings_button.setEnabled(False)
        self.settings_button.clicked.connect(self._show_plugin_settings)
        title_layout.addWidget(self.settings_button)
        
        parent_layout.addLayout(title_layout)
        
    def _show_empty_state(self):
        """显示空状态"""
        empty_widget = QWidget()
        empty_layout = QVBoxLayout(empty_widget)
        empty_layout.setAlignment(Qt.AlignCenter)
        
        empty_label = QLabel("请从左侧导航面板选择功能")
        empty_label.setAlignment(Qt.AlignCenter)
        empty_font = QFont()
        empty_font.setPointSize(16)
        empty_label.setFont(empty_font)
        empty_layout.addWidget(empty_label)
        
        # 添加空状态到堆栈控件
        self.stacked_widget.addWidget(empty_widget)
        self.empty_index = self.stacked_widget.count() - 1
        
    def add_plugin(self, plugin_name: str, plugin_widget: QWidget):
        """
        添加插件到工作区
        
        Args:
            plugin_name: 插件名称
            plugin_widget: 插件实例
        """
        if plugin_name in self._plugins:
            logger.warning(f"插件 {plugin_name} 已存在，将被替换")
            self.remove_plugin(plugin_name)
            
        # 添加插件到堆栈控件
        index = self.stacked_widget.addWidget(plugin_widget)
        
        # 保存插件信息
        self._plugins[plugin_name] = {
            'widget': plugin_widget,
            'index': index
        }
        
        logger.info(f"插件 {plugin_name} 已添加到工作区")
        
    def remove_plugin(self, plugin_name: str):
        """
        从工作区移除插件

        Args:
            plugin_name: 插件名称
        """
        if plugin_name not in self._plugins:
            logger.warning(f"尝试移除不存在的插件: {plugin_name}")
            return

        # 从堆栈控件中移除
        plugin_info = self._plugins[plugin_name]
        self.stacked_widget.removeWidget(plugin_info['widget'])

        # 如果是当前插件，切换到空状态
        if self._current_plugin == plugin_name:
            self._current_plugin = None
            self.stacked_widget.setCurrentIndex(self.empty_index)
            self.title_label.setText("请选择功能")
            self.settings_button.setEnabled(False)

    def clear_plugins(self):
        """清空所有插件"""
        # 移除所有插件控件
        for plugin_name, plugin_info in self._plugins.items():
            self.stacked_widget.removeWidget(plugin_info['widget'])

        # 清空插件字典
        self._plugins.clear()
        self._current_plugin = None

        # 切换到空状态
        self.stacked_widget.setCurrentIndex(self.empty_index)
        self.title_label.setText("请选择功能")
        self.settings_button.setEnabled(False)

        logger.info("工作区插件已清空")
            
        # 从映射中移除
        del self._plugins[plugin_name]
        
        logger.info(f"插件 {plugin_name} 已从工作区移除")
        
    def show_plugin(self, plugin_name: str) -> bool:
        """
        显示指定插件
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            是否成功显示
        """
        if plugin_name not in self._plugins:
            logger.warning(f"尝试显示不存在的插件: {plugin_name}")
            return False
            
        # 如果已经是当前插件，无需切换
        if self._current_plugin == plugin_name:
            return True
            
        try:
            # 停用这个插件
            if self._current_plugin and self._current_plugin in self._plugins:
                old_plugin_widget = self._plugins[self._current_plugin]['widget']
                if hasattr(old_plugin_widget, 'on_deactivate'):
                    old_plugin_widget.on_deactivate()
            
            # 切换到指定插件
            plugin_info = self._plugins[plugin_name]
            self.stacked_widget.setCurrentIndex(plugin_info['index'])
            
            # 更新标题栏
            self.title_label.setText(plugin_name)
            
            # 检查插件是否有设置界面
            plugin = plugin_info['widget']
            if hasattr(plugin, 'has_settings') and callable(plugin.has_settings):
                self.settings_button.setEnabled(plugin.has_settings())
            else:
                self.settings_button.setEnabled(False)
            
            # 调用新插件的 on_activate
            if hasattr(plugin, 'on_activate'):
                plugin.on_activate()
                
            # 更新当前插件
            old_plugin = self._current_plugin
            self._current_plugin = plugin_name
            
            # 发送插件切换信号
            self.plugin_changed.emit(plugin_name)
            
            logger.info(f"工作区切换到插件: {plugin_name}")
            return True
            
        except Exception as e:
            logger.error(f"显示插件 {plugin_name} 失败: {str(e)}")
            return False
            
    def get_current_plugin(self) -> Optional[str]:
        """
        获取当前显示的插件
        
        Returns:
            当前显示的插件名称，如果没有则返回None
        """
        return self._current_plugin
        
    def get_plugin_widget(self, plugin_name: str) -> Optional[QWidget]:
        """
        获取指定插件的控件
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            插件控件，如果不存在则返回None
        """
        if plugin_name in self._plugins:
            return self._plugins[plugin_name]['widget']
        return None
        
    def _show_plugin_settings(self):
        """显示当前插件的设置界面"""
        if not self._current_plugin:
            return
            
        try:
            plugin = self.get_plugin_widget(self._current_plugin)
            if not plugin:
                return
                
            # 优先调用插件的 _show_settings_dialog 方法（如果存在）
            if hasattr(plugin, '_show_settings_dialog') and callable(plugin._show_settings_dialog):
                plugin._show_settings_dialog()
                logger.info(f"显示插件 {self._current_plugin} 的设置对话框")
            # 其次调用 get_settings_widget 方法（如果存在）
            elif hasattr(plugin, 'get_settings_widget') and callable(plugin.get_settings_widget):
                settings_widget = plugin.get_settings_widget()
                if settings_widget:
                    from PyQt5.QtWidgets import QDialog, QVBoxLayout
                    # 创建对话框显示设置界面
                    dialog = QDialog(self)
                    dialog.setWindowTitle(f"{self._current_plugin} 设置")
                    layout = QVBoxLayout(dialog)
                    layout.addWidget(settings_widget)
                    dialog.exec_()
                    logger.info(f"显示插件 {self._current_plugin} 的设置界面")
            else:
                logger.info(f"插件 {self._current_plugin} 没有设置界面")
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.information(self, "设置", f"{self._current_plugin} 暂无设置选项")
        except Exception as e:
            logger.error(f"显示插件 {self._current_plugin} 设置界面失败: {str(e)}")