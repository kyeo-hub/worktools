# -*- coding: utf-8 -*-

"""
月汇总工具插件
用于处理运输数据的汇总和分析
"""

import os
import re
import pandas as pd
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
                           QPushButton, QLabel, QLineEdit, QGroupBox, QCheckBox,
                           QFileDialog, QMessageBox, QProgressBar, QSplitter,
                           QTableWidget, QTableWidgetItem, QHeaderView, QComboBox,
                           QTextEdit, QSpinBox, QGridLayout, QFormLayout,
                           QDialog, QDialogButtonBox, QScrollArea, QFrame, QSizePolicy)
from PyQt5.QtGui import QIcon, QFont, QStandardItemModel, QStandardItem
from PyQt5.QtCore import Qt, QDir, QFileInfo, QThread, pyqtSignal, QSettings

from worktools.base_plugin import BasePlugin

class SummaryWorker(QThread):
    """数据处理工作线程"""
    
    progress_updated = pyqtSignal(int, str)
    data_processed = pyqtSignal(object)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, file_path, confirm_transportation=True):
        super().__init__()
        self.file_path = file_path
        self.confirm_transportation = confirm_transportation
        self.settings = QSettings("WorkTools", "MonthlySummary")
        
    def run(self):
        """执行数据处理"""
        try:
            self.progress_updated.emit(10, "正在读取数据文件...")
            
            # 设置格式对齐
            pd.set_option('display.unicode.ambiguous_as_wide', True)
            pd.set_option('display.unicode.east_asian_width', True)
            
            # 读取Excel文件
            df = pd.read_excel(self.file_path)
            self.progress_updated.emit(20, f"成功读取 {len(df)} 行数据")
            
            # 车牌号正则表达式
            re_str = '([京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤青藏川宁琼使领]{1}[A-Z]{1}(([A-Z0-9]{5}[DF]{1})|([DF]{1}[A-Z0-9]{5})))|([京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤青藏川宁琼使领]{1}[A-Z]{1}[A-Z0-9]{4}[A-Z0-9挂学警港澳]{1})'
            
            # 车牌号修正映射
            plate_corrections = self.settings.value("plate_corrections", {}, type=dict)
            default_correction = '卾:鄂'  # 默认将卾修正为鄂
            
            self.progress_updated.emit(30, "正在分析运输方式...")
            
            # 处理运输方式
            def confirm_transportation(x):
                x_upper = x.upper()
                
                # 应用修正映射
                for wrong, correct in plate_corrections.items():
                    x_upper = x_upper.replace(wrong, correct)
                    
                # 应用默认修正
                for correction in default_correction.split(','):
                    if ':' in correction:
                        wrong_part, correct_part = correction.split(':')
                        x_upper = x_upper.replace(wrong_part, correct_part)
                
                matches = re.findall(re_str, x_upper)
                if matches:
                    return '汽提'
                else:
                    # 在GUI模式下，不需要手动确认，默认为装船
                    return '装船'
            
            # 如果启用确认运输方式
            if self.confirm_transportation:
                df['运输方式'] = df['提货车号'].apply(confirm_transportation)
            else:
                # 直接使用正则表达式判断
                def auto_confirm(x):
                    x_upper = x.upper()
                    for wrong, correct in plate_corrections.items():
                        x_upper = x_upper.replace(wrong, correct)
                    for correction in default_correction.split(','):
                        if ':' in correction:
                            wrong_part, correct_part = correction.split(':')
                            x_upper = x_upper.replace(wrong_part, correct_part)
                    
                    matches = re.findall(re_str, x_upper)
                    return '汽提' if matches else '装船'
                
                df['运输方式'] = df['提货车号'].apply(auto_confirm)
            
            self.progress_updated.emit(50, "正在分析运输类别...")
            
            # 读取产地到类别的映射
            category_mapping = self.settings.value("category_mapping", {}, type=dict)
            default_mapping = {
                '九江萍钢': '水运',
                '长钢': '水运',
                '广钢': '水运',
                '宁夏建龙(特钢)': '水运',
                '迁安九江': '水运',
                '萍安钢铁': '水运',
                '山西晋南': '铁运'
            }
            
            # 合并映射
            all_mapping = {**default_mapping, **category_mapping}
            
            def categorize(x):
                if x in all_mapping:
                    return all_mapping[x]
                else:
                    return '汽运'
            
            df['类别'] = df['产地'].apply(categorize)
            
            self.progress_updated.emit(70, "正在生成汇总表...")
            
            # 分类统计
            df2 = pd.pivot_table(
                df, 
                index=['类别', '产地'], 
                columns=['运输方式'], 
                values=['实发量', '实发件数'], 
                aggfunc=['sum'], 
                margins=True, 
                margins_name='合计'
            )
            
            self.progress_updated.emit(90, "正在完成处理...")
            
            # 返回结果
            result = {
                '原始数据': df,
                '汇总数据': df2
            }
            
            self.progress_updated.emit(100, "处理完成")
            self.data_processed.emit(result)
            
        except Exception as e:
            self.error_occurred.emit(f"数据处理失败: {str(e)}")

class ManualConfirmDialog(QDialog):
    """手动确认对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("确认运输方式")
        self.setModal(True)
        self.resize(400, 300)
        
        layout = QVBoxLayout(self)
        
        # 说明
        info_label = QLabel("以下提货车号无法自动判断，请确认运输方式：")
        layout.addWidget(info_label)
        
        # 滚动区域
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        self.confirm_widgets = []
        layout.addWidget(scroll_area)
        scroll_area.setWidget(scroll_widget)
        
        # 按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
    def add_confirm_item(self, text):
        """添加确认项"""
        item_widget = QFrame()
        item_layout = QHBoxLayout(item_widget)
        
        label = QLabel(f"确认 '{text}' 是否为装车？")
        item_layout.addWidget(label)
        
        combo = QComboBox()
        combo.addItems(["装船", "汽提"])
        item_layout.addWidget(combo)
        
        self.confirm_widgets.append((text, combo))
        scroll_layout.addWidget(item_widget)
        
    def get_results(self):
        """获取确认结果"""
        results = {}
        for text, combo in self.confirm_widgets:
            results[text] = combo.currentText()
        return results

class SettingsDialog(QDialog):
    """设置对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("月汇总工具设置")
        self.setModal(True)
        self.resize(500, 400)
        
        self.settings = QSettings("WorkTools", "MonthlySummary")
        
        layout = QVBoxLayout(self)
        
        # 设置选项卡
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # 车牌号修正
        self._setup_plate_correction_tab()
        
        # 产地类别映射
        self._setup_category_mapping_tab()
        
        # 按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
    def _setup_plate_correction_tab(self):
        """设置车牌号修正选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 说明
        info_label = QLabel("设置常见车牌号字符错误修正映射：")
        layout.addWidget(info_label)
        
        # 示例
        example_label = QLabel("例如：卾 → 鄂")
        example_font = example_label.font()
        example_font.setItalic(True)
        example_label.setFont(example_font)
        layout.addWidget(example_label)
        
        # 滚动区域
        scroll_area = QScrollArea()
        self.correction_widget = QWidget()
        self.correction_layout = QVBoxLayout(self.correction_widget)
        scroll_area.setWidget(self.correction_widget)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)
        
        # 添加按钮
        add_button = QPushButton("添加修正项")
        add_button.clicked.connect(lambda: self._add_correction_item())
        layout.addWidget(add_button)
        
        self.tab_widget.addTab(tab, "车牌号修正")
        
    def _setup_category_mapping_tab(self):
        """设置产地类别映射选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 说明
        info_label = QLabel("设置产地到运输类别的映射：")
        layout.addWidget(info_label)
        
        # 示例
        example_label = QLabel("例如：九江萍钢 → 水运")
        example_font = example_label.font()
        example_font.setItalic(True)
        example_label.setFont(example_font)
        layout.addWidget(example_label)
        
        # 滚动区域
        scroll_area = QScrollArea()
        self.mapping_widget = QWidget()
        self.mapping_layout = QVBoxLayout(self.mapping_widget)
        scroll_area.setWidget(self.mapping_widget)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)
        
        # 添加按钮
        add_button = QPushButton("添加映射项")
        add_button.clicked.connect(lambda: self._add_mapping_item())
        layout.addWidget(add_button)
        
        self.tab_widget.addTab(tab, "产地类别映射")
        
    def _add_correction_item(self, wrong='', correct=''):
        """添加修正项"""
        item_widget = QWidget()
        item_layout = QHBoxLayout(item_widget)
        
        wrong_edit = QLineEdit(wrong)
        wrong_edit.setPlaceholderText("错误字符")
        item_layout.addWidget(wrong_edit)
        
        label = QLabel("→")
        item_layout.addWidget(label)
        
        correct_edit = QLineEdit(correct)
        correct_edit.setPlaceholderText("正确字符")
        item_layout.addWidget(correct_edit)
        
        remove_button = QPushButton("删除")
        remove_button.clicked.connect(lambda: self._remove_item(item_widget))
        item_layout.addWidget(remove_button)
        
        self.correction_layout.addWidget(item_widget)
        
    def _add_mapping_item(self, origin='', category=''):
        """添加映射项"""
        item_widget = QWidget()
        item_layout = QHBoxLayout(item_widget)
        
        origin_edit = QLineEdit(origin)
        origin_edit.setPlaceholderText("产地")
        item_layout.addWidget(origin_edit)
        
        category_combo = QComboBox()
        category_combo.setEditable(True)
        category_combo.addItems(["水运", "铁运", "汽运"])
        if category:
            category_combo.setCurrentText(category)
        item_layout.addWidget(category_combo)
        
        remove_button = QPushButton("删除")
        remove_button.clicked.connect(lambda: self._remove_item(item_widget))
        item_layout.addWidget(remove_button)
        
        self.mapping_layout.addWidget(item_widget)
        
    def _remove_item(self, widget):
        """移除项目"""
        widget.setParent(None)
        widget.deleteLater()
        
    def accept(self):
        """接受设置"""
        # 保存修正映射
        corrections = {}
        for i in range(self.correction_layout.count()):
            item = self.correction_layout.itemAt(i).widget()
            if item:
                wrong_edit = item.findChild(QLineEdit)
                correct_edit = item.findChildren(QLineEdit)[1] if item.findChildren(QLineEdit) else None
                
                if wrong_edit and correct_edit and wrong_edit.text() and correct_edit.text():
                    corrections[wrong_edit.text()] = correct_edit.text()
                    
        self.settings.setValue("plate_corrections", corrections)
        
        # 保存类别映射
        mappings = {}
        for i in range(self.mapping_layout.count()):
            item = self.mapping_layout.itemAt(i).widget()
            if item:
                origin_edit = item.findChild(QLineEdit)
                category_combo = item.findChild(QComboBox)
                
                if origin_edit and category_combo and origin_edit.text():
                    mappings[origin_edit.text()] = category_combo.currentText()
                    
        self.settings.setValue("category_mapping", mappings)
        
        super().accept()
        
    def load_settings(self):
        """加载设置"""
        # 加载修正映射
        corrections = self.settings.value("plate_corrections", {}, type=dict)
        for wrong, correct in corrections.items():
            self._add_correction_item(wrong, correct)
            
        # 加载类别映射
        mappings = self.settings.value("category_mapping", {}, type=dict)
        for origin, category in mappings.items():
            self._add_mapping_item(origin, category)

class MonthlySummary(BasePlugin):
    """
    月汇总工具插件
    
    用于处理运输数据的汇总和分析
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._name = "月汇总工具"
        self._description = "用于处理运输数据的汇总和分析"
        self.data = None
        self.summary_data = None
        
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
        self._setup_data_processing_tab()
        self._setup_data_view_tab()
        self._setup_summary_view_tab()
        
        # 加载设置
        self._load_settings()
        
    def _setup_data_processing_tab(self):
        """设置数据处理选项卡"""
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
        
        # 处理选项
        options_layout = QHBoxLayout()
        
        self.auto_confirm_check = QCheckBox("自动确认运输方式")
        self.auto_confirm_check.setChecked(True)
        options_layout.addWidget(self.auto_confirm_check)
        
        settings_button = QPushButton("高级设置")
        settings_button.clicked.connect(self._show_settings)
        options_layout.addWidget(settings_button)
        
        options_layout.addStretch()
        
        file_layout.addLayout(options_layout)
        layout.addWidget(file_group)
        
        # 处理按钮
        button_layout = QHBoxLayout()
        
        process_button = QPushButton("处理数据")
        process_button.clicked.connect(self._process_data)
        button_layout.addWidget(process_button)
        
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
        
        self.tab_widget.addTab(process_widget, "数据处理")
        
    def _setup_data_view_tab(self):
        """设置数据查看选项卡"""
        view_widget = QWidget()
        layout = QVBoxLayout(view_widget)
        
        # 原始数据表
        self.data_table = QTableWidget()
        self.data_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.data_table.setAlternatingRowColors(True)
        layout.addWidget(self.data_table)
        
        self.tab_widget.addTab(view_widget, "原始数据")
        
    def _setup_summary_view_tab(self):
        """设置汇总查看选项卡"""
        summary_widget = QWidget()
        layout = QVBoxLayout(summary_widget)
        
        # 汇总数据表
        self.summary_table = QTableWidget()
        self.summary_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.summary_table.setAlternatingRowColors(True)
        layout.addWidget(self.summary_table)
        
        self.tab_widget.addTab(summary_widget, "汇总数据")
        
    def _browse_file(self):
        """浏览文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择数据文件", "", "Excel文件 (*.xlsx *.xls)"
        )
        
        if file_path:
            self.file_path_edit.setText(file_path)
            
    def _show_settings(self):
        """显示设置对话框"""
        dialog = SettingsDialog(self)
        dialog.load_settings()
        
        if dialog.exec_() == QDialog.Accepted:
            QMessageBox.information(self, "设置", "设置已保存")
            
    def _load_settings(self):
        """加载设置"""
        self.settings = QSettings("WorkTools", "MonthlySummary")
        
    def _process_data(self):
        """处理数据"""
        file_path = self.file_path_edit.text()
        
        if not file_path or not os.path.exists(file_path):
            QMessageBox.warning(self, "警告", "请选择有效的数据文件")
            return
            
        # 禁用处理按钮，启用进度条
        self.progress_bar.setValue(0)
        self.status_label.setText("开始处理...")
        
        # 创建并启动工作线程
        self.worker = SummaryWorker(file_path, not self.auto_confirm_check.isChecked())
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
        self.summary_data = result['汇总数据']
        
        # 更新数据表
        self._update_data_table()
        self._update_summary_table()
        
        # 启用保存按钮
        self.save_button.setEnabled(True)
        
        QMessageBox.information(self, "完成", "数据处理完成")
        
    def _on_error_occurred(self, error_message):
        """处理错误"""
        QMessageBox.critical(self, "错误", error_message)
        
    def _update_data_table(self):
        """更新数据表"""
        if self.data is None:
            return
            
        # 设置表格
        self.data_table.setRowCount(len(self.data))
        self.data_table.setColumnCount(len(self.data.columns))
        self.data_table.setHorizontalHeaderLabels(self.data.columns)
        
        # 填充数据
        for i in range(len(self.data)):
            for j in range(len(self.data.columns)):
                value = str(self.data.iloc[i, j])
                item = QTableWidgetItem(value)
                self.data_table.setItem(i, j, item)
                
    def _update_summary_table(self):
        """更新汇总表"""
        if self.summary_data is None:
            return
            
        # 重置索引以便显示
        summary_reset = self.summary_data.reset_index()
        
        # 设置表格
        self.summary_table.setRowCount(len(summary_reset))
        self.summary_table.setColumnCount(len(summary_reset.columns))
        self.summary_table.setHorizontalHeaderLabels([str(col) for col in summary_reset.columns])
        
        # 填充数据
        for i in range(len(summary_reset)):
            for j in range(len(summary_reset.columns)):
                value = str(summary_reset.iloc[i, j])
                item = QTableWidgetItem(value)
                self.summary_table.setItem(i, j, item)
                
    def _save_results(self):
        """保存结果"""
        if self.summary_data is None:
            QMessageBox.warning(self, "警告", "没有可保存的数据")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存汇总结果", "", "Excel文件 (*.xlsx)"
        )
        
        if file_path:
            try:
                with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                    if self.data is not None:
                        self.data.to_excel(writer, sheet_name='原始数据', index=False)
                    self.summary_data.to_excel(writer, sheet_name='汇总表', index=True)
                    
                QMessageBox.information(self, "成功", f"结果已保存到: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存失败: {str(e)}")
                
    def save_state(self) -> dict:
        """保存插件状态"""
        state = {
            'current_tab': self.tab_widget.currentIndex(),
            'file_path': self.file_path_edit.text(),
            'auto_confirm': self.auto_confirm_check.isChecked()
        }
        return state
        
    def restore_state(self, state: dict):
        """恢复插件状态"""
        if 'current_tab' in state:
            self.tab_widget.setCurrentIndex(state['current_tab'])
            
        if 'file_path' in state:
            self.file_path_edit.setText(state['file_path'])
            
        if 'auto_confirm' in state:
            self.auto_confirm_check.setChecked(state['auto_confirm'])