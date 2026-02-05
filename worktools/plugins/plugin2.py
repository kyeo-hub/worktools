# -*- coding: utf-8 -*-

"""
文件管理器插件
提供增强的文件管理和操作工具
"""

import os
import shutil
import time
from pathlib import Path
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
                           QTreeWidget, QTreeWidgetItem, QListWidget, QListWidgetItem,
                           QPushButton, QLabel, QLineEdit, QGroupBox, QCheckBox,
                           QFileDialog, QMessageBox, QProgressBar, QSplitter,
                           QTableWidget, QTableWidgetItem, QHeaderView, QComboBox,
                           QTextEdit, QSpinBox, QFileSystemModel, QGridLayout)
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import Qt, QDir, QFileInfo, QThread, pyqtSignal

from worktools.base_plugin import BasePlugin

class FileOperationThread(QThread):
    """文件操作线程，用于避免UI阻塞"""
    
    progress_updated = pyqtSignal(int)
    operation_finished = pyqtSignal(bool, str)
    
    def __init__(self, operation, paths, target_path=None, pattern=None, replacement=None):
        super().__init__()
        self.operation = operation  # 操作类型: copy, move, delete, rename
        self.paths = paths
        self.target_path = target_path
        self.pattern = pattern
        self.replacement = replacement
        
    def run(self):
        """执行文件操作"""
        try:
            if self.operation == "copy":
                self._copy_files()
            elif self.operation == "move":
                self._move_files()
            elif self.operation == "delete":
                self._delete_files()
            elif self.operation == "rename":
                self._rename_files()
                
            self.operation_finished.emit(True, "操作成功完成")
        except Exception as e:
            self.operation_finished.emit(False, str(e))
            
    def _copy_files(self):
        """复制文件"""
        total = len(self.paths)
        for i, path in enumerate(self.paths):
            if os.path.isfile(path):
                shutil.copy2(path, self.target_path)
            elif os.path.isdir(path):
                shutil.copytree(path, os.path.join(self.target_path, os.path.basename(path)), dirs_exist_ok=True)
            self.progress_updated.emit(int((i + 1) / total * 100))
            
    def _move_files(self):
        """移动文件"""
        total = len(self.paths)
        for i, path in enumerate(self.paths):
            shutil.move(path, self.target_path)
            self.progress_updated.emit(int((i + 1) / total * 100))
            
    def _delete_files(self):
        """删除文件"""
        total = len(self.paths)
        for i, path in enumerate(self.paths):
            if os.path.isfile(path):
                os.remove(path)
            elif os.path.isdir(path):
                shutil.rmtree(path)
            self.progress_updated.emit(int((i + 1) / total * 100))
            
    def _rename_files(self):
        """重命名文件"""
        import re
        
        total = len(self.paths)
        for i, path in enumerate(self.paths):
            dir_path = os.path.dirname(path)
            old_name = os.path.basename(path)
            new_name = re.sub(self.pattern, self.replacement, old_name)
            new_path = os.path.join(dir_path, new_name)
            
            if old_name != new_name:
                os.rename(path, new_path)
                
            self.progress_updated.emit(int((i + 1) / total * 100))

class FileManager(BasePlugin):
    """
    文件管理器插件
    
    提供文件浏览、批量操作、搜索等功能
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._name = "文件管理器"
        self._description = "提供增强的文件管理和操作工具，支持批量重命名、搜索等"
        self.operation_thread = None
        
    def get_name(self) -> str:
        """返回插件显示名称"""
        return self._name
        
    def get_description(self) -> str:
        """返回插件描述信息"""
        return self._description
        
    def get_icon(self):
        """返回插件图标"""
        # 这里应该返回实际图标，暂时返回None
        return None
        
    def get_category(self) -> str:
        """返回插件所属分类"""
        return "文件工具"
        
    def _setup_ui(self):
        """设置用户界面"""
        # 创建主布局
        main_layout = QVBoxLayout(self)
        
        # 创建选项卡
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # 添加各个功能选项卡
        self._setup_browser_tab()
        self._setup_batch_operations_tab()
        self._setup_search_tab()
        self._setup_file_info_tab()
        
    def _setup_browser_tab(self):
        """设置文件浏览器选项卡"""
        browser_widget = QWidget()
        layout = QVBoxLayout(browser_widget)
        
        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)
        
        # 目录树
        dir_group = QGroupBox("目录")
        dir_layout = QVBoxLayout(dir_group)
        
        self.dir_tree = QTreeWidget()
        self.dir_tree.setHeaderLabel("目录结构")
        self.dir_tree.setAlternatingRowColors(True)
        dir_layout.addWidget(self.dir_tree)
        
        # 加载根目录
        self._load_directory_tree()
        
        splitter.addWidget(dir_group)
        
        # 文件列表
        file_group = QGroupBox("文件列表")
        file_layout = QVBoxLayout(file_group)
        
        # 路径栏
        path_layout = QHBoxLayout()
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("当前路径")
        path_layout.addWidget(QLabel("路径:"))
        path_layout.addWidget(self.path_edit)
        
        browse_button = QPushButton("浏览")
        browse_button.clicked.connect(self._browse_directory)
        path_layout.addWidget(browse_button)
        
        file_layout.addLayout(path_layout)
        
        # 文件列表
        self.file_list = QListWidget()
        self.file_list.setAlternatingRowColors(True)
        self.file_list.itemDoubleClicked.connect(self._open_file)
        file_layout.addWidget(self.file_list)
        
        splitter.addWidget(file_group)
        
        # 设置分割比例
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        
        # 连接信号
        self.dir_tree.itemClicked.connect(self._on_directory_clicked)
        
        self.tab_widget.addTab(browser_widget, "文件浏览器")
        
    def _setup_batch_operations_tab(self):
        """设置批量操作选项卡"""
        batch_widget = QWidget()
        layout = QVBoxLayout(batch_widget)
        
        # 添加文件
        add_group = QGroupBox("添加文件")
        add_layout = QHBoxLayout(add_group)
        
        add_files_button = QPushButton("添加文件")
        add_files_button.clicked.connect(self._add_files)
        add_layout.addWidget(add_files_button)
        
        add_folder_button = QPushButton("添加文件夹")
        add_folder_button.clicked.connect(self._add_folder)
        add_layout.addWidget(add_folder_button)
        
        clear_button = QPushButton("清空列表")
        clear_button.clicked.connect(self._clear_file_list)
        add_layout.addWidget(clear_button)
        
        add_layout.addStretch()
        
        layout.addWidget(add_group)
        
        # 文件列表
        list_group = QGroupBox("文件列表")
        list_layout = QVBoxLayout(list_group)
        
        self.batch_file_list = QListWidget()
        self.batch_file_list.setAlternatingRowColors(True)
        list_layout.addWidget(self.batch_file_list)
        
        layout.addWidget(list_group)
        
        # 操作选项
        operations_layout = QHBoxLayout()
        
        # 批量重命名
        rename_group = QGroupBox("批量重命名")
        rename_layout = QGridLayout(rename_group)
        
        rename_layout.addWidget(QLabel("查找模式:"), 0, 0)
        self.rename_pattern = QLineEdit()
        self.rename_pattern.setPlaceholderText("如: (.*)\\.jpg")
        rename_layout.addWidget(self.rename_pattern, 0, 1)
        
        rename_layout.addWidget(QLabel("替换为:"), 1, 0)
        self.rename_replacement = QLineEdit()
        self.rename_replacement.setPlaceholderText("如: \\1_new.jpg")
        rename_layout.addWidget(self.rename_replacement, 1, 1)
        
        rename_button = QPushButton("执行重命名")
        rename_button.clicked.connect(self._batch_rename)
        rename_layout.addWidget(rename_button, 2, 0, 1, 2)
        
        operations_layout.addWidget(rename_group)
        
        # 批量复制/移动
        copy_group = QGroupBox("批量复制/移动")
        copy_layout = QGridLayout(copy_group)
        
        copy_layout.addWidget(QLabel("目标路径:"), 0, 0)
        self.copy_target = QLineEdit()
        self.copy_target.setPlaceholderText("选择目标路径")
        copy_layout.addWidget(self.copy_target, 0, 1)
        
        browse_target_button = QPushButton("浏览")
        browse_target_button.clicked.connect(self._browse_copy_target)
        copy_layout.addWidget(browse_target_button, 0, 2)
        
        copy_button = QPushButton("复制")
        copy_button.clicked.connect(self._batch_copy)
        copy_layout.addWidget(copy_button, 1, 0)
        
        move_button = QPushButton("移动")
        move_button.clicked.connect(self._batch_move)
        copy_layout.addWidget(move_button, 1, 1)
        
        delete_button = QPushButton("删除")
        delete_button.clicked.connect(self._batch_delete)
        copy_layout.addWidget(delete_button, 1, 2)
        
        operations_layout.addWidget(copy_group)
        
        layout.addLayout(operations_layout)
        
        # 进度条
        progress_group = QGroupBox("操作进度")
        progress_layout = QVBoxLayout(progress_group)
        
        self.progress_bar = QProgressBar()
        progress_layout.addWidget(self.progress_bar)
        
        self.progress_label = QLabel("就绪")
        progress_layout.addWidget(self.progress_label)
        
        layout.addWidget(progress_group)
        
        self.tab_widget.addTab(batch_widget, "批量操作")
        
    def _setup_search_tab(self):
        """设置文件搜索选项卡"""
        search_widget = QWidget()
        layout = QVBoxLayout(search_widget)
        
        # 搜索设置
        settings_group = QGroupBox("搜索设置")
        settings_layout = QGridLayout(settings_group)
        
        settings_layout.addWidget(QLabel("搜索路径:"), 0, 0)
        self.search_path = QLineEdit()
        self.search_path.setPlaceholderText("选择搜索路径")
        settings_layout.addWidget(self.search_path, 0, 1)
        
        browse_search_button = QPushButton("浏览")
        browse_search_button.clicked.connect(self._browse_search_path)
        settings_layout.addWidget(browse_search_button, 0, 2)
        
        settings_layout.addWidget(QLabel("文件名模式:"), 1, 0)
        self.search_pattern = QLineEdit()
        self.search_pattern.setPlaceholderText("如: *.txt, *.py")
        settings_layout.addWidget(self.search_pattern, 1, 1)
        
        self.include_subdirs_check = QCheckBox("包含子目录")
        self.include_subdirs_check.setChecked(True)
        settings_layout.addWidget(self.include_subdirs_check, 1, 2)
        
        settings_layout.addWidget(QLabel("内容关键词:"), 2, 0)
        self.search_content = QLineEdit()
        self.search_content.setPlaceholderText("搜索文件内容（可选）")
        settings_layout.addWidget(self.search_content, 2, 1, 1, 2)
        
        search_button = QPushButton("开始搜索")
        search_button.clicked.connect(self._search_files)
        settings_layout.addWidget(search_button, 3, 0, 1, 3)
        
        layout.addWidget(settings_group)
        
        # 搜索结果
        results_group = QGroupBox("搜索结果")
        results_layout = QVBoxLayout(results_group)
        
        self.search_results = QTableWidget()
        self.search_results.setColumnCount(4)
        self.search_results.setHorizontalHeaderLabels(["文件名", "路径", "大小", "修改时间"])
        self.search_results.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.search_results.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        results_layout.addWidget(self.search_results)
        
        layout.addWidget(results_group)
        
        self.tab_widget.addTab(search_widget, "文件搜索")
        
    def _setup_file_info_tab(self):
        """设置文件信息选项卡"""
        info_widget = QWidget()
        layout = QVBoxLayout(info_widget)
        
        # 文件选择
        select_group = QGroupBox("选择文件")
        select_layout = QHBoxLayout(select_group)
        
        self.file_path = QLineEdit()
        self.file_path.setPlaceholderText("选择文件或文件夹")
        select_layout.addWidget(self.file_path)
        
        browse_file_button = QPushButton("浏览")
        browse_file_button.clicked.connect(self._browse_file)
        select_layout.addWidget(browse_file_button)
        
        layout.addWidget(select_group)
        
        # 文件信息
        info_group = QGroupBox("文件信息")
        info_layout = QVBoxLayout(info_group)
        
        self.file_info_table = QTableWidget()
        self.file_info_table.setColumnCount(2)
        self.file_info_table.setHorizontalHeaderLabels(["属性", "值"])
        self.file_info_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.file_info_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        info_layout.addWidget(self.file_info_table)
        
        layout.addWidget(info_group)
        
        # 文件哈希
        hash_group = QGroupBox("文件哈希")
        hash_layout = QVBoxLayout(hash_group)
        
        hash_button_layout = QHBoxLayout()
        calculate_md5_button = QPushButton("计算MD5")
        calculate_md5_button.clicked.connect(self._calculate_md5)
        hash_button_layout.addWidget(calculate_md5_button)
        
        calculate_sha1_button = QPushButton("计算SHA1")
        calculate_sha1_button.clicked.connect(self._calculate_sha1)
        hash_button_layout.addWidget(calculate_sha1_button)
        
        calculate_sha256_button = QPushButton("计算SHA256")
        calculate_sha256_button.clicked.connect(self._calculate_sha256)
        hash_button_layout.addWidget(calculate_sha256_button)
        
        hash_layout.addLayout(hash_button_layout)
        
        self.hash_result = QTextEdit()
        self.hash_result.setMaximumHeight(100)
        self.hash_result.setReadOnly(True)
        hash_layout.addWidget(self.hash_result)
        
        layout.addWidget(hash_group)
        
        self.tab_widget.addTab(info_widget, "文件信息")
        
    def _load_directory_tree(self):
        """加载目录树"""
        self.dir_tree.clear()
        
        # 获取系统驱动器
        drives = []
        if os.name == 'nt':  # Windows
            import string
            for letter in string.ascii_uppercase:
                drive = f"{letter}:\\"
                if os.path.exists(drive):
                    drives.append(drive)
        else:  # Unix-like
            drives.append("/")
            
        # 添加驱动器到树
        for drive in drives:
            drive_item = QTreeWidgetItem(self.dir_tree)
            drive_item.setText(0, drive)
            drive_item.setData(0, Qt.UserRole, drive)
            
            # 添加子目录
            try:
                for entry in os.listdir(drive):
                    full_path = os.path.join(drive, entry)
                    if os.path.isdir(full_path) and not entry.startswith('.'):
                        child_item = QTreeWidgetItem(drive_item)
                        child_item.setText(0, entry)
                        child_item.setData(0, Qt.UserRole, full_path)
            except (PermissionError, OSError):
                pass
                
        # 展开第一层
        self.dir_tree.expandAll()
        
    def _on_directory_clicked(self, item: QTreeWidgetItem, column: int):
        """处理目录点击事件"""
        path = item.data(0, Qt.UserRole)
        if path and os.path.isdir(path):
            self._load_file_list(path)
            self.path_edit.setText(path)
            
    def _load_file_list(self, dir_path):
        """加载文件列表"""
        self.file_list.clear()
        
        try:
            entries = os.listdir(dir_path)
            for entry in sorted(entries):
                full_path = os.path.join(dir_path, entry)
                
                item = QListWidgetItem(entry)
                
                # 设置不同图标（这里简化处理）
                if os.path.isdir(full_path):
                    item.setText(f"[目录] {entry}")
                else:
                    size = os.path.getsize(full_path)
                    item.setText(f"{entry} ({self._format_size(size)})")
                    
                item.setData(Qt.UserRole, full_path)
                self.file_list.addItem(item)
        except (PermissionError, OSError):
            self.file_list.addItem("无权限访问此目录")
            
    def _format_size(self, size):
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} PB"
        
    def _browse_directory(self):
        """浏览目录"""
        dir_path = QFileDialog.getExistingDirectory(self, "选择目录")
        if dir_path:
            self.path_edit.setText(dir_path)
            self._load_file_list(dir_path)
            
    def _open_file(self, item):
        """打开文件"""
        file_path = item.data(Qt.UserRole)
        if file_path and os.path.isfile(file_path):
            # 这里可以使用系统默认程序打开文件
            os.startfile(file_path) if os.name == 'nt' else os.system(f"open '{file_path}'")
            
    def _add_files(self):
        """添加文件到批量操作列表"""
        files, _ = QFileDialog.getOpenFileNames(self, "选择文件")
        if files:
            for file_path in files:
                item = QListWidgetItem(file_path)
                item.setData(Qt.UserRole, file_path)
                self.batch_file_list.addItem(item)
                
    def _add_folder(self):
        """添加文件夹到批量操作列表"""
        dir_path = QFileDialog.getExistingDirectory(self, "选择文件夹")
        if dir_path:
            item = QListWidgetItem(dir_path)
            item.setData(Qt.UserRole, dir_path)
            self.batch_file_list.addItem(item)
            
    def _clear_file_list(self):
        """清空批量操作列表"""
        self.batch_file_list.clear()
        
    def _browse_copy_target(self):
        """浏览复制目标路径"""
        dir_path = QFileDialog.getExistingDirectory(self, "选择目标目录")
        if dir_path:
            self.copy_target.setText(dir_path)
            
    def _batch_rename(self):
        """批量重命名"""
        pattern = self.rename_pattern.text()
        replacement = self.rename_replacement.text()
        
        if not pattern:
            QMessageBox.warning(self, "警告", "请输入重命名模式")
            return
            
        paths = []
        for i in range(self.batch_file_list.count()):
            item = self.batch_file_list.item(i)
            paths.append(item.data(Qt.UserRole))
            
        if not paths:
            QMessageBox.warning(self, "警告", "请先添加文件")
            return
            
        # 确认操作
        reply = QMessageBox.question(
            self, "确认", 
            f"确定要重命名 {len(paths)} 个文件吗？\n模式: {pattern} -> {replacement}",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self._start_operation("rename", paths, pattern=pattern, replacement=replacement)
            
    def _batch_copy(self):
        """批量复制"""
        target_path = self.copy_target.text()
        if not target_path or not os.path.isdir(target_path):
            QMessageBox.warning(self, "警告", "请选择有效的目标目录")
            return
            
        paths = []
        for i in range(self.batch_file_list.count()):
            item = self.batch_file_list.item(i)
            paths.append(item.data(Qt.UserRole))
            
        if not paths:
            QMessageBox.warning(self, "警告", "请先添加文件")
            return
            
        # 确认操作
        reply = QMessageBox.question(
            self, "确认", 
            f"确定要复制 {len(paths)} 个文件到 {target_path} 吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self._start_operation("copy", paths, target_path=target_path)
            
    def _batch_move(self):
        """批量移动"""
        target_path = self.copy_target.text()
        if not target_path or not os.path.isdir(target_path):
            QMessageBox.warning(self, "警告", "请选择有效的目标目录")
            return
            
        paths = []
        for i in range(self.batch_file_list.count()):
            item = self.batch_file_list.item(i)
            paths.append(item.data(Qt.UserRole))
            
        if not paths:
            QMessageBox.warning(self, "警告", "请先添加文件")
            return
            
        # 确认操作
        reply = QMessageBox.question(
            self, "确认", 
            f"确定要移动 {len(paths)} 个文件到 {target_path} 吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self._start_operation("move", paths, target_path=target_path)
            
    def _batch_delete(self):
        """批量删除"""
        paths = []
        for i in range(self.batch_file_list.count()):
            item = self.batch_file_list.item(i)
            paths.append(item.data(Qt.UserRole))
            
        if not paths:
            QMessageBox.warning(self, "警告", "请先添加文件")
            return
            
        # 确认操作
        reply = QMessageBox.question(
            self, "确认", 
            f"确定要删除 {len(paths)} 个文件吗？此操作不可撤销！",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self._start_operation("delete", paths)
            
    def _start_operation(self, operation, paths, target_path=None, pattern=None, replacement=None):
        """启动文件操作线程"""
        self.progress_bar.setValue(0)
        self.progress_label.setText("操作进行中...")
        
        # 创建并启动操作线程
        self.operation_thread = FileOperationThread(
            operation, paths, target_path, pattern, replacement
        )
        self.operation_thread.progress_updated.connect(self.progress_bar.setValue)
        self.operation_thread.operation_finished.connect(self._on_operation_finished)
        self.operation_thread.start()
        
    def _on_operation_finished(self, success, message):
        """操作完成回调"""
        self.progress_label.setText(message)
        
        if success:
            QMessageBox.information(self, "操作完成", message)
        else:
            QMessageBox.critical(self, "操作失败", f"操作失败: {message}")
            
    def _browse_search_path(self):
        """浏览搜索路径"""
        dir_path = QFileDialog.getExistingDirectory(self, "选择搜索目录")
        if dir_path:
            self.search_path.setText(dir_path)
            
    def _search_files(self):
        """搜索文件"""
        search_path = self.search_path.text()
        pattern = self.search_pattern.text()
        include_subdirs = self.include_subdirs_check.isChecked()
        content_keyword = self.search_content.text()
        
        if not search_path or not os.path.isdir(search_path):
            QMessageBox.warning(self, "警告", "请选择有效的搜索路径")
            return
            
        if not pattern and not content_keyword:
            QMessageBox.warning(self, "警告", "请输入文件名模式或内容关键词")
            return
            
        # 清空结果表
        self.search_results.setRowCount(0)
        
        # 搜索文件
        import fnmatch
        results = []
        
        if include_subdirs:
            for root, dirs, files in os.walk(search_path):
                for file in files:
                    if pattern and not fnmatch.fnmatch(file, pattern):
                        continue
                        
                    if content_keyword:
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                                if content_keyword not in content:
                                    continue
                        except (PermissionError, OSError):
                            continue
                            
                    # 获取文件信息
                    file_path = os.path.join(root, file)
                    try:
                        stat = os.stat(file_path)
                        size = stat.st_size
                        mtime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(stat.st_mtime))
                    except (PermissionError, OSError):
                        size = 0
                        mtime = "未知"
                        
                    results.append((file, root, self._format_size(size), mtime))
        else:
            for file in os.listdir(search_path):
                full_path = os.path.join(search_path, file)
                if not os.path.isfile(full_path):
                    continue
                    
                if pattern and not fnmatch.fnmatch(file, pattern):
                    continue
                    
                if content_keyword:
                    try:
                        with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            if content_keyword not in content:
                                continue
                    except (PermissionError, OSError):
                        continue
                        
                # 获取文件信息
                try:
                    stat = os.stat(full_path)
                    size = stat.st_size
                    mtime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(stat.st_mtime))
                except (PermissionError, OSError):
                    size = 0
                    mtime = "未知"
                    
                results.append((file, search_path, self._format_size(size), mtime))
                
        # 显示结果
        self.search_results.setRowCount(len(results))
        for i, (filename, path, size, mtime) in enumerate(results):
            self.search_results.setItem(i, 0, QTableWidgetItem(filename))
            self.search_results.setItem(i, 1, QTableWidgetItem(path))
            self.search_results.setItem(i, 2, QTableWidgetItem(size))
            self.search_results.setItem(i, 3, QTableWidgetItem(mtime))
            
        QMessageBox.information(self, "搜索完成", f"找到 {len(results)} 个匹配的文件")
        
    def _browse_file(self):
        """浏览文件"""
        file_path, _ = QFileDialog.getOpenFileName(self, "选择文件")
        if file_path:
            self.file_path.setText(file_path)
            self._display_file_info(file_path)
            
    def _display_file_info(self, file_path):
        """显示文件信息"""
        try:
            stat = os.stat(file_path)
            
            # 清空表
            self.file_info_table.setRowCount(0)
            
            # 文件信息
            info = [
                ("文件名", os.path.basename(file_path)),
                ("路径", os.path.dirname(file_path)),
                ("大小", self._format_size(stat.st_size)),
                ("创建时间", time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(stat.st_ctime))),
                ("修改时间", time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(stat.st_mtime))),
                ("访问时间", time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(stat.st_atime))),
            ]
            
            if os.path.isfile(file_path):
                # 文件扩展名
                _, ext = os.path.splitext(file_path)
                info.append(("扩展名", ext))
                
                # 文件类型
                mime_type = "未知"
                try:
                    import mimetypes
                    mime_type, _ = mimetypes.guess_type(file_path)
                    mime_type = mime_type or "未知"
                except ImportError:
                    pass
                info.append(("MIME类型", mime_type))
                
            elif os.path.isdir(file_path):
                # 目录中的文件数
                try:
                    file_count = len([f for f in os.listdir(file_path) if os.path.isfile(os.path.join(file_path, f))])
                    info.append(("文件数", str(file_count)))
                except (PermissionError, OSError):
                    info.append(("文件数", "未知"))
                    
                # 目录中的子目录数
                try:
                    dir_count = len([d for d in os.listdir(file_path) if os.path.isdir(os.path.join(file_path, d))])
                    info.append(("子目录数", str(dir_count)))
                except (PermissionError, OSError):
                    info.append(("子目录数", "未知"))
                    
            # 设置表内容
            self.file_info_table.setRowCount(len(info))
            for i, (key, value) in enumerate(info):
                self.file_info_table.setItem(i, 0, QTableWidgetItem(key))
                self.file_info_table.setItem(i, 1, QTableWidgetItem(value))
                
        except Exception as e:
            QMessageBox.warning(self, "错误", f"无法获取文件信息: {str(e)}")
            
    def _calculate_md5(self):
        """计算MD5哈希"""
        file_path = self.file_path.text()
        if not file_path or not os.path.isfile(file_path):
            QMessageBox.warning(self, "警告", "请选择有效的文件")
            return
            
        try:
            import hashlib
            with open(file_path, 'rb') as f:
                md5_hash = hashlib.md5()
                for chunk in iter(lambda: f.read(4096), b""):
                    md5_hash.update(chunk)
                    
                self.hash_result.setText(f"MD5: {md5_hash.hexdigest()}")
        except Exception as e:
            QMessageBox.warning(self, "错误", f"计算MD5失败: {str(e)}")
            
    def _calculate_sha1(self):
        """计算SHA1哈希"""
        file_path = self.file_path.text()
        if not file_path or not os.path.isfile(file_path):
            QMessageBox.warning(self, "警告", "请选择有效的文件")
            return
            
        try:
            import hashlib
            with open(file_path, 'rb') as f:
                sha1_hash = hashlib.sha1()
                for chunk in iter(lambda: f.read(4096), b""):
                    sha1_hash.update(chunk)
                    
                self.hash_result.setText(f"SHA1: {sha1_hash.hexdigest()}")
        except Exception as e:
            QMessageBox.warning(self, "错误", f"计算SHA1失败: {str(e)}")
            
    def _calculate_sha256(self):
        """计算SHA256哈希"""
        file_path = self.file_path.text()
        if not file_path or not os.path.isfile(file_path):
            QMessageBox.warning(self, "警告", "请选择有效的文件")
            return
            
        try:
            import hashlib
            with open(file_path, 'rb') as f:
                sha256_hash = hashlib.sha256()
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
                    
                self.hash_result.setText(f"SHA256: {sha256_hash.hexdigest()}")
        except Exception as e:
            QMessageBox.warning(self, "错误", f"计算SHA256失败: {str(e)}")