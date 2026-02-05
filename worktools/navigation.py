# -*- coding: utf-8 -*-

"""
导航面板
显示功能列表并处理功能切换
"""

import logging
from typing import Dict, List
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, 
                           QTreeWidgetItem, QLineEdit, QPushButton, QLabel,
                           QFrame, QScrollArea, QButtonGroup, QStackedLayout)
from PyQt5.QtCore import Qt, QSize, pyqtSignal
from PyQt5.QtGui import QIcon, QFont, QPalette, QColor

logger = logging.getLogger(__name__)

class NavigationPanel(QWidget):
    """
    导航面板类
    
    提供功能插件的导航界面，支持分类显示和搜索
    """
    
    # 信号定义
    plugin_selected = pyqtSignal(str)  # 插件被选中
    
    def __init__(self, parent=None):
        """
        初始化导航面板
        
        Args:
            parent: 父控件
        """
        super().__init__(parent)
        self._plugin_items: Dict[str, QTreeWidgetItem] = {}  # 插件名到树项的映射
        self._plugin_categories: Dict[str, List[str]] = {}  # 插件分类
        self._current_plugin: str = ""  # 当前选中的插件
        
        self._setup_ui()
        self._connect_signals()
        
    def _setup_ui(self):
        """设置用户界面"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        # 标题
        title_label = QLabel("功能导航")
        title_label.setAlignment(Qt.AlignCenter)
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(12)
        title_label.setFont(title_font)
        main_layout.addWidget(title_label)
        
        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(line)
        
        # 搜索框
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("搜索功能...")
        main_layout.addWidget(self.search_box)
        
        # 功能树
        self.plugin_tree = QTreeWidget()
        self.plugin_tree.setHeaderHidden(True)
        self.plugin_tree.setIndentation(15)
        main_layout.addWidget(self.plugin_tree)
        
    def _connect_signals(self):
        """连接信号和槽"""
        self.plugin_tree.itemClicked.connect(self._on_item_clicked)
        self.search_box.textChanged.connect(self._on_search_text_changed)
        
    def _on_item_clicked(self, item: QTreeWidgetItem, column: int):
        """
        处理树项点击事件
        
        Args:
            item: 被点击的树项
            column: 列索引
        """
        # 检查是否为插件项（不是分类项）
        item_data = item.data(0, Qt.UserRole)
        if item_data and isinstance(item_data, str):
            plugin_name = item_data
            self._select_plugin(plugin_name)
            
    def _on_search_text_changed(self, text: str):
        """
        处理搜索文本变化事件
        
        Args:
            text: 搜索文本
        """
        search_text = text.lower().strip()
        
        # 如果搜索框为空，显示所有项
        if not search_text:
            self._show_all_items()
            return
            
        # 隐藏所有分类和插件
        self._hide_all_items()
        
        # 搜索匹配的插件
        matching_plugins = []
        for plugin_name, item in self._plugin_items.items():
            if search_text in plugin_name.lower():
                matching_plugins.append(plugin_name)
                
        # 显示匹配的插件及其父分类
        for plugin_name in matching_plugins:
            item = self._plugin_items[plugin_name]
            item.setHidden(False)
            
            # 显示父分类
            parent = item.parent()
            while parent:
                parent.setHidden(False)
                parent.setExpanded(True)
                parent = parent.parent()
                
    def _hide_all_items(self):
        """隐藏所有项"""
        root = self.plugin_tree.invisibleRootItem()
        for i in range(root.childCount()):
            category_item = root.child(i)
            category_item.setHidden(True)
            
            for j in range(category_item.childCount()):
                plugin_item = category_item.child(j)
                plugin_item.setHidden(True)
                
    def _show_all_items(self):
        """显示所有项"""
        root = self.plugin_tree.invisibleRootItem()
        for i in range(root.childCount()):
            category_item = root.child(i)
            category_item.setHidden(False)
            
            for j in range(category_item.childCount()):
                plugin_item = category_item.child(j)
                plugin_item.setHidden(False)
                
    def _select_plugin(self, plugin_name: str):
        """
        选择指定的插件
        
        Args:
            plugin_name: 插件名称
        """
        if plugin_name == self._current_plugin:
            return  # 已经是当前插件，无需重复选择
            
        # 更新当前选中状态
        self._update_selection_state(plugin_name)
        
        # 发送插件选中信号
        self._current_plugin = plugin_name
        self.plugin_selected.emit(plugin_name)
        
    def _update_selection_state(self, plugin_name: str):
        """
        更新选中状态
        
        Args:
            plugin_name: 被选中的插件名
        """
        # 清除所有插件项的选中状态
        for item in self._plugin_items.values():
            item.setData(0, Qt.BackgroundRole, QColor(240, 240, 240))
            
        # 设置新选中插件项的背景色
        if plugin_name in self._plugin_items:
            item = self._plugin_items[plugin_name]
            item.setData(0, Qt.BackgroundRole, QColor(200, 220, 255))
            
    def update_plugins(self, plugins: Dict[str, object], plugin_categories: Dict[str, List[str]]):
        """
        更新插件列表
        
        Args:
            plugins: 插件名到插件实例的映射
            plugin_categories: 插件分类
        """
        # 清空现有内容
        self.plugin_tree.clear()
        self._plugin_items.clear()
        self._plugin_categories = plugin_categories.copy()
        
        # 按分类添加插件
        for category, plugin_names in plugin_categories.items():
            # 创建分类项
            category_item = QTreeWidgetItem(self.plugin_tree)
            category_item.setText(0, category)
            category_item.setExpanded(True)
            
            # 设置分类项字体
            font = category_item.font(0)
            font.setBold(True)
            category_item.setFont(0, font)
            
            # 添加该分类下的所有插件
            for plugin_name in plugin_names:
                if plugin_name in plugins:
                    plugin = plugins[plugin_name]
                    
                    # 创建插件项
                    plugin_item = QTreeWidgetItem(category_item)
                    plugin_item.setText(0, plugin_name)
                    
                    # 设置插件图标
                    try:
                        icon = plugin.get_icon()
                        if icon:
                            plugin_item.setIcon(0, icon)
                    except Exception as e:
                        logger.warning(f"获取插件 {plugin_name} 图标失败: {str(e)}")
                    
                    # 存储插件名
                    plugin_item.setData(0, Qt.UserRole, plugin_name)
                    
                    # 保存引用
                    self._plugin_items[plugin_name] = plugin_item
                    
        # 设置当前选中插件
        if self._current_plugin and self._current_plugin in self._plugin_items:
            self._update_selection_state(self._current_plugin)
            
    def set_active_plugin(self, plugin_name: str):
        """
        设置当前激活的插件
        
        Args:
            plugin_name: 插件名称
        """
        if plugin_name != self._current_plugin:
            self._current_plugin = plugin_name
            self._update_selection_state(plugin_name)
            
    def get_current_plugin(self) -> str:
        """
        获取当前选中的插件
        
        Returns:
            当前选中的插件名称
        """
        return self._current_plugin