#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PyQt工作工具主入口
"""

import sys
import os
import logging
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTranslator, QLocale
from PyQt5.QtGui import QIcon

# 添加应用路径到sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from worktools.app import WorkToolsApp

def setup_logging():
    """设置日志配置"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(os.path.join(os.path.dirname(__file__), 'worktools.log'))
        ]
    )

def main():
    """主函数"""
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("应用程序启动")
    
    # 创建并显示主窗口
    work_tools = WorkToolsApp(sys.argv)
    
    # 设置应用信息
    work_tools.setApplicationName("工作工具")
    work_tools.setApplicationVersion("0.1.0")
    work_tools.setOrganizationName("WorkTools")
    
    # 设置应用图标
    work_tools.setWindowIcon(QIcon(os.path.join(os.path.dirname(__file__), "worktools/resources/icons/app.png")))
    
    # 加载中文翻译（可选）
    translator = QTranslator()
    locale = QLocale.system().name()
    if translator.load(f"worktools/i18n/worktools_{locale}.qm"):
        work_tools.installTranslator(translator)
    
    work_tools.show()
    
    # 运行应用程序
    exit_code = work_tools.run()
    logger.info(f"应用程序退出，退出码: {exit_code}")
    sys.exit(exit_code)

if __name__ == "__main__":
    main()