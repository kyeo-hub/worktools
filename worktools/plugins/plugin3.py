# -*- coding: utf-8 -*-

"""
系统工具插件
提供常用系统工具集合
"""

import os
import sys
import platform
import subprocess
import time
import psutil
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
                           QPushButton, QLabel, QLineEdit, QGroupBox, QCheckBox,
                           QMessageBox, QProgressBar, QTableWidget, QTableWidgetItem,
                           QHeaderView, QTextEdit, QComboBox, QSpinBox, QSplitter,
                           QListWidget, QListWidgetItem, QTreeWidget, QTreeWidgetItem)
from PyQt5.QtGui import QIcon, QFont, QPalette, QColor
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal

from worktools.base_plugin import BasePlugin

class ProcessMonitorThread(QThread):
    """进程监控线程"""
    
    data_updated = pyqtSignal(list)
    
    def __init__(self):
        super().__init__()
        self.running = True
        
    def run(self):
        """运行监控"""
        while self.running:
            try:
                # 获取进程列表
                processes = []
                for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent']):
                    try:
                        processes.append([
                            proc.info['pid'],
                            proc.info['name'],
                            proc.info['username'] or 'N/A',
                            f"{proc.info['cpu_percent']:.1f}%",
                            f"{proc.info['memory_percent']:.1f}%"
                        ])
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                        pass
                        
                # 按CPU使用率排序
                processes.sort(key=lambda x: float(x[3].rstrip('%')), reverse=True)
                
                # 发送数据
                self.data_updated.emit(processes[:50])  # 只发送前50个进程
                
                # 休眠
                self.msleep(2000)  # 2秒更新一次
            except Exception as e:
                print(f"进程监控错误: {str(e)}")
                self.msleep(5000)  # 出错时等待更长时间
                
    def stop(self):
        """停止监控"""
        self.running = False

class SystemTools(BasePlugin):
    """
    系统工具插件
    
    提供常用系统工具，包括进程管理、系统信息查看等
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._name = "系统工具"
        self._description = "提供常用系统工具，包括进程管理、系统信息查看等"
        self.process_monitor_thread = None
        
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
        return "系统工具"
        
    def _setup_ui(self):
        """设置用户界面"""
        # 创建主布局
        main_layout = QVBoxLayout(self)
        
        # 创建选项卡
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # 添加各个功能选项卡
        self._setup_system_info_tab()
        self._setup_process_manager_tab()
        self._setup_network_tools_tab()
        self._setup_disk_tools_tab()
        
    def _setup_system_info_tab(self):
        """设置系统信息选项卡"""
        info_widget = QWidget()
        layout = QVBoxLayout(info_widget)
        
        # 系统基本信息
        basic_group = QGroupBox("系统基本信息")
        basic_layout = QVBoxLayout(basic_group)
        
        self.basic_info_table = QTableWidget()
        self.basic_info_table.setColumnCount(2)
        self.basic_info_table.setHorizontalHeaderLabels(["属性", "值"])
        self.basic_info_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.basic_info_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        basic_layout.addWidget(self.basic_info_table)
        
        # 刷新按钮
        refresh_basic_button = QPushButton("刷新")
        refresh_basic_button.clicked.connect(self._refresh_basic_info)
        basic_layout.addWidget(refresh_basic_button)
        
        layout.addWidget(basic_group)
        
        # 系统资源使用情况
        resource_group = QGroupBox("系统资源使用情况")
        resource_layout = QVBoxLayout(resource_group)
        
        # CPU使用率
        cpu_layout = QHBoxLayout()
        cpu_layout.addWidget(QLabel("CPU使用率:"))
        self.cpu_progress = QProgressBar()
        cpu_layout.addWidget(self.cpu_progress)
        self.cpu_label = QLabel("0%")
        cpu_layout.addWidget(self.cpu_label)
        resource_layout.addLayout(cpu_layout)
        
        # 内存使用率
        memory_layout = QHBoxLayout()
        memory_layout.addWidget(QLabel("内存使用率:"))
        self.memory_progress = QProgressBar()
        memory_layout.addWidget(self.memory_progress)
        self.memory_label = QLabel("0%")
        memory_layout.addWidget(self.memory_label)
        resource_layout.addLayout(memory_layout)
        
        # 磁盘使用情况
        self.disk_table = QTableWidget()
        self.disk_table.setColumnCount(4)
        self.disk_table.setHorizontalHeaderLabels(["磁盘", "总容量", "已使用", "可用"])
        self.disk_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        resource_layout.addWidget(self.disk_table)
        
        # 刷新资源按钮
        refresh_resource_button = QPushButton("刷新资源信息")
        refresh_resource_button.clicked.connect(self._refresh_resource_info)
        resource_layout.addWidget(refresh_resource_button)
        
        layout.addWidget(resource_group)
        
        # 设置定时器，定期更新资源使用情况
        self.resource_timer = QTimer()
        self.resource_timer.timeout.connect(self._refresh_resource_info)
        self.resource_timer.start(5000)  # 5秒更新一次
        
        # 初始化信息
        self._refresh_basic_info()
        self._refresh_resource_info()
        
        self.tab_widget.addTab(info_widget, "系统信息")
        
    def _setup_process_manager_tab(self):
        """设置进程管理器选项卡"""
        process_widget = QWidget()
        layout = QVBoxLayout(process_widget)
        
        # 控制按钮
        control_layout = QHBoxLayout()
        
        self.refresh_process_button = QPushButton("刷新进程列表")
        self.refresh_process_button.clicked.connect(self._refresh_process_list)
        control_layout.addWidget(self.refresh_process_button)
        
        self.kill_process_button = QPushButton("结束进程")
        self.kill_process_button.clicked.connect(self._kill_selected_process)
        self.kill_process_button.setEnabled(False)
        control_layout.addWidget(self.kill_process_button)
        
        self.start_monitor_button = QPushButton("开始监控")
        self.start_monitor_button.clicked.connect(self._toggle_process_monitor)
        control_layout.addWidget(self.start_monitor_button)
        
        control_layout.addStretch()
        
        layout.addLayout(control_layout)
        
        # 进程列表
        self.process_table = QTableWidget()
        self.process_table.setColumnCount(5)
        self.process_table.setHorizontalHeaderLabels(["PID", "名称", "用户", "CPU", "内存"])
        self.process_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.process_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.process_table.setSelectionMode(QTableWidget.SingleSelection)
        self.process_table.itemSelectionChanged.connect(self._on_process_selection_changed)
        layout.addWidget(self.process_table)
        
        # 初始化进程列表
        self._refresh_process_list()
        
        self.tab_widget.addTab(process_widget, "进程管理")
        
    def _setup_network_tools_tab(self):
        """设置网络工具选项卡"""
        network_widget = QWidget()
        layout = QVBoxLayout(network_widget)
        
        # Ping工具
        ping_group = QGroupBox("Ping工具")
        ping_layout = QVBoxLayout(ping_group)
        
        ping_input_layout = QHBoxLayout()
        ping_input_layout.addWidget(QLabel("目标地址:"))
        self.ping_target = QLineEdit()
        self.ping_target.setPlaceholderText("输入IP地址或域名")
        ping_input_layout.addWidget(self.ping_target)
        
        self.ping_button = QPushButton("Ping")
        self.ping_button.clicked.connect(self._ping_target)
        ping_input_layout.addWidget(self.ping_button)
        
        ping_layout.addLayout(ping_input_layout)
        
        self.ping_result = QTextEdit()
        self.ping_result.setMaximumHeight(150)
        self.ping_result.setReadOnly(True)
        ping_layout.addWidget(self.ping_result)
        
        layout.addWidget(ping_group)
        
        # 端口扫描
        port_group = QGroupBox("端口扫描")
        port_layout = QVBoxLayout(port_group)
        
        port_input_layout = QHBoxLayout()
        port_input_layout.addWidget(QLabel("目标地址:"))
        self.scan_target = QLineEdit()
        self.scan_target.setPlaceholderText("输入IP地址或域名")
        port_input_layout.addWidget(self.scan_target)
        
        port_input_layout.addWidget(QLabel("端口范围:"))
        self.start_port = QSpinBox()
        self.start_port.setRange(1, 65535)
        self.start_port.setValue(1)
        port_input_layout.addWidget(self.start_port)
        
        port_input_layout.addWidget(QLabel("-"))
        self.end_port = QSpinBox()
        self.end_port.setRange(1, 65535)
        self.end_port.setValue(1024)
        port_input_layout.addWidget(self.end_port)
        
        self.scan_button = QPushButton("扫描")
        self.scan_button.clicked.connect(self._scan_ports)
        port_input_layout.addWidget(self.scan_button)
        
        port_layout.addLayout(port_input_layout)
        
        self.scan_result = QTextEdit()
        self.scan_result.setReadOnly(True)
        port_layout.addWidget(self.scan_result)
        
        layout.addWidget(port_group)
        
        # 网络连接
        connection_group = QGroupBox("网络连接")
        connection_layout = QVBoxLayout(connection_group)
        
        connection_type_layout = QHBoxLayout()
        connection_type_layout.addWidget(QLabel("连接类型:"))
        self.connection_type = QComboBox()
        self.connection_type.addItems(["所有", "TCP", "UDP"])
        connection_type_layout.addWidget(self.connection_type)
        
        refresh_connection_button = QPushButton("刷新")
        refresh_connection_button.clicked.connect(self._refresh_connections)
        connection_type_layout.addWidget(refresh_connection_button)
        
        connection_layout.addLayout(connection_type_layout)
        
        self.connection_table = QTableWidget()
        self.connection_table.setColumnCount(6)
        self.connection_table.setHorizontalHeaderLabels(["协议", "本地地址", "本地端口", "远程地址", "远程端口", "状态"])
        self.connection_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        connection_layout.addWidget(self.connection_table)
        
        layout.addWidget(connection_group)
        
        # 初始化网络连接信息
        self._refresh_connections()
        
        self.tab_widget.addTab(network_widget, "网络工具")
        
    def _setup_disk_tools_tab(self):
        """设置磁盘工具选项卡"""
        disk_widget = QWidget()
        layout = QVBoxLayout(disk_widget)
        
        # 磁盘分析
        analysis_group = QGroupBox("磁盘分析")
        analysis_layout = QVBoxLayout(analysis_group)
        
        # 选择驱动器
        drive_layout = QHBoxLayout()
        drive_layout.addWidget(QLabel("选择驱动器:"))
        self.drive_combo = QComboBox()
        self._populate_drives()
        drive_layout.addWidget(self.drive_combo)
        
        analyze_button = QPushButton("分析")
        analyze_button.clicked.connect(self._analyze_disk)
        drive_layout.addWidget(analyze_button)
        
        analysis_layout.addLayout(drive_layout)
        
        # 大文件列表
        self.large_files_table = QTableWidget()
        self.large_files_table.setColumnCount(3)
        self.large_files_table.setHorizontalHeaderLabels(["文件名", "路径", "大小"])
        self.large_files_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        analysis_layout.addWidget(self.large_files_table)
        
        layout.addWidget(analysis_group)
        
        # 重复文件查找
        duplicate_group = QGroupBox("重复文件查找")
        duplicate_layout = QVBoxLayout(duplicate_group)
        
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("搜索路径:"))
        self.duplicate_path = QLineEdit()
        self.duplicate_path.setPlaceholderText("输入要搜索的路径")
        path_layout.addWidget(self.duplicate_path)
        
        browse_button = QPushButton("浏览")
        browse_button.clicked.connect(self._browse_duplicate_path)
        path_layout.addWidget(browse_button)
        
        duplicate_layout.addLayout(path_layout)
        
        find_duplicate_button = QPushButton("查找重复文件")
        find_duplicate_button.clicked.connect(self._find_duplicate_files)
        duplicate_layout.addWidget(find_duplicate_button)
        
        # 重复文件结果
        self.duplicate_tree = QTreeWidget()
        self.duplicate_tree.setHeaderLabels(["文件", "大小", "路径"])
        self.duplicate_tree.header().setSectionResizeMode(QHeaderView.Stretch)
        duplicate_layout.addWidget(self.duplicate_tree)
        
        layout.addWidget(duplicate_group)
        
        self.tab_widget.addTab(disk_widget, "磁盘工具")
        
    def _populate_drives(self):
        """填充驱动器列表"""
        self.drive_combo.clear()
        
        if os.name == 'nt':  # Windows
            import string
            for letter in string.ascii_uppercase:
                drive = f"{letter}:\\"
                if os.path.exists(drive):
                    self.drive_combo.addItem(drive)
        else:  # Unix-like
            self.drive_combo.addItem("/")
            
    def _refresh_basic_info(self):
        """刷新基本信息"""
        info = [
            ("操作系统", platform.system()),
            ("系统版本", platform.version()),
            ("系统架构", platform.architecture()[0]),
            ("处理器", platform.processor()),
            ("计算机名", platform.node()),
            ("Python版本", sys.version.split()[0]),
            ("PyQt版本", "5.x"),  # 这里应该动态获取
        ]
        
        self.basic_info_table.setRowCount(len(info))
        for i, (key, value) in enumerate(info):
            self.basic_info_table.setItem(i, 0, QTableWidgetItem(key))
            self.basic_info_table.setItem(i, 1, QTableWidgetItem(value))
            
    def _refresh_resource_info(self):
        """刷新资源使用情况"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            self.cpu_progress.setValue(int(cpu_percent))
            self.cpu_label.setText(f"{cpu_percent:.1f}%")
            
            # 内存使用率
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            self.memory_progress.setValue(int(memory_percent))
            self.memory_label.setText(f"{memory_percent:.1f}%")
            
            # 磁盘使用情况
            disk_partitions = psutil.disk_partitions()
            self.disk_table.setRowCount(len(disk_partitions))
            
            for i, partition in enumerate(disk_partitions):
                try:
                    disk_usage = psutil.disk_usage(partition.mountpoint)
                    total = self._format_size(disk_usage.total)
                    used = self._format_size(disk_usage.used)
                    free = self._format_size(disk_usage.free)
                    
                    self.disk_table.setItem(i, 0, QTableWidgetItem(partition.device))
                    self.disk_table.setItem(i, 1, QTableWidgetItem(total))
                    self.disk_table.setItem(i, 2, QTableWidgetItem(used))
                    self.disk_table.setItem(i, 3, QTableWidgetItem(free))
                except (PermissionError, OSError):
                    self.disk_table.setItem(i, 0, QTableWidgetItem(partition.device))
                    self.disk_table.setItem(i, 1, QTableWidgetItem("无法访问"))
                    self.disk_table.setItem(i, 2, QTableWidgetItem("无法访问"))
                    self.disk_table.setItem(i, 3, QTableWidgetItem("无法访问"))
        except Exception as e:
            print(f"刷新资源信息失败: {str(e)}")
            
    def _format_size(self, size):
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} PB"
        
    def _refresh_process_list(self):
        """刷新进程列表"""
        processes = []
        
        try:
            for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent']):
                try:
                    processes.append([
                        proc.info['pid'],
                        proc.info['name'],
                        proc.info['username'] or 'N/A',
                        f"{proc.info['cpu_percent']:.1f}%",
                        f"{proc.info['memory_percent']:.1f}%"
                    ])
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
                    
            # 按CPU使用率排序
            processes.sort(key=lambda x: float(x[3].rstrip('%')), reverse=True)
            
            # 显示前50个进程
            processes = processes[:50]
            
            self.process_table.setRowCount(len(processes))
            for i, process in enumerate(processes):
                for j, value in enumerate(process):
                    self.process_table.setItem(i, j, QTableWidgetItem(str(value)))
        except Exception as e:
            print(f"刷新进程列表失败: {str(e)}")
            
    def _on_process_selection_changed(self):
        """处理进程选择变化"""
        selected_items = self.process_table.selectedItems()
        self.kill_process_button.setEnabled(len(selected_items) > 0)
        
    def _kill_selected_process(self):
        """结束选中的进程"""
        selected_items = self.process_table.selectedItems()
        if not selected_items:
            return
            
        row = selected_items[0].row()
        pid_item = self.process_table.item(row, 0)
        name_item = self.process_table.item(row, 1)
        
        pid = int(pid_item.text())
        name = name_item.text()
        
        # 确认操作
        reply = QMessageBox.question(
            self, "确认操作", 
            f"确定要结束进程 {name} (PID: {pid}) 吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # 结束进程
                psutil.Process(pid).terminate()
                
                # 刷新进程列表
                self._refresh_process_list()
                
                QMessageBox.information(self, "操作成功", f"已成功结束进程 {name}")
            except psutil.NoSuchProcess:
                QMessageBox.warning(self, "操作失败", f"进程 {name} (PID: {pid}) 不存在")
            except psutil.AccessDenied:
                QMessageBox.warning(self, "操作失败", f"没有权限结束进程 {name}")
            except Exception as e:
                QMessageBox.warning(self, "操作失败", f"结束进程失败: {str(e)}")
                
    def _toggle_process_monitor(self):
        """切换进程监控"""
        if self.process_monitor_thread and self.process_monitor_thread.isRunning():
            # 停止监控
            self.process_monitor_thread.stop()
            self.process_monitor_thread.wait()
            self.process_monitor_thread = None
            self.start_monitor_button.setText("开始监控")
        else:
            # 开始监控
            self.process_monitor_thread = ProcessMonitorThread()
            self.process_monitor_thread.data_updated.connect(self._update_process_table)
            self.process_monitor_thread.start()
            self.start_monitor_button.setText("停止监控")
            
    def _update_process_table(self, processes):
        """更新进程表"""
        try:
            self.process_table.setRowCount(len(processes))
            for i, process in enumerate(processes):
                for j, value in enumerate(process):
                    self.process_table.setItem(i, j, QTableWidgetItem(str(value)))
        except Exception as e:
            print(f"更新进程表失败: {str(e)}")
            
    def _ping_target(self):
        """Ping目标地址"""
        target = self.ping_target.text()
        if not target:
            QMessageBox.warning(self, "警告", "请输入目标地址")
            return
            
        try:
            # 执行ping命令
            if os.name == 'nt':  # Windows
                cmd = f"ping -n 4 {target}"
            else:  # Unix-like
                cmd = f"ping -c 4 {target}"
                
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            # 显示结果
            self.ping_result.setPlainText(result.stdout + result.stderr)
        except Exception as e:
            self.ping_result.setPlainText(f"Ping失败: {str(e)}")
            
    def _scan_ports(self):
        """扫描端口"""
        target = self.scan_target.text()
        start_port = self.start_port.value()
        end_port = self.end_port.value()
        
        if not target:
            QMessageBox.warning(self, "警告", "请输入目标地址")
            return
            
        self.scan_result.clear()
        self.scan_result.append(f"开始扫描 {target} 的端口 {start_port}-{end_port}...")
        
        try:
            import socket
            
            open_ports = []
            
            for port in range(start_port, end_port + 1):
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(0.5)
                    result = sock.connect_ex((target, port))
                    sock.close()
                    
                    if result == 0:
                        open_ports.append(port)
                        self.scan_result.append(f"端口 {port}: 开放")
                except Exception:
                    pass
                    
            if not open_ports:
                self.scan_result.append("未发现开放端口")
            else:
                self.scan_result.append(f"扫描完成，发现 {len(open_ports)} 个开放端口")
        except Exception as e:
            self.scan_result.append(f"扫描失败: {str(e)}")
            
    def _refresh_connections(self):
        """刷新网络连接"""
        conn_type = self.connection_type.currentText().lower()
        
        try:
            connections = []
            
            if conn_type == "tcp":
                connections = psutil.net_connections(kind='tcp')
            elif conn_type == "udp":
                connections = psutil.net_connections(kind='udp')
            else:
                connections = psutil.net_connections()
                
            self.connection_table.setRowCount(len(connections))
            
            for i, conn in enumerate(connections):
                # 协议
                protocol = conn.type.name
                
                # 本地地址和端口
                local_addr = f"{conn.laddr.ip}" if conn.laddr else "N/A"
                local_port = str(conn.laddr.port) if conn.laddr else "N/A"
                
                # 远程地址和端口
                remote_addr = f"{conn.raddr.ip}" if conn.raddr else "N/A"
                remote_port = str(conn.raddr.port) if conn.raddr else "N/A"
                
                # 状态
                status = conn.status if conn.status else "N/A"
                
                self.connection_table.setItem(i, 0, QTableWidgetItem(protocol))
                self.connection_table.setItem(i, 1, QTableWidgetItem(local_addr))
                self.connection_table.setItem(i, 2, QTableWidgetItem(local_port))
                self.connection_table.setItem(i, 3, QTableWidgetItem(remote_addr))
                self.connection_table.setItem(i, 4, QTableWidgetItem(remote_port))
                self.connection_table.setItem(i, 5, QTableWidgetItem(status))
        except Exception as e:
            print(f"刷新网络连接失败: {str(e)}")
            
    def _analyze_disk(self):
        """分析磁盘"""
        drive = self.drive_combo.currentText()
        
        if not drive:
            QMessageBox.warning(self, "警告", "请选择要分析的驱动器")
            return
            
        self.large_files_table.setRowCount(0)
        
        try:
            # 查找大文件
            large_files = []
            
            for root, dirs, files in os.walk(drive):
                for file in files:
                    try:
                        file_path = os.path.join(root, file)
                        size = os.path.getsize(file_path)
                        large_files.append((file, root, size))
                    except (PermissionError, OSError):
                        pass
                        
            # 按大小排序，取前20个
            large_files.sort(key=lambda x: x[2], reverse=True)
            large_files = large_files[:20]
            
            # 显示结果
            self.large_files_table.setRowCount(len(large_files))
            for i, (filename, path, size) in enumerate(large_files):
                self.large_files_table.setItem(i, 0, QTableWidgetItem(filename))
                self.large_files_table.setItem(i, 1, QTableWidgetItem(path))
                self.large_files_table.setItem(i, 2, QTableWidgetItem(self._format_size(size)))
        except Exception as e:
            QMessageBox.warning(self, "错误", f"分析磁盘失败: {str(e)}")
            
    def _browse_duplicate_path(self):
        """浏览重复文件路径"""
        dir_path = QFileDialog.getExistingDirectory(self, "选择搜索路径")
        if dir_path:
            self.duplicate_path.setText(dir_path)
            
    def _find_duplicate_files(self):
        """查找重复文件"""
        search_path = self.duplicate_path.text()
        
        if not search_path or not os.path.isdir(search_path):
            QMessageBox.warning(self, "警告", "请选择有效的搜索路径")
            return
            
        self.duplicate_tree.clear()
        
        try:
            # 使用文件大小和哈希值查找重复文件
            file_hashes = {}
            
            for root, dirs, files in os.walk(search_path):
                for file in files:
                    try:
                        file_path = os.path.join(root, file)
                        size = os.path.getsize(file_path)
                        
                        # 先按大小分组
                        size_group = file_hashes.setdefault(size, {})
                        
                        # 计算文件哈希（对大文件只计算前1KB的哈希）
                        import hashlib
                        hash_md5 = hashlib.md5()
                        
                        with open(file_path, 'rb') as f:
                            chunk = f.read(1024)
                            hash_md5.update(chunk)
                                
                        file_hash = hash_md5.hexdigest()
                        
                        # 添加到哈希组
                        if file_hash not in size_group:
                            size_group[file_hash] = []
                            
                        size_group[file_hash].append(file_path)
                    except (PermissionError, OSError):
                        pass
                        
            # 查找重复文件
            duplicate_count = 0
            for size, size_group in file_hashes.items():
                for file_hash, file_list in size_group.items():
                    if len(file_list) > 1:
                        # 创建重复文件组
                        group_item = QTreeWidgetItem(self.duplicate_tree)
                        group_item.setText(0, f"重复文件组 (大小: {self._format_size(size)})")
                        group_item.setData(0, Qt.UserRole, len(file_list))
                        
                        # 添加重复文件
                        for file_path in file_list:
                            file_item = QTreeWidgetItem(group_item)
                            file_item.setText(0, os.path.basename(file_path))
                            file_item.setText(1, self._format_size(size))
                            file_item.setText(2, file_path)
                            
                        duplicate_count += 1
                        
            if duplicate_count == 0:
                QMessageBox.information(self, "结果", "未发现重复文件")
            else:
                QMessageBox.information(self, "结果", f"发现 {duplicate_count} 组重复文件")
        except Exception as e:
            QMessageBox.warning(self, "错误", f"查找重复文件失败: {str(e)}")
            
    def save_state(self) -> dict:
        """保存插件状态"""
        state = {
            'current_tab': self.tab_widget.currentIndex()
        }
        return state
        
    def restore_state(self, state: dict):
        """恢复插件状态"""
        if 'current_tab' in state:
            self.tab_widget.setCurrentIndex(state['current_tab'])