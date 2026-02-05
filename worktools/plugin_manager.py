# -*- coding: utf-8 -*-

"""
插件管理器
负责加载、管理和协调所有功能插件
"""

import os
import importlib
import inspect
import logging
from typing import Dict, List, Optional, Type
from PyQt5.QtCore import QObject, pyqtSignal

from .base_plugin import BasePlugin

logger = logging.getLogger(__name__)

class PluginManager(QObject):
    """
    插件管理器
    
    负责插件的加载、注册、激活和停用
    """
    
    # 信号定义
    plugin_loaded = pyqtSignal(str)  # 插件加载完成
    plugin_activated = pyqtSignal(str)  # 插件被激活
    plugin_deactivated = pyqtSignal(str)  # 插件被停用
    plugin_error = pyqtSignal(str, str)  # 插件错误，参数：插件名，错误信息
    
    def __init__(self, parent=None):
        """
        初始化插件管理器
        
        Args:
            parent: 父对象
        """
        super().__init__(parent)
        self._plugins: Dict[str, BasePlugin] = {}  # 插件名到插件实例的映射
        self._active_plugin: Optional[str] = None  # 当前激活的插件名
        self._plugin_categories: Dict[str, List[str]] = {}  # 分类到插件名的映射
        
    def load_plugins(self, plugin_directory: str):
        """
        从指定目录加载插件
        
        Args:
            plugin_directory: 插件目录路径
        """
        if not os.path.exists(plugin_directory):
            logger.warning(f"插件目录不存在: {plugin_directory}")
            return
            
        logger.info(f"开始加载插件，目录: {plugin_directory}")
        
        # 确保插件目录在Python路径中
        if plugin_directory not in os.sys.path:
            os.sys.path.insert(0, plugin_directory)
            
        # 扫描插件目录中的Python文件
        for filename in os.listdir(plugin_directory):
            if filename.endswith('.py') and not filename.startswith('__'):
                module_name = filename[:-3]  # 去掉.py后缀
                try:
                    self._load_plugin_module(module_name, plugin_directory)
                except Exception as e:
                    logger.error(f"加载插件模块 {module_name} 失败: {str(e)}")
                    self.plugin_error.emit(module_name, str(e))
                    
        logger.info(f"插件加载完成，共加载 {len(self._plugins)} 个插件")
        
    def _load_plugin_module(self, module_name: str, plugin_directory: str):
        """
        加载单个插件模块
        
        Args:
            module_name: 模块名称
            plugin_directory: 插件目录
        """
        # 导入模块
        module = importlib.import_module(module_name)
        
        # 查找模块中的插件类
        for name, obj in inspect.getmembers(module):
            if (inspect.isclass(obj) and 
                issubclass(obj, BasePlugin) and 
                obj != BasePlugin):
                
                # 创建插件实例
                plugin_instance = obj()
                plugin_name = plugin_instance.get_name()
                
                # 注册插件
                self._plugins[plugin_name] = plugin_instance
                
                # 按分类组织插件
                category = plugin_instance.get_category()
                if category not in self._plugin_categories:
                    self._plugin_categories[category] = []
                self._plugin_categories[category].append(plugin_name)
                
                # 初始化插件
                try:
                    plugin_instance.initialize()
                    logger.info(f"插件 {plugin_name} 加载成功")
                    self.plugin_loaded.emit(plugin_name)
                except Exception as e:
                    logger.error(f"初始化插件 {plugin_name} 失败: {str(e)}")
                    self.plugin_error.emit(plugin_name, str(e))
                
                break  # 每个模块只处理一个插件类
                
    def register_plugin(self, plugin: BasePlugin):
        """
        直接注册插件实例
        
        Args:
            plugin: 插件实例
        """
        plugin_name = plugin.get_name()
        self._plugins[plugin_name] = plugin
        
        # 按分类组织插件
        category = plugin.get_category()
        if category not in self._plugin_categories:
            self._plugin_categories[category] = []
        self._plugin_categories[category].append(plugin_name)
        
        # 初始化插件
        try:
            plugin.initialize()
            logger.info(f"插件 {plugin_name} 注册成功")
            self.plugin_loaded.emit(plugin_name)
        except Exception as e:
            logger.error(f"初始化插件 {plugin_name} 失败: {str(e)}")
            self.plugin_error.emit(plugin_name, str(e))
        
    def get_plugin(self, name: str) -> Optional[BasePlugin]:
        """
        获取插件实例
        
        Args:
            name: 插件名称
            
        Returns:
            插件实例，如果不存在则返回None
        """
        return self._plugins.get(name)
        
    def get_all_plugins(self) -> Dict[str, BasePlugin]:
        """
        获取所有已加载的插件
        
        Returns:
            插件名到插件实例的映射
        """
        return self._plugins.copy()
        
    def get_plugin_categories(self) -> Dict[str, List[str]]:
        """
        获取插件分类
        
        Returns:
            分类名到插件名列表的映射
        """
        return self._plugin_categories.copy()
        
    def activate_plugin(self, name: str) -> bool:
        """
        激活指定插件
        
        Args:
            name: 插件名称
            
        Returns:
            是否成功激活
        """
        if name not in self._plugins:
            logger.warning(f"尝试激活不存在的插件: {name}")
            return False
            
        # 如果已有插件处于激活状态，先停用它
        if self._active_plugin and self._active_plugin != name:
            self.deactivate_plugin(self._active_plugin)
            
        # 激活新插件
        try:
            plugin = self._plugins[name]
            plugin.on_activate()
            self._active_plugin = name
            logger.info(f"插件 {name} 已激活")
            self.plugin_activated.emit(name)
            return True
        except Exception as e:
            logger.error(f"激活插件 {name} 失败: {str(e)}")
            self.plugin_error.emit(name, str(e))
            return False
            
    def deactivate_plugin(self, name: str) -> bool:
        """
        停用指定插件
        
        Args:
            name: 插件名称
            
        Returns:
            是否成功停用
        """
        if name not in self._plugins:
            logger.warning(f"尝试停用不存在的插件: {name}")
            return False
            
        if self._active_plugin != name:
            logger.warning(f"插件 {name} 当前未处于激活状态")
            return False
            
        try:
            plugin = self._plugins[name]
            plugin.on_deactivate()
            self._active_plugin = None
            logger.info(f"插件 {name} 已停用")
            self.plugin_deactivated.emit(name)
            return True
        except Exception as e:
            logger.error(f"停用插件 {name} 失败: {str(e)}")
            self.plugin_error.emit(name, str(e))
            return False
            
    def get_active_plugin(self) -> Optional[BasePlugin]:
        """
        获取当前激活的插件
        
        Returns:
            当前激活的插件实例，如果没有则返回None
        """
        if self._active_plugin:
            return self._plugins.get(self._active_plugin)
        return None
        
    def get_active_plugin_name(self) -> Optional[str]:
        """
        获取当前激活的插件名称
        
        Returns:
            当前激活的插件名称，如果没有则返回None
        """
        return self._active_plugin
        
    def save_all_plugin_states(self) -> Dict[str, Dict]:
        """
        保存所有插件的状态
        
        Returns:
            插件名到状态数据的映射
        """
        states = {}
        for name, plugin in self._plugins.items():
            try:
                states[name] = plugin.save_state()
            except Exception as e:
                logger.error(f"保存插件 {name} 状态失败: {str(e)}")
                
        return states
        
    def restore_all_plugin_states(self, states: Dict[str, Dict]):
        """
        恢复所有插件的状态
        
        Args:
            states: 插件名到状态数据的映射
        """
        for name, state in states.items():
            if name in self._plugins:
                try:
                    self._plugins[name].restore_state(state)
                except Exception as e:
                    logger.error(f"恢复插件 {name} 状态失败: {str(e)}")