#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PyQt工作工具主入口
"""

import sys
import os
import logging
import tempfile
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTranslator, QLocale
from PyQt5.QtGui import QIcon

def get_resource_path(relative_path):
    """获取资源文件的绝对路径（支持开发和打包环境）"""
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller打包后的临时目录
        return os.path.join(sys._MEIPASS, relative_path)
    # 开发环境
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), relative_path)

# 添加应用路径到sys.path（仅开发环境）
if not hasattr(sys, '_MEIPASS'):
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from worktools.app import WorkToolsApp

def setup_logging():
    """设置日志配置"""
    # 使用临时目录写入日志（打包后没有写权限）
    if hasattr(sys, '_MEIPASS'):
        # 打包环境：写入用户临时目录
        log_dir = os.path.join(tempfile.gettempdir(), 'WorkTools')
        if not os.path.exists(log_dir):
            try:
                os.makedirs(log_dir)
            except:
                log_dir = tempfile.gettempdir()
        log_file = os.path.join(log_dir, 'worktools.log')
    else:
        # 开发环境：写入项目目录
        log_file = os.path.join(os.path.dirname(__file__), 'worktools.log')
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file)
        ]
    )
    return log_file

def main():
    """主函数"""
    try:
        log_file = setup_logging()
        logger = logging.getLogger(__name__)
        logger.info(f"应用程序启动 - 日志文件: {log_file}")
        logger.info(f"工作目录: {os.getcwd()}")
        
        # 创建并显示主窗口
        work_tools = WorkToolsApp(sys.argv)
    
        # 设置应用信息
        work_tools.setApplicationName("工作工具")
        work_tools.setApplicationVersion("0.1.0")
        work_tools.setOrganizationName("WorkTools")
        
        # 设置应用图标
        icon_path = get_resource_path("worktools/resources/icons/app.png")
        if os.path.exists(icon_path):
            work_tools.setWindowIcon(QIcon(icon_path))
        else:
            logger.warning(f"图标文件不存在: {icon_path}")
        
        # 加载中文翻译（可选）
        translator = QTranslator()
        locale = QLocale.system().name()
        qm_path = get_resource_path(f"worktools/i18n/worktools_{locale}.qm")
        if os.path.exists(qm_path):
            if translator.load(qm_path):
                work_tools.installTranslator(translator)
                logger.info(f"已加载翻译: {locale}")
            else:
                logger.warning(f"翻译加载失败: {qm_path}")
        else:
            logger.info(f"翻译文件不存在: {qm_path}，跳过翻译")
        
        work_tools.show()
        
        # 运行应用程序
        exit_code = work_tools.run()
        logger.info(f"应用程序退出，退出码: {exit_code}")
        sys.exit(exit_code)
    
    except Exception as e:
        # 捕获未处理的异常，防止窗口直接关闭
        import traceback
        error_msg = f"应用程序启动失败: {str(e)}\n{traceback.format_exc()}"
        print(error_msg, file=sys.stderr)
        
        # 尝试写入错误日志
        try:
            error_log_dir = os.path.join(tempfile.gettempdir(), 'WorkTools')
            if not os.path.exists(error_log_dir):
                os.makedirs(error_log_dir)
            error_log_file = os.path.join(error_log_dir, 'error.log')
            with open(error_log_file, 'w', encoding='utf-8') as f:
                f.write(error_msg)
            print(f"错误已写入: {error_log_file}", file=sys.stderr)
        except:
            pass
        
        # 显示错误对话框
        from PyQt5.QtWidgets import QMessageBox
        app = QApplication(sys.argv)
        QMessageBox.critical(
            None,
            "启动失败",
            f"应用程序启动失败！\n\n错误信息:\n{str(e)}\n\n详细错误已记录到:\n{os.path.join(tempfile.gettempdir(), 'WorkTools', 'error.log')}"
        )
        sys.exit(1)

if __name__ == "__main__":
    main()