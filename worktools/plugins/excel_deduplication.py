# -*- coding: utf-8 -*-

"""
Excel去重工具插件
用于Excel表格数据的去重处理
"""

import os
import pandas as pd
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
                           QPushButton, QLabel, QLineEdit, QGroupBox, QCheckBox,
                           QFileDialog, QMessageBox, QProgressBar, QSplitter,
                           QTableWidget, QTableWidgetItem, QHeaderView, QComboBox,
                           QTextEdit, QSpinBox, QGridLayout, QFormLayout,
                           QDialog, QDialogButtonBox, QScrollArea, QFrame, QSizePolicy,
                           QListWidget, QListWidgetItem)
from PyQt5.QtGui import QIcon, QFont, QStandardItemModel, QStandardItem, QColor
from PyQt5.QtCore import Qt, QDir, QFileInfo, QThread, pyqtSignal, QSettings

from worktools.base_plugin import BasePlugin

class DeduplicationWorker(QThread):
    """Excel去重工作线程"""
    
    progress_updated = pyqtSignal(int, str)
    data_processed = pyqtSignal(object)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, file_path, deduplication_settings):
        super().__init__()
        self.file_path = file_path
        self.deduplication_settings = deduplication_settings
        
    def run(self):
        """执行Excel去重"""
        try:
            self.progress_updated.emit(10, "正在读取数据文件...")
            
            # 读取Excel文件
            df = pd.read_excel(self.file_path)
            self.progress_updated.emit(20, f"成功读取 {len(df)} 行数据，{len(df.columns)} 列")
            
            # 应用设置
            processed_df = self._apply_deduplication(df)
            
            # 计算去重统计
            original_count = len(df)
            deduplicated_count = len(processed_df)
            removed_count = original_count - deduplicated_count
            
            self.progress_updated.emit(90, "正在完成处理...")
            
            # 返回结果
            result = {
                '原始数据': df,
                '去重数据': processed_df,
                '原始行数': original_count,
                '去重后行数': deduplicated_count,
                '删除行数': removed_count,
                '删除比例': f"{removed_count/original_count*100:.2f}%" if original_count > 0 else "0%"
            }
            
            self.progress_updated.emit(100, "处理完成")
            self.data_processed.emit(result)
            
        except Exception as e:
            self.error_occurred.emit(f"去重处理失败: {str(e)}")
    
    def _apply_deduplication(self, df):
        """应用去重设置"""
        settings = self.deduplication_settings
        
        # 获取去重列
        if settings['deduplication_mode'] == '全行匹配':
            # 全行去重
            deduplicated_df = df.drop_duplicates()
        elif settings['deduplication_mode'] == '指定列':
            # 指定列去重
            columns = settings['deduplication_columns']
            if columns:
                # 只使用存在的列
                existing_columns = [col for col in columns if col in df.columns]
                if existing_columns:
                    deduplicated_df = df.drop_duplicates(subset=existing_columns)
                else:
                    self.error_occurred.emit("指定的列不存在于数据中")
                    return df
            else:
                deduplicated_df = df
        else:
            deduplicated_df = df
            
        # 保留首条或最后一条
        if settings['keep_method'] == '保留最后一条':
            deduplicated_df = deduplicated_df.drop_duplicates(keep='last')
        else:
            deduplicated_df = deduplicated_df.drop_duplicates(keep='first')
            
        return deduplicated_df.reset_index(drop=True)

class DeduplicationSettingsDialog(QDialog):
    """去重设置对话框"""
    
    def __init__(self, df_columns, current_settings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("去重设置")
        self.setModal(True)
        self.resize(500, 400)
        
        self.df_columns = df_columns
        
        layout = QVBoxLayout(self)
        
        # 创建表单
        form_layout = QFormLayout()
        
        # 去重模式
        self.deduplication_mode_combo = QComboBox()
        self.deduplication_mode_combo.addItems(["全行匹配", "指定列"])
        self.deduplication_mode_combo.setCurrentText(current_settings.get('deduplication_mode', '全行匹配'))
        form_layout.addRow("去重模式:", self.deduplication_mode_combo)
        
        # 去重列
        columns_group = QGroupBox("选择去重列 (按住Ctrl多选)")
        columns_layout = QVBoxLayout(columns_group)
        
        self.columns_list = QListWidget()
        self.columns_list.setSelectionMode(QListWidget.MultiSelection)
        
        # 添加列名
        for column in df_columns:
            item = QListWidgetItem(column)
            self.columns_list.addItem(item)
            
        columns_layout.addWidget(self.columns_list)
        form_layout.addRow(columns_group)
        
        # 保留方法
        self.keep_method_combo = QComboBox()
        self.keep_method_combo.addItems(["保留首条", "保留最后一条"])
        self.keep_method_combo.setCurrentText(current_settings.get('keep_method', '保留首条'))
        form_layout.addRow("保留方法:", self.keep_method_combo)
        
        # 忽略大小写
        self.ignore_case_check = QCheckBox()
        self.ignore_case_check.setChecked(current_settings.get('ignore_case', False))
        form_layout.addRow("忽略大小写:", self.ignore_case_check)
        
        # 忽略空格
        self.ignore_spaces_check = QCheckBox()
        self.ignore_spaces_check.setChecked(current_settings.get('ignore_spaces', False))
        form_layout.addRow("忽略空格:", self.ignore_spaces_check)
        
        layout.addLayout(form_layout)
        
        # 按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        # 连接信号
        self.deduplication_mode_combo.currentTextChanged.connect(self._on_mode_changed)
        self._on_mode_changed(self.deduplication_mode_combo.currentText())
        
    def _on_mode_changed(self, mode):
        """处理模式变化"""
        self.columns_list.setEnabled(mode == "指定列")
        
    def get_settings(self):
        """获取设置"""
        # 获取选中的列
        selected_columns = []
        if self.deduplication_mode_combo.currentText() == "指定列":
            for i in range(self.columns_list.count()):
                item = self.columns_list.item(i)
                if item.isSelected():
                    selected_columns.append(item.text())
        
        return {
            'deduplication_mode': self.deduplication_mode_combo.currentText(),
            'deduplication_columns': selected_columns,
            'keep_method': self.keep_method_combo.currentText(),
            'ignore_case': self.ignore_case_check.isChecked(),
            'ignore_spaces': self.ignore_spaces_check.isChecked()
        }

class ExcelDeduplication(BasePlugin):
    """
    Excel去重工具插件
    
    用于Excel表格数据的去重处理
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._name = "Excel去重工具"
        self._description = "用于Excel表格数据的去重处理"
        self.data = None
        self.deduplicated_data = None
        self.settings = None
        
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
        return "数据处理"
        
    def _setup_ui(self):
        """设置用户界面"""
        # 创建主布局
        main_layout = QVBoxLayout(self)
        
        # 创建选项卡
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # 添加各个功能选项卡
        self._setup_file_processing_tab()
        self._setup_data_preview_tab()
        self._setup_settings_tab()
        
        # 加载设置
        self._load_settings()
        
    def _setup_file_processing_tab(self):
        """设置文件处理选项卡"""
        process_widget = QWidget()
        layout = QVBoxLayout(process_widget)
        
        # 文件选择
        file_group = QGroupBox("数据文件")
        file_layout = QVBoxLayout(file_group)
        
        path_layout = QHBoxLayout()
        self.file_path_edit = QLineEdit()
        self.file_path_edit.setPlaceholderText("选择要处理的Excel文件...")
        path_layout.addWidget(self.file_path_edit)
        
        browse_button = QPushButton("浏览")
        browse_button.clicked.connect(self._browse_file)
        path_layout.addWidget(browse_button)
        
        file_layout.addLayout(path_layout)
        layout.addWidget(file_group)
        
        # 处理按钮
        button_layout = QHBoxLayout()
        
        settings_button = QPushButton("去重设置")
        settings_button.clicked.connect(self._show_settings_dialog)
        button_layout.addWidget(settings_button)
        
        deduplicate_button = QPushButton("执行去重")
        deduplicate_button.clicked.connect(self._deduplicate_data)
        button_layout.addWidget(deduplicate_button)
        
        save_button = QPushButton("保存结果")
        save_button.clicked.connect(self._save_results)
        save_button.setEnabled(False)
        self.save_button = save_button
        button_layout.addWidget(save_button)
        
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        # 进度
        progress_group = QGroupBox("处理进度")
        progress_layout = QVBoxLayout(progress_group)
        
        self.progress_bar = QProgressBar()
        progress_layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("就绪")
        progress_layout.addWidget(self.status_label)
        
        layout.addWidget(progress_group)
        
        # 统计信息
        stats_group = QGroupBox("去重统计")
        stats_layout = QGridLayout(stats_group)
        
        self.original_rows_label = QLabel("原始行数: -")
        stats_layout.addWidget(self.original_rows_label, 0, 0)
        
        self.deduplicated_rows_label = QLabel("去重后行数: -")
        stats_layout.addWidget(self.deduplicated_rows_label, 0, 1)
        
        self.removed_rows_label = QLabel("删除行数: -")
        stats_layout.addWidget(self.removed_rows_label, 1, 0)
        
        self.removed_percentage_label = QLabel("删除比例: -")
        stats_layout.addWidget(self.removed_percentage_label, 1, 1)
        
        layout.addWidget(stats_group)
        
        self.tab_widget.addTab(process_widget, "数据处理")
        
    def _setup_data_preview_tab(self):
        """设置数据预览选项卡"""
        # 创建一个带有子选项卡的选项卡
        preview_tab = QWidget()
        preview_layout = QHBoxLayout(preview_tab)
        
        # 原始数据预览
        original_group = QGroupBox("原始数据")
        original_layout = QVBoxLayout(original_group)
        
        self.original_table = QTableWidget()
        self.original_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.original_table.setAlternatingRowColors(True)
        original_layout.addWidget(self.original_table)
        
        # 去重后数据预览
        deduplicated_group = QGroupBox("去重后数据")
        deduplicated_layout = QVBoxLayout(deduplicated_group)
        
        self.deduplicated_table = QTableWidget()
        self.deduplicated_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.deduplicated_table.setAlternatingRowColors(True)
        deduplicated_layout.addWidget(self.deduplicated_table)
        
        # 添加到布局
        preview_layout.addWidget(original_group)
        preview_layout.addWidget(deduplicated_group)
        
        self.tab_widget.addTab(preview_tab, "数据对比")
        
    def _setup_settings_tab(self):
        """设置设置选项卡"""
        settings_widget = QWidget()
        layout = QVBoxLayout(settings_widget)
        
        # 当前设置显示
        settings_group = QGroupBox("当前去重设置")
        settings_layout = QVBoxLayout(settings_group)
        
        self.settings_display = QTextEdit()
        self.settings_display.setReadOnly(True)
        settings_layout.addWidget(self.settings_display)
        
        layout.addWidget(settings_group)
        
        # 更新设置按钮
        update_button = QPushButton("更新设置")
        update_button.clicked.connect(self._show_settings_dialog)
        layout.addWidget(update_button)
        
        self.tab_widget.addTab(settings_widget, "去重设置")
        
    def _browse_file(self):
        """浏览文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择数据文件", "", "Excel文件 (*.xlsx *.xls)"
        )
        
        if file_path:
            self.file_path_edit.setText(file_path)
            
    def _show_settings_dialog(self):
        """显示设置对话框"""
        if not self.file_path_edit.text():
            QMessageBox.warning(self, "警告", "请先选择数据文件")
            return
            
        try:
            # 读取文件以获取列名
            df = pd.read_excel(self.file_path_edit.text())
            columns = df.columns.tolist()
            
            # 显示设置对话框
            dialog = DeduplicationSettingsDialog(columns, self.settings or {}, self)
            
            if dialog.exec_() == QDialog.Accepted:
                # 保存设置
                self.settings = dialog.get_settings()
                
                # 保存到应用设置
                for key, value in self.settings.items():
                    self.app_settings.setValue(key, value)
                    
                self.app_settings.sync()
                
                # 更新显示
                self._update_settings_display()
                
                QMessageBox.information(self, "设置", "设置已更新")
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"读取文件失败: {str(e)}")
            
    def _load_settings(self):
        """加载设置"""
        self.app_settings = QSettings("WorkTools", "ExcelDeduplication")
        
        # 默认设置
        self.settings = {
            'deduplication_mode': '全行匹配',
            'deduplication_columns': [],
            'keep_method': '保留首条',
            'ignore_case': False,
            'ignore_spaces': False
        }
        
        # 从设置中加载
        for key, default_value in self.settings.items():
            value = self.app_settings.value(key, default_value)
            self.settings[key] = value
            
        self._update_settings_display()
        
    def _update_settings_display(self):
        """更新设置显示"""
        settings_text = f"""去重模式: {self.settings.get('deduplication_mode', '全行匹配')}
去重列: {', '.join(self.settings.get('deduplication_columns', []))}
保留方法: {self.settings.get('keep_method', '保留首条')}
忽略大小写: {self.settings.get('ignore_case', False)}
忽略空格: {self.settings.get('ignore_spaces', False)}"""
        
        self.settings_display.setPlainText(settings_text)
        
    def _deduplicate_data(self):
        """执行去重"""
        file_path = self.file_path_edit.text()
        
        if not file_path or not os.path.exists(file_path):
            QMessageBox.warning(self, "警告", "请选择有效的数据文件")
            return
            
        # 重置进度
        self.progress_bar.setValue(0)
        self.status_label.setText("开始处理...")
        
        # 创建并启动工作线程
        self.worker = DeduplicationWorker(file_path, self.settings)
        self.worker.progress_updated.connect(self._on_progress_updated)
        self.worker.data_processed.connect(self._on_data_processed)
        self.worker.error_occurred.connect(self._on_error_occurred)
        self.worker.start()
        
    def _on_progress_updated(self, value, message):
        """更新进度"""
        self.progress_bar.setValue(value)
        self.status_label.setText(message)
        
    def _on_data_processed(self, result):
        """处理完成"""
        self.data = result['原始数据']
        self.deduplicated_data = result['去重数据']
        
        # 更新统计信息
        self.original_rows_label.setText(f"原始行数: {result['原始行数']}")
        self.deduplicated_rows_label.setText(f"去重后行数: {result['去重后行数']}")
        self.removed_rows_label.setText(f"删除行数: {result['删除行数']}")
        self.removed_percentage_label.setText(f"删除比例: {result['删除比例']}")
        
        # 更新数据表
        self._update_data_tables()
        
        # 启用保存按钮
        self.save_button.setEnabled(True)
        
        QMessageBox.information(self, "完成", "数据去重完成")
        
    def _on_error_occurred(self, error_message):
        """处理错误"""
        QMessageBox.critical(self, "错误", error_message)
        
    def _update_data_tables(self):
        """更新数据表"""
        if self.data is None or self.deduplicated_data is None:
            return
            
        # 限制显示行数
        max_rows = 100
        
        # 原始数据
        original_display = self.data.head(max_rows)
        self.original_table.setRowCount(len(original_display))
        self.original_table.setColumnCount(len(original_display.columns))
        self.original_table.setHorizontalHeaderLabels(original_display.columns)
        
        for i in range(len(original_display)):
            for j in range(len(original_display.columns)):
                value = str(original_display.iloc[i, j])
                item = QTableWidgetItem(value)
                self.original_table.setItem(i, j, item)
                
        if len(self.data) > max_rows:
            self.original_table.setRowCount(max_rows + 1)
            info_item = QTableWidgetItem(f"...(共 {len(self.data)} 行，仅显示前 {max_rows} 行)")
            info_item.setBackground(QColor(240, 240, 240))
            self.original_table.setItem(max_rows, 0, info_item)
            
        # 去重后数据
        deduplicated_display = self.deduplicated_data.head(max_rows)
        self.deduplicated_table.setRowCount(len(deduplicated_display))
        self.deduplicated_table.setColumnCount(len(deduplicated_display.columns))
        self.deduplicated_table.setHorizontalHeaderLabels(deduplicated_display.columns)
        
        for i in range(len(deduplicated_display)):
            for j in range(len(deduplicated_display.columns)):
                value = str(deduplicated_display.iloc[i, j])
                item = QTableWidgetItem(value)
                self.deduplicated_table.setItem(i, j, item)
                
        if len(self.deduplicated_data) > max_rows:
            self.deduplicated_table.setRowCount(max_rows + 1)
            info_item = QTableWidgetItem(f"...(共 {len(self.deduplicated_data)} 行，仅显示前 {max_rows} 行)")
            info_item.setBackground(QColor(240, 240, 240))
            self.deduplicated_table.setItem(max_rows, 0, info_item)
                
    def _save_results(self):
        """保存结果"""
        if self.deduplicated_data is None:
            QMessageBox.warning(self, "警告", "没有可保存的数据")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存去重结果", "", "Excel文件 (*.xlsx)"
        )
        
        if file_path:
            try:
                self.deduplicated_data.to_excel(file_path, index=False)
                QMessageBox.information(self, "成功", f"结果已保存到: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存失败: {str(e)}")
                
    def save_state(self) -> dict:
        """保存插件状态"""
        state = {
            'current_tab': self.tab_widget.currentIndex(),
            'file_path': self.file_path_edit.text()
        }
        return state
        
    def restore_state(self, state: dict):
        """恢复插件状态"""
        if 'current_tab' in state:
            self.tab_widget.setCurrentIndex(state['current_tab'])
            
        if 'file_path' in state:
            self.file_path_edit.setText(state['file_path'])