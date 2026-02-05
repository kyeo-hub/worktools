# -*- coding: utf-8 -*-

"""
自动更新模块
负责检查更新、下载更新、安装更新
"""

import os
import sys
import json
import urllib.request
import urllib.error
import zipfile
import shutil
import tempfile
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QProgressBar, QMessageBox, QTextEdit)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSettings
from PyQt5.QtGui import QFont

import logging

logger = logging.getLogger(__name__)


class UpdateChecker(QThread):
    """检查更新的工作线程"""
    
    check_finished = pyqtSignal(dict)  # 检查结果
    check_error = pyqtSignal(str)  # 错误信息
    
    def run(self):
        """检查更新"""
        try:
            # 获取当前版本
            current_version = self._get_current_version()
            
            # 获取服务器版本信息
            version_url = self._get_version_url()
            
            req = urllib.request.Request(
                version_url,
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                server_info = json.loads(response.read().decode('utf-8'))
            
            # 比较版本
            latest_version = server_info.get('version', current_version)
            
            if self._compare_version(latest_version, current_version) > 0:
                # 有新版本
                result = {
                    'has_update': True,
                    'current_version': current_version,
                    'latest_version': latest_version,
                    'changelog': server_info.get('changelog', []),
                    'download_url': server_info.get('download_url', ''),
                    'mandatory': server_info.get('mandatory', False),
                    'published_at': server_info.get('published_at', '')
                }
            else:
                # 无更新
                result = {
                    'has_update': False,
                    'current_version': current_version,
                    'latest_version': latest_version
                }
            
            self.check_finished.emit(result)
            
        except Exception as e:
            logger.error(f"检查更新失败: {e}")
            self.check_error.emit(str(e))
    
    def _get_current_version(self):
        """获取当前版本"""
        try:
            # 尝试从version.json读取
            version_file = self._get_resource_path('version.json')
            if os.path.exists(version_file):
                with open(version_file, 'r', encoding='utf-8') as f:
                    info = json.load(f)
                    return info.get('version', '0.0.0')
        except Exception as e:
            logger.error(f"读取版本文件失败: {e}")
        
        # 默认版本
        return '0.1.0'
    
    def _get_version_url(self):
        """获取版本检查URL"""
        try:
            version_file = self._get_resource_path('version.json')
            if os.path.exists(version_file):
                with open(version_file, 'r', encoding='utf-8') as f:
                    info = json.load(f)
                    return info.get('update_url', '')
        except:
            pass
        
        # 默认URL（请修改为你的服务器地址）
        return 'https://your-server.com/updates/version.json'
    
    def _get_resource_path(self, relative_path):
        """获取资源文件的绝对路径（支持开发和打包环境）"""
        if hasattr(sys, '_MEIPASS'):
            # PyInstaller打包后的临时目录
            return os.path.join(sys._MEIPASS, relative_path)
        return os.path.join(os.path.dirname(os.path.dirname(__file__)), relative_path)
    
    def _compare_version(self, v1, v2):
        """比较版本号，v1>v2返回1，相等返回0，v1<v2返回-1"""
        parts1 = [int(x) for x in v1.split('.')]
        parts2 = [int(x) for x in v2.split('.')]
        
        for i in range(max(len(parts1), len(parts2))):
            p1 = parts1[i] if i < len(parts1) else 0
            p2 = parts2[i] if i < len(parts2) else 0
            
            if p1 > p2:
                return 1
            elif p1 < p2:
                return -1
        
        return 0


class UpdateDownloader(QThread):
    """下载更新的工作线程"""
    
    download_progress = pyqtSignal(int, int)  # 当前大小，总大小
    download_finished = pyqtSignal(str)  # 下载完成的文件路径
    download_error = pyqtSignal(str)  # 错误信息
    
    def __init__(self, download_url, save_path):
        super().__init__()
        self.download_url = download_url
        self.save_path = save_path
    
    def run(self):
        """下载更新包"""
        try:
            req = urllib.request.Request(
                self.download_url,
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            
            with urllib.request.urlopen(req, timeout=30) as response:
                total_size = int(response.headers.get('Content-Length', 0))
                downloaded = 0
                
                with open(self.save_path, 'wb') as f:
                    while True:
                        chunk = response.read(8192)
                        if not chunk:
                            break
                        
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if total_size > 0:
                            self.download_progress.emit(downloaded, total_size)
            
            self.download_finished.emit(self.save_path)
            
        except Exception as e:
            logger.error(f"下载更新失败: {e}")
            self.download_error.emit(str(e))


class UpdateDialog(QDialog):
    """更新对话框"""
    
    def __init__(self, update_info, parent=None):
        super().__init__(parent)
        self.update_info = update_info
        self.downloaded_file = None
        
        self.setWindowTitle("发现新版本")
        self.setMinimumSize(500, 400)
        self._setup_ui()
    
    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        
        # 版本信息
        version_label = QLabel(
            f"<h2>发现新版本</h2>"
            f"<p>当前版本: {self.update_info['current_version']}</p>"
            f"<p>最新版本: <b style='color: green;'>{self.update_info['latest_version']}</b></p>"
        )
        version_label.setTextFormat(Qt.RichText)
        layout.addWidget(version_label)
        
        # 发布日期
        if self.update_info.get('published_at'):
            date_label = QLabel(f"发布日期: {self.update_info['published_at']}")
            layout.addWidget(date_label)
        
        # 更新日志
        changelog_label = QLabel("<b>更新内容:</b>")
        layout.addWidget(changelog_label)
        
        changelog_text = QTextEdit()
        changelog_text.setReadOnly(True)
        changelog_text.setMaximumHeight(150)
        
        changelog = self.update_info.get('changelog', [])
        if changelog:
            changelog_text.setText('\n'.join([f"• {item}" for item in changelog]))
        else:
            changelog_text.setText("无更新说明")
        layout.addWidget(changelog_text)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # 状态标签
        self.status_label = QLabel("")
        layout.addWidget(self.status_label)
        
        # 按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.update_btn = QPushButton("立即更新")
        self.update_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 8px 20px;")
        self.update_btn.clicked.connect(self._start_update)
        button_layout.addWidget(self.update_btn)
        
        self.later_btn = QPushButton("稍后提醒")
        self.later_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.later_btn)
        
        # 强制更新时不显示"稍后"按钮
        if self.update_info.get('mandatory', False):
            self.later_btn.setVisible(False)
            self.setWindowTitle("需要更新")
            version_label.setText(
                f"<h2>需要更新</h2>"
                f"<p>当前版本: {self.update_info['current_version']}</p>"
                f"<p>最新版本: <b style='color: red;'>{self.update_info['latest_version']}</b></p>"
                f"<p style='color: red;'>此更新为强制更新，必须安装后才能继续使用。</p>"
            )
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
    
    def _start_update(self):
        """开始更新"""
        self.update_btn.setEnabled(False)
        self.later_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.status_label.setText("正在下载更新...")
        
        # 创建临时目录
        temp_dir = tempfile.gettempdir()
        download_path = os.path.join(temp_dir, 'worktools_update.zip')
        
        # 开始下载
        self.downloader = UpdateDownloader(
            self.update_info['download_url'],
            download_path
        )
        self.downloader.download_progress.connect(self._on_download_progress)
        self.downloader.download_finished.connect(self._on_download_finished)
        self.downloader.download_error.connect(self._on_download_error)
        self.downloader.start()
    
    def _on_download_progress(self, current, total):
        """下载进度"""
        if total > 0:
            percent = int(current * 100 / total)
            self.progress_bar.setValue(percent)
            self.status_label.setText(f"下载进度: {percent}% ({current//1024}KB / {total//1024}KB)")
    
    def _on_download_finished(self, file_path):
        """下载完成"""
        self.downloaded_file = file_path
        self.status_label.setText("下载完成，准备安装...")
        self._install_update()
    
    def _on_download_error(self, error_msg):
        """下载错误"""
        self.status_label.setText(f"下载失败: {error_msg}")
        self.status_label.setStyleSheet("color: red;")
        self.update_btn.setEnabled(True)
        self.later_btn.setEnabled(True)
    
    def _install_update(self):
        """安装更新"""
        try:
            # 解压更新包
            temp_dir = tempfile.gettempdir()
            extract_dir = os.path.join(temp_dir, 'worktools_update')
            
            if os.path.exists(extract_dir):
                shutil.rmtree(extract_dir)
            os.makedirs(extract_dir)
            
            with zipfile.ZipFile(self.downloaded_file, 'r') as zf:
                zf.extractall(extract_dir)
            
            # 创建更新脚本
            self._create_update_script(extract_dir)
            
            # 执行更新脚本并退出
            self.status_label.setText("更新准备就绪，应用程序将重启...")
            
            QMessageBox.information(
                self, 
                "更新就绪", 
                "更新文件已准备就绪，点击确定后将关闭应用程序并安装更新。"
            )
            
            self.accept()
            self._execute_update()
            
        except Exception as e:
            logger.error(f"安装更新失败: {e}")
            self.status_label.setText(f"安装失败: {str(e)}")
            self.status_label.setStyleSheet("color: red;")
            self.update_btn.setEnabled(True)
            self.later_btn.setEnabled(True)
    
    def _create_update_script(self, extract_dir):
        """创建更新脚本"""
        if sys.platform == 'win32':
            script_path = os.path.join(tempfile.gettempdir(), 'worktools_updater.bat')
            current_exe = sys.executable
            
            script_content = f'''@echo off
chcp 65001 >nul
echo 正在安装更新...
timeout /t 2 /nobreak >nul

REM 关闭原程序进程
taskkill /F /IM "{os.path.basename(current_exe)}" 2>nul
timeout /t 1 /nobreak >nul

REM 复制新文件
xcopy /Y /E "{extract_dir}\\*" "{os.path.dirname(current_exe)}\\"

REM 删除临时文件
rmdir /S /Q "{extract_dir}"
del "{self.downloaded_file}"

REM 启动新版本
echo 启动新版本...
start "" "{current_exe}"

REM 删除自身
del "%~f0"
'''
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(script_content)
    
    def _execute_update(self):
        """执行更新"""
        if sys.platform == 'win32':
            script_path = os.path.join(tempfile.gettempdir(), 'worktools_updater.bat')
            import subprocess
            subprocess.Popen(
                ['cmd', '/c', script_path],
                shell=True,
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
        
        # 退出应用程序
        from PyQt5.QtWidgets import QApplication
        QApplication.instance().quit()


class AutoUpdater:
    """自动更新管理器"""
    
    def __init__(self, parent=None):
        self.parent = parent
        self.update_dialog = None
    
    def check_update(self, silent=False):
        """
        检查更新
        
        Args:
            silent: 是否静默检查（无更新时不提示）
        """
        self.silent = silent
        
        self.checker = UpdateChecker()
        self.checker.check_finished.connect(self._on_check_finished)
        self.checker.check_error.connect(self._on_check_error)
        self.checker.start()
    
    def _on_check_finished(self, result):
        """检查完成"""
        if result['has_update']:
            # 显示更新对话框
            self.update_dialog = UpdateDialog(result, self.parent)
            self.update_dialog.exec_()
        else:
            if not self.silent:
                QMessageBox.information(
                    self.parent,
                    "检查更新",
                    f"当前已是最新版本 ({result['current_version']})"
                )
    
    def _on_check_error(self, error_msg):
        """检查错误"""
        if not self.silent:
            QMessageBox.warning(
                self.parent,
                "检查更新失败",
                f"无法连接到更新服务器:\n{error_msg}"
            )
