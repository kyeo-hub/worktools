# -*- coding: utf-8 -*-

"""
主应用类
负责应用程序的初始化和生命周期管理
"""

import sys
import logging
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer, QSettings
from PyQt5.QtGui import QFont

from .main_window import MainWindow

logger = logging.getLogger(__name__)

class WorkToolsApp(QApplication):
    """
    工作工具应用类
    
    继承自QApplication，负责应用程序的整体初始化和生命周期管理
    """
    
    def __init__(self, argv):
        """
        初始化应用
        
        Args:
            argv: 命令行参数
        """
        super().__init__(argv)
        
        # 应用设置
        self.setApplicationName("PyQt工作工具")
        self.setApplicationVersion("0.1.0")
        self.setOrganizationName("WorkTools")
        
        # 设置应用程序样式
        self._setup_style()
        
        # 创建主窗口
        self.main_window = MainWindow()
        
        # 启动时更新检查器引用
        self.startup_updater = None
        
        # 设置异常处理
        self._setup_exception_handling()
        
        # 设置定时器，用于异步任务
        self._setup_timers()
        
        logger.info("工作工具应用初始化完成")
        
    def _setup_style(self):
        """设置应用程序样式"""
        # 设置默认字体
        font = QFont("Microsoft YaHei", 9)
        self.setFont(font)
        
        # 设置应用程序样式表
        style = """
        QMainWindow {
            background-color: #f0f0f0;
        }
        
        QMenuBar {
            background-color: #e0e0e0;
            border-bottom: 1px solid #cccccc;
        }
        
        QMenuBar::item {
            background-color: transparent;
            padding: 4px 8px;
        }
        
        QMenuBar::item:selected {
            background-color: #d0d0d0;
        }
        
        QMenu {
            background-color: #ffffff;
            border: 1px solid #cccccc;
        }
        
        QMenu::item {
            padding: 6px 20px;
        }
        
        QMenu::item:selected {
            background-color: #e0e0e0;
        }
        
        QStatusBar {
            background-color: #e0e0e0;
            border-top: 1px solid #cccccc;
        }
        
        QSplitter::handle {
            background-color: #d0d0d0;
        }
        
        QSplitter::handle:horizontal {
            width: 2px;
        }
        
        QSplitter::handle:vertical {
            height: 2px;
        }
        
        QTreeWidget {
            background-color: #ffffff;
            border: 1px solid #cccccc;
            alternate-background-color: #f8f8f8;
        }
        
        QTreeWidget::item {
            height: 24px;
            border-bottom: 1px solid #f0f0f0;
        }
        
        QTreeWidget::item:selected {
            background-color: #c0d0ff;
        }
        
        QLineEdit {
            background-color: #ffffff;
            border: 1px solid #cccccc;
            border-radius: 3px;
            padding: 2px 5px;
        }
        
        QLineEdit:focus {
            border-color: #4a90e2;
        }
        
        QPushButton {
            background-color: #f0f0f0;
            border: 1px solid #cccccc;
            border-radius: 3px;
            padding: 4px 12px;
        }
        
        QPushButton:hover {
            background-color: #e0e0e0;
        }
        
        QPushButton:pressed {
            background-color: #d0d0d0;
        }
        
        QStackedWidget {
            background-color: #ffffff;
            border: 1px solid #cccccc;
            border-radius: 3px;
        }
        """
        
        self.setStyleSheet(style)
        
    def _setup_exception_handling(self):
        """设置异常处理"""
        def handle_exception(exc_type, exc_value, exc_traceback):
            """全局异常处理"""
            if issubclass(exc_type, KeyboardInterrupt):
                sys.__excepthook__(exc_type, exc_value, exc_traceback)
                return
                
            logger.error(
                "未捕获的异常",
                exc_info=(exc_type, exc_value, exc_traceback)
            )
            
        sys.excepthook = handle_exception
        
    def _setup_timers(self):
        """设置定时器"""
        # 创建一个定时器，用于定期保存状态
        self.auto_save_timer = QTimer()
        self.auto_save_timer.timeout.connect(self._auto_save)
        self.auto_save_timer.start(5 * 60 * 1000)  # 5分钟自动保存一次
        
        # 延迟5秒后检查更新（避免影响启动速度）
        self.update_check_timer = QTimer()
        self.update_check_timer.setSingleShot(True)
        self.update_check_timer.timeout.connect(self._check_update_on_startup)
        self.update_check_timer.start(5000)  # 5秒后检查
        
    def _check_update_on_startup(self):
        """启动时检查更新"""
        try:
            from .updater import AutoUpdater
            # 保存引用以防止垃圾回收
            self.startup_updater = AutoUpdater(self.main_window)
            self.startup_updater.check_update(silent=True)  # 静默检查
        except Exception as e:
            logger.warning(f"启动时检查更新失败: {e}")
        
    def _auto_save(self):
        """自动保存状态"""
        try:
            self.main_window._save_state()
            logger.info("自动保存完成")
        except Exception as e:
            logger.error(f"自动保存失败: {str(e)}")
            
    def show(self):
        """显示主窗口"""
        self.main_window.show()
        
    def run(self):
        """运行应用程序"""
        return self.exec_()