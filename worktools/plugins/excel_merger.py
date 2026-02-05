# -*- coding: utf-8 -*-

"""
Excel表格合并工具插件
用于处理具有多层级结构的Excel表格合并
"""

import os
import pandas as pd
import re
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

class ExcelMergerWorker(QThread):
    """Excel合并工作线程"""
    
    progress_updated = pyqtSignal(int, str)
    data_processed = pyqtSignal(object)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, file_paths, merge_settings):
        super().__init__()
        self.file_paths = file_paths
        self.merge_settings = merge_settings
        
    def run(self):
        """执行Excel合并"""
        try:
            merge_mode = self.merge_settings.get('merge_mode', '多文件合并')
            
            if merge_mode == '多文件合并':
                self._merge_multiple_files()
            else:
                self._merge_single_file_sheets()
                
        except Exception as e:
            self.error_occurred.emit(f"合并失败: {str(e)}")
            
    def _merge_multiple_files(self):
        """合并多个文件"""
        self.progress_updated.emit(5, "开始处理多个文件...")
        
        all_dataframes = []
        total_files = len(self.file_paths)
        
        for i, file_path in enumerate(self.file_paths):
            self.progress_updated.emit(
                5 + (i * 80 // total_files), 
                f"正在处理文件 {i+1}/{total_files}: {os.path.basename(file_path)}"
            )
            
            try:
                # 读取Excel文件
                df = self._process_excel_file(file_path)
                if df is not None and not df.empty:
                    all_dataframes.append(df)
            except Exception as e:
                self.error_occurred.emit(f"处理文件 {file_path} 失败: {str(e)}")
                continue
        
        if not all_dataframes:
            self.error_occurred.emit("没有成功处理任何文件")
            return
            
        self.progress_updated.emit(90, "正在合并数据...")
        
        # 合并所有数据框
        if len(all_dataframes) == 1:
            merged_df = all_dataframes[0]
        else:
            merged_df = pd.concat(all_dataframes, ignore_index=True)
        
        self.progress_updated.emit(95, "正在生成结果...")
        
        # 返回结果
        result = {
            '合并数据': merged_df,
            '文件数量': len(self.file_paths),
            '成功处理': len(all_dataframes)
        }
        
        self.progress_updated.emit(100, "处理完成")
        self.data_processed.emit(result)
        
    def _merge_single_file_sheets(self):
        """合并单个文件的多个工作表"""
        file_path = self.file_paths[0]  # 只使用第一个文件
        self.progress_updated.emit(5, f"开始处理文件: {os.path.basename(file_path)}")
        
        try:
            # 读取Excel文件的所有工作表
            xls = pd.ExcelFile(file_path)
            sheet_names = xls.sheet_names
            
            if len(sheet_names) == 0:
                self.error_occurred.emit("文件中没有工作表")
                return
                
            all_dataframes = []
            total_sheets = len(sheet_names)
            
            for i, sheet_name in enumerate(sheet_names):
                self.progress_updated.emit(
                    5 + (i * 80 // total_sheets), 
                    f"正在处理工作表 {i+1}/{total_sheets}: {sheet_name}"
                )
                
                try:
                    # 读取工作表
                    df = pd.read_excel(file_path, sheet_name=sheet_name)
                    
                    # 应用设置
                    df = self._apply_settings(df)
                    
                    # 添加工作表名列
                    if self.merge_settings.get('add_sheet_name', True):
                        sheet_column = self.merge_settings.get('sheet_name_column', '来源工作表')
                        df.insert(0, sheet_column, [sheet_name] * len(df))
                    
                    if df is not None and not df.empty:
                        all_dataframes.append(df)
                except Exception as e:
                    self.error_occurred.emit(f"处理工作表 {sheet_name} 失败: {str(e)}")
                    continue
            
            if not all_dataframes:
                self.error_occurred.emit("没有成功处理任何工作表")
                return
                
            self.progress_updated.emit(90, "正在合并工作表...")
            
            # 合并所有数据框
            if len(all_dataframes) == 1:
                merged_df = all_dataframes[0]
            else:
                merged_df = pd.concat(all_dataframes, ignore_index=True)
            
            self.progress_updated.emit(95, "正在生成结果...")
            
            # 返回结果
            result = {
                '合并数据': merged_df,
                '文件数量': 1,
                '工作表数量': len(sheet_names),
                '成功处理': len(all_dataframes)
            }
            
            self.progress_updated.emit(100, "处理完成")
            self.data_processed.emit(result)
            
        except Exception as e:
            self.error_occurred.emit(f"合并失败: {str(e)}")
    
    def _process_excel_file(self, file_path):
        """处理单个Excel文件"""
        # 读取Excel文件
        xls = pd.ExcelFile(file_path)
        
        # 如果有多个工作表，只使用第一个
        if len(xls.sheet_names) > 0:
            sheet_name = xls.sheet_names[0]
            
            # 尝试读取数据
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            
            # 应用设置
            df = self._apply_settings(df)
            
            return df
        
        return None
    
    def _apply_settings(self, df):
        """应用合并设置"""
        settings = self.merge_settings
        
        # 跳过顶部标题行
        if settings['skip_header_rows'] > 0:
            df = df.iloc[settings['skip_header_rows']:].reset_index(drop=True)
        
        # 设置列标题
        if settings['use_custom_header'] and settings['header_row'] < len(df):
            df.columns = df.iloc[settings['header_row']]
            df = df.iloc[settings['header_row']+1:].reset_index(drop=True)
        
        # 跳过底部合计行
        if settings['skip_footer_rows'] > 0:
            df = df.iloc[:-settings['skip_footer_rows']]
        
        # 重置索引
        df = df.reset_index(drop=True)
        
        # 删除完全空白的行和列
        df = df.dropna(how='all').dropna(axis=1, how='all')
        
        return df

class ExcelMergeSettingsDialog(QDialog):
    """Excel合并设置对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Excel合并设置")
        self.setModal(True)
        self.resize(500, 500)
        
        layout = QVBoxLayout(self)
        
        # 创建表单
        form_layout = QFormLayout()
        
        # 合并模式
        self.merge_mode_combo = QComboBox()
        self.merge_mode_combo.addItems(["多文件合并", "单文件多工作表合并"])
        self.merge_mode_combo.currentTextChanged.connect(self._on_merge_mode_changed)
        form_layout.addRow("合并模式:", self.merge_mode_combo)
        
        # 顶部跳过行数
        self.skip_header_rows_spin = QSpinBox()
        self.skip_header_rows_spin.setRange(0, 100)
        self.skip_header_rows_spin.setValue(1)
        self.skip_header_rows_spin.setSpecialValueText("无")
        form_layout.addRow("顶部标题行数:", self.skip_header_rows_spin)
        
        # 使用自定义标题行
        self.use_custom_header_check = QCheckBox("使用自定义标题行")
        self.use_custom_header_check.setChecked(False)
        form_layout.addRow(self.use_custom_header_check)
        
        # 标题行位置
        self.header_row_spin = QSpinBox()
        self.header_row_spin.setRange(0, 100)
        self.header_row_spin.setValue(0)
        form_layout.addRow("标题行位置:", self.header_row_spin)
        
        # 底部跳过行数
        self.skip_footer_rows_spin = QSpinBox()
        self.skip_footer_rows_spin.setRange(0, 100)
        self.skip_footer_rows_spin.setValue(1)
        self.skip_footer_rows_spin.setSpecialValueText("无")
        form_layout.addRow("底部合计行数:", self.skip_footer_rows_spin)
        
        # 文件/工作表源信息
        self.source_info_group = QGroupBox("源信息")
        source_layout = QVBoxLayout(self.source_info_group)
        
        # 文件模式
        self.file_options_widget = QWidget()
        file_layout = QVBoxLayout(self.file_options_widget)
        
        self.add_filename_check = QCheckBox("添加文件名列")
        self.add_filename_check.setChecked(True)
        file_layout.addWidget(self.add_filename_check)
        
        # 文件名列名
        filename_layout = QHBoxLayout()
        filename_layout.addWidget(QLabel("文件名列名:"))
        self.filename_column_edit = QLineEdit("来源文件")
        filename_layout.addWidget(self.filename_column_edit)
        file_layout.addLayout(filename_layout)
        
        source_layout.addWidget(self.file_options_widget)
        
        # 工作表模式
        self.sheet_options_widget = QWidget()
        sheet_layout = QVBoxLayout(self.sheet_options_widget)
        
        self.add_sheet_name_check = QCheckBox("添加工作表名列")
        self.add_sheet_name_check.setChecked(True)
        sheet_layout.addWidget(self.add_sheet_name_check)
        
        # 工作表名列名
        sheet_name_layout = QHBoxLayout()
        sheet_name_layout.addWidget(QLabel("工作表名列名:"))
        self.sheet_name_column_edit = QLineEdit("来源工作表")
        sheet_name_layout.addWidget(self.sheet_name_column_edit)
        sheet_layout.addLayout(sheet_name_layout)
        
        source_layout.addWidget(self.sheet_options_widget)
        
        # 默认显示工作表选项
        self.sheet_options_widget.hide()
        
        form_layout.addRow(self.source_info_group)
        
        layout.addLayout(form_layout)
        
        # 按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        # 连接信号
        self.use_custom_header_check.toggled.connect(self.header_row_spin.setEnabled)
        self.header_row_spin.setEnabled(self.use_custom_header_check.isChecked())
        
    def _on_merge_mode_changed(self, mode):
        """处理合并模式变化"""
        if mode == "多文件合并":
            self.file_options_widget.show()
            self.sheet_options_widget.hide()
        else:
            self.file_options_widget.hide()
            self.sheet_options_widget.show()
        
    def get_settings(self):
        """获取设置"""
        return {
            'merge_mode': str(self.merge_mode_combo.currentText()),
            'skip_header_rows': int(self.skip_header_rows_spin.value()),
            'use_custom_header': bool(self.use_custom_header_check.isChecked()),
            'header_row': int(self.header_row_spin.value()),
            'skip_footer_rows': int(self.skip_footer_rows_spin.value()),
            'add_filename': bool(self.add_filename_check.isChecked()),
            'filename_column': str(self.filename_column_edit.text()),
            'add_sheet_name': bool(self.add_sheet_name_check.isChecked()),
            'sheet_name_column': str(self.sheet_name_column_edit.text())
        }

class ExcelMerger(BasePlugin):
    """
    Excel表格合并工具插件
    
    用于处理具有多层级结构的Excel表格合并
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._name = "Excel合并工具"
        self._description = "用于处理具有多层级结构的Excel表格合并"
        self.data = None
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
        self._setup_file_selection_tab()
        self._setup_preview_tab()
        self._setup_settings_tab()
        
        # 加载设置
        self._load_settings()
        
    def _setup_file_selection_tab(self):
        """设置文件选择选项卡"""
        selection_widget = QWidget()
        layout = QVBoxLayout(selection_widget)
        
        # 合并模式选择
        mode_group = QGroupBox("合并模式")
        mode_layout = QVBoxLayout(mode_group)
        
        self.merge_mode_combo = QComboBox()
        self.merge_mode_combo.addItems(["多文件合并", "单文件多工作表合并"])
        self.merge_mode_combo.currentTextChanged.connect(self._on_merge_mode_changed)
        mode_layout.addWidget(self.merge_mode_combo)
        
        layout.addWidget(mode_group)
        
        # 多文件合并选项
        self.files_group = QGroupBox("文件选择")
        files_layout = QVBoxLayout(self.files_group)
        
        # 文件列表
        self.file_list = QListWidget()
        self.file_list.setAlternatingRowColors(True)
        files_layout.addWidget(self.file_list)
        
        # 按钮布局
        file_button_layout = QHBoxLayout()
        
        add_files_button = QPushButton("添加文件")
        add_files_button.clicked.connect(self._add_files)
        file_button_layout.addWidget(add_files_button)
        
        add_folder_button = QPushButton("添加文件夹")
        add_folder_button.clicked.connect(self._add_folder)
        file_button_layout.addWidget(add_folder_button)
        
        clear_button = QPushButton("清空列表")
        clear_button.clicked.connect(self._clear_file_list)
        file_button_layout.addWidget(clear_button)
        
        files_layout.addLayout(file_button_layout)
        layout.addWidget(self.files_group)
        
        # 单文件多工作表选项
        self.single_file_group = QGroupBox("文件选择")
        single_file_layout = QVBoxLayout(self.single_file_group)
        
        # 文件路径
        path_layout = QHBoxLayout()
        self.single_file_edit = QLineEdit()
        self.single_file_edit.setPlaceholderText("选择要处理的Excel文件...")
        path_layout.addWidget(self.single_file_edit)
        
        browse_single_button = QPushButton("浏览")
        browse_single_button.clicked.connect(self._browse_single_file)
        path_layout.addWidget(browse_single_button)
        
        single_file_layout.addLayout(path_layout)
        
        # 工作表预览
        self.sheets_preview = QListWidget()
        self.sheets_preview.setAlternatingRowColors(True)
        single_file_layout.addWidget(self.sheets_preview)
        
        # 默认隐藏工作表选项
        self.single_file_group.hide()
        
        layout.addWidget(self.single_file_group)
        
        # 操作按钮
        operation_layout = QHBoxLayout()
        
        settings_button = QPushButton("合并设置")
        settings_button.clicked.connect(self._show_settings_dialog)
        operation_layout.addWidget(settings_button)
        
        merge_button = QPushButton("执行合并")
        merge_button.clicked.connect(self._merge_files)
        operation_layout.addWidget(merge_button)
        
        save_button = QPushButton("保存结果")
        save_button.clicked.connect(self._save_results)
        save_button.setEnabled(False)
        self.save_button = save_button
        operation_layout.addWidget(save_button)
        
        operation_layout.addStretch()
        
        layout.addLayout(operation_layout)
        
        # 进度
        progress_group = QGroupBox("处理进度")
        progress_layout = QVBoxLayout(progress_group)
        
        self.progress_bar = QProgressBar()
        progress_layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("就绪")
        progress_layout.addWidget(self.status_label)
        
        layout.addWidget(progress_group)
        
        self.tab_widget.addTab(selection_widget, "合并选择")
        
    def _on_merge_mode_changed(self, mode):
        """处理合并模式变化"""
        if mode == "多文件合并":
            self.files_group.show()
            self.single_file_group.hide()
        else:
            self.files_group.hide()
            self.single_file_group.show()
            
    def _browse_single_file(self):
        """浏览单个文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择Excel文件", "", "Excel文件 (*.xlsx *.xls)"
        )
        
        if file_path:
            self.single_file_edit.setText(file_path)
            self._preview_sheets(file_path)
        
    def _setup_preview_tab(self):
        """设置预览选项卡"""
        preview_widget = QWidget()
        layout = QVBoxLayout(preview_widget)
        
        # 预览表格
        self.preview_table = QTableWidget()
        self.preview_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.preview_table.setAlternatingRowColors(True)
        layout.addWidget(self.preview_table)
        
        self.tab_widget.addTab(preview_widget, "数据预览")
        
    def _setup_settings_tab(self):
        """设置设置选项卡"""
        settings_widget = QWidget()
        layout = QVBoxLayout(settings_widget)
        
        # 当前设置显示
        settings_group = QGroupBox("当前合并设置")
        settings_layout = QVBoxLayout(settings_group)
        
        self.settings_display = QTextEdit()
        self.settings_display.setReadOnly(True)
        settings_layout.addWidget(self.settings_display)
        
        layout.addWidget(settings_group)
        
        # 更新设置按钮
        update_button = QPushButton("更新设置")
        update_button.clicked.connect(self._show_settings_dialog)
        layout.addWidget(update_button)
        
        self.tab_widget.addTab(settings_widget, "合并设置")
        
    def _load_settings(self):
        """加载设置"""
        self.app_settings = QSettings("WorkTools", "ExcelMerger")
        
        # 默认设置
        self.settings = {
            'merge_mode': '多文件合并',
            'skip_header_rows': 1,
            'use_custom_header': False,
            'header_row': 0,
            'skip_footer_rows': 1,
            'add_filename': True,
            'filename_column': '来源文件',
            'add_sheet_name': True,
            'sheet_name_column': '来源工作表'
        }
        
        # 从设置中加载
        for key, default_value in self.settings.items():
            value = self.app_settings.value(key, default_value)
            # 确保布尔值保持正确的类型
            if isinstance(default_value, bool):
                if isinstance(value, str):
                    value = value.lower() in ('true', '1', 'yes')
                elif not isinstance(value, bool):
                    value = bool(value)
            self.settings[key] = value
            
        self._update_settings_display()
        
        # 设置合并模式
        if hasattr(self, 'merge_mode_combo'):
            self.merge_mode_combo.setCurrentText(self.settings['merge_mode'])
            self._on_merge_mode_changed(self.settings['merge_mode'])
        
    def _update_settings_display(self):
        """更新设置显示"""
        settings_text = f"""合并模式: {self.settings.get('merge_mode', '多文件合并')}
顶部标题行数: {self.settings.get('skip_header_rows', 1)}
使用自定义标题行: {self.settings.get('use_custom_header', False)}
标题行位置: {self.settings.get('header_row', 0)}
底部合计行数: {self.settings.get('skip_footer_rows', 1)}
添加文件名列: {self.settings.get('add_filename', True)}
文件名列名: {self.settings.get('filename_column', '来源文件')}
添加工作表名列: {self.settings.get('add_sheet_name', True)}
工作表名列名: {self.settings.get('sheet_name_column', '来源工作表')}"""
        
        self.settings_display.setPlainText(settings_text)
        
    def _add_files(self):
        """添加文件"""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "选择Excel文件", "", "Excel文件 (*.xlsx *.xls)"
        )
        
        if file_paths:
            for file_path in file_paths:
                item = QListWidgetItem(os.path.basename(file_path))
                item.setData(Qt.UserRole, file_path)
                self.file_list.addItem(item)
                
    def _add_folder(self):
        """添加文件夹"""
        folder_path = QFileDialog.getExistingDirectory(self, "选择文件夹")
        
        if folder_path:
            for file_name in os.listdir(folder_path):
                if file_name.endswith(('.xlsx', '.xls')):
                    file_path = os.path.join(folder_path, file_name)
                    item = QListWidgetItem(file_name)
                    item.setData(Qt.UserRole, file_path)
                    self.file_list.addItem(item)
                    
    def _clear_file_list(self):
        """清空文件列表"""
        self.file_list.clear()
        
    def _show_settings_dialog(self):
        """显示设置对话框"""
        dialog = ExcelMergeSettingsDialog(self)
        
        # 设置当前值
        dialog.skip_header_rows_spin.setValue(int(self.settings['skip_header_rows']))
        dialog.use_custom_header_check.setChecked(bool(self.settings['use_custom_header']))
        dialog.header_row_spin.setValue(int(self.settings['header_row']))
        dialog.skip_footer_rows_spin.setValue(int(self.settings['skip_footer_rows']))
        dialog.add_filename_check.setChecked(bool(self.settings['add_filename']))
        dialog.filename_column_edit.setText(str(self.settings['filename_column']))
        
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
            
    def _merge_files(self):
        """合并文件或工作表"""
        merge_mode = self.merge_mode_combo.currentText()
        
        if merge_mode == "多文件合并":
            self._merge_multiple_files()
        else:
            self._merge_single_file_sheets()
            
    def _merge_multiple_files(self):
        """合并多个文件"""
        if self.file_list.count() == 0:
            QMessageBox.warning(self, "警告", "请先添加要合并的文件")
            return
            
        # 获取文件路径
        file_paths = []
        for i in range(self.file_list.count()):
            item = self.file_list.item(i)
            file_paths.append(item.data(Qt.UserRole))
            
        # 重置进度
        self.progress_bar.setValue(0)
        self.status_label.setText("开始处理多个文件...")
        
        # 创建并启动工作线程
        self.worker = ExcelMergerWorker(file_paths, self.settings)
        self.worker.progress_updated.connect(self._on_progress_updated)
        self.worker.data_processed.connect(self._on_data_processed)
        self.worker.error_occurred.connect(self._on_error_occurred)
        self.worker.start()
        
    def _merge_single_file_sheets(self):
        """合并单个文件的多个工作表"""
        file_path = self.single_file_edit.text()
        
        if not file_path or not os.path.exists(file_path):
            QMessageBox.warning(self, "警告", "请先选择要处理的Excel文件")
            return
            
        # 重置进度
        self.progress_bar.setValue(0)
        self.status_label.setText("开始处理工作表...")
        
        # 创建并启动工作线程
        file_paths = [file_path]  # 传递单个文件路径
        self.worker = ExcelMergerWorker(file_paths, self.settings)
        self.worker.progress_updated.connect(self._on_progress_updated)
        self.worker.data_processed.connect(self._on_data_processed)
        self.worker.error_occurred.connect(self._on_error_occurred)
        self.worker.start()
        
    def _preview_sheets(self, file_path):
        """预览Excel文件中的工作表"""
        try:
            # 清空当前列表
            self.sheets_preview.clear()
            
            # 读取Excel文件
            xls = pd.ExcelFile(file_path)
            sheet_names = xls.sheet_names
            
            # 添加到列表
            for sheet_name in sheet_names:
                item = QListWidgetItem(sheet_name)
                self.sheets_preview.addItem(item)
                
            self.sheets_preview.repaint()
        except Exception as e:
            QMessageBox.warning(self, "警告", f"无法预览工作表: {str(e)}")
        
    def _on_progress_updated(self, value, message):
        """更新进度"""
        self.progress_bar.setValue(value)
        self.status_label.setText(message)
        
    def _on_data_processed(self, result):
        """处理完成"""
        self.data = result['合并数据']
        
        merge_mode = self.settings.get('merge_mode', '多文件合并')
        
        # 根据合并模式添加源信息列
        if merge_mode == "多文件合并" and self.settings['add_filename']:
            # 获取文件名列表
            file_names = []
            for i in range(self.file_list.count()):
                item = self.file_list.item(i)
                file_path = item.data(Qt.UserRole)
                file_names.append(os.path.basename(file_path))
                
            # 为每一行添加文件名
            rows_per_file = len(self.data) // len(file_names)
            file_name_column = []
            
            for file_name in file_names:
                file_name_column.extend([file_name] * rows_per_file)
                
            # 补充剩余行
            remaining_rows = len(self.data) - len(file_name_column)
            if remaining_rows > 0:
                file_name_column.extend([file_names[-1]] * remaining_rows)
                
            # 添加列
            self.data.insert(0, self.settings['filename_column'], file_name_column)
            
        elif merge_mode == "单文件多工作表合并" and self.settings.get('add_sheet_name', True):
            # 为每一行添加工作表名
            # 这个逻辑已经在工作线程中处理，不需要在这里重复
            pass
        
        # 更新预览
        self._update_preview_table()
        
        # 启用保存按钮
        self.save_button.setEnabled(True)
        
        # 显示完成信息
        if '工作表数量' in result:
            QMessageBox.information(
                self, "完成", 
                f"工作表合并完成！\n工作表数量: {result['工作表数量']}\n成功合并: {result['成功处理']}"
            )
        else:
            QMessageBox.information(
                self, "完成", 
                f"文件合并完成！\n处理文件数: {result['文件数量']}\n成功合并: {result['成功处理']}"
            )
        
    def _on_error_occurred(self, error_message):
        """处理错误"""
        QMessageBox.critical(self, "错误", error_message)
        
    def _update_preview_table(self):
        """更新预览表"""
        if self.data is None:
            return
            
        # 限制显示行数
        max_rows = 100
        display_data = self.data.head(max_rows)
        
        # 设置表格
        self.preview_table.setRowCount(len(display_data))
        self.preview_table.setColumnCount(len(display_data.columns))
        self.preview_table.setHorizontalHeaderLabels(display_data.columns)
        
        # 填充数据
        for i in range(len(display_data)):
            for j in range(len(display_data.columns)):
                value = str(display_data.iloc[i, j])
                item = QTableWidgetItem(value)
                self.preview_table.setItem(i, j, item)
                
        if len(self.data) > max_rows:
            self.preview_table.setRowCount(max_rows + 1)
            info_item = QTableWidgetItem(f"...(共 {len(self.data)} 行，仅显示前 {max_rows} 行)")
            info_item.setBackground(QColor(240, 240, 240))
            self.preview_table.setItem(max_rows, 0, info_item)
            
    def _save_results(self):
        """保存结果"""
        if self.data is None:
            QMessageBox.warning(self, "警告", "没有可保存的数据")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存合并结果", "", "Excel文件 (*.xlsx)"
        )
        
        if file_path:
            try:
                self.data.to_excel(file_path, index=False)
                QMessageBox.information(self, "成功", f"结果已保存到: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存失败: {str(e)}")
                
    def save_state(self) -> dict:
        """保存插件状态"""
        state = {
            'current_tab': self.tab_widget.currentIndex(),
            'merge_mode': self.merge_mode_combo.currentText(),
            'file_path': self.single_file_edit.text() if hasattr(self, 'single_file_edit') else ''
        }
        return state
        
    def restore_state(self, state: dict):
        """恢复插件状态"""
        if 'current_tab' in state:
            self.tab_widget.setCurrentIndex(state['current_tab'])
            
        if 'merge_mode' in state:
            self.merge_mode_combo.setCurrentText(state['merge_mode'])
            self._on_merge_mode_changed(state['merge_mode'])
            
        if 'file_path' in state and hasattr(self, 'single_file_edit'):
            self.single_file_edit.setText(state['file_path'])