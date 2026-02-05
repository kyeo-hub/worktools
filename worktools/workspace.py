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
        main_layout.addWidget(self.stacked_widget)
        
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
            # 切换到指定插件
            plugin_info = self._plugins[plugin_name]
            self.stacked_widget.setCurrentIndex(plugin_info['index'])
            
            # 更新标题栏
            self.title_label.setText(plugin_name)
            
            # 检查插件是否有设置界面
            plugin = plugin_info['widget']
            if hasattr(plugin, 'get_settings_widget') and callable(plugin.get_settings_widget):
                self.settings_button.setEnabled(True)
            else:
                self.settings_button.setEnabled(False)
                
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
            if plugin and hasattr(plugin, 'get_settings_widget') and callable(plugin.get_settings_widget):
                settings_widget = plugin.get_settings_widget()
                if settings_widget:
                    # 这里可以创建一个对话框显示设置界面
                    # 为了简化，暂时只打印日志
                    logger.info(f"显示插件 {self._current_plugin} 的设置界面")
        except Exception as e:
            logger.error(f"显示插件 {self._current_plugin} 设置界面失败: {str(e)}")