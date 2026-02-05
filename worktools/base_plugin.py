# -*- coding: utf-8 -*-

"""
插件基类定义
所有功能插件都应该继承自此类
"""

from abc import ABC, abstractmethod
from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QObject
from typing import Dict, Any, Optional

class BasePlugin(QWidget):
    """
    所有功能插件的基础类
    
    定义了插件的标准接口，包括初始化、激活、停用等生命周期方法
    """
    
    def __init__(self, parent=None):
        """
        初始化插件
        
        Args:
            parent: 父控件
        """
        super().__init__(parent)
        self._name = ""
        self._description = ""
        self._icon = None
        self._initialized = False
        
    def get_name(self) -> str:
        """
        返回插件显示名称
        
        Returns:
            插件名称
        """
        raise NotImplementedError
        
    def get_description(self) -> str:
        """
        返回插件描述信息
        
        Returns:
            插件描述
        """
        raise NotImplementedError
        
    def get_icon(self) -> QIcon:
        """
        返回插件图标
        
        Returns:
            插件图标
        """
        raise NotImplementedError
        
    def initialize(self):
        """
        插件初始化
        在插件首次加载时调用，用于加载资源、连接信号等
        """
        if not self._initialized:
            self._setup_ui()
            self._connect_signals()
            self._initialized = True
            
    def is_initialized(self) -> bool:
        """检查插件是否已初始化"""
        return self._initialized
        
    def on_activate(self):
        """
        当插件被激活时调用
        当用户从导航面板选择该插件时触发
        """
        pass
        
    def on_deactivate(self):
        """
        当插件被停用时调用
        当用户切换到其他插件时触发
        """
        pass
        
    def save_state(self) -> Dict[str, Any]:
        """
        保存插件状态
        
        Returns:
            包含插件状态的字典
        """
        return {}
        
    def restore_state(self, state: Dict[str, Any]):
        """
        恢复插件状态
        
        Args:
            state: 包含插件状态的字典
        """
        pass
        
    def get_settings_widget(self) -> Optional[QWidget]:
        """
        返回插件设置界面（可选）
        
        Returns:
            设置界面控件，如果插件没有设置选项则返回None
        """
        return None
        
    def _setup_ui(self):
        """
        设置用户界面
        子类可以重写此方法来创建自定义UI
        """
        pass
        
    def _connect_signals(self):
        """
        连接信号和槽
        子类可以重写此方法来连接自定义信号
        """
        pass
        
    def get_shortcut(self) -> Optional[str]:
        """
        返回插件快捷键（可选）
        
        Returns:
            快捷键字符串，如 "Ctrl+T"，如果无快捷键则返回None
        """
        return None
        
    def get_category(self) -> str:
        """
        返回插件所属分类
        
        Returns:
            分类名称，默认为"其他"
        """
        return "其他"
        
    def get_version(self) -> str:
        """
        返回插件版本
        
        Returns:
            版本号，默认为"1.0.0"
        """
        return "1.0.0"
        
    def is_enabled(self) -> bool:
        """
        检查插件是否已启用
        
        Returns:
            是否已启用，默认为True
        """
        return True
        
    def set_enabled(self, enabled: bool):
        """
        设置插件启用状态
        
        Args:
            enabled: 是否启用
        """
        # 子类可以重写此方法来处理启用状态变化
        pass