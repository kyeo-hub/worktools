# -*- coding: utf-8 -*-

"""
文本处理工具插件
提供常用文本处理功能
"""

import re
import base64
import urllib.parse
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
                           QTextEdit, QPushButton, QLabel, QComboBox,
                           QLineEdit, QGroupBox, QCheckBox, QSpinBox,
                           QMessageBox, QGridLayout)
from PyQt5.QtGui import QIcon, QFont, QTextCursor
from PyQt5.QtCore import Qt

from worktools.base_plugin import BasePlugin

class TextProcessor(BasePlugin):
    """
    文本处理工具插件
    
    提供常用文本处理功能，包括格式化、编码转换、正则表达式匹配等
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._name = "文本处理工具"
        self._description = "提供常用文本处理功能，包括格式化、编码转换、正则表达式匹配等"
        
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
        return "文本工具"
        
    def _setup_ui(self):
        """设置用户界面"""
        # 创建主布局
        main_layout = QVBoxLayout(self)
        
        # 创建选项卡
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # 添加各个功能选项卡
        self._setup_format_tab()
        self._setup_encoding_tab()
        self._setup_regex_tab()
        self._setup_generator_tab()
        
    def _setup_format_tab(self):
        """设置文本格式化选项卡"""
        format_widget = QWidget()
        layout = QVBoxLayout(format_widget)
        
        # 输入区域
        input_group = QGroupBox("输入文本")
        input_layout = QVBoxLayout(input_group)
        self.format_input_text = QTextEdit()
        self.format_input_text.setPlaceholderText("在此输入要格式化的文本...")
        input_layout.addWidget(self.format_input_text)
        layout.addWidget(input_group)
        
        # 格式化选项
        options_group = QGroupBox("格式化选项")
        options_layout = QGridLayout(options_group)
        
        self.uppercase_check = QCheckBox("转大写")
        self.lowercase_check = QCheckBox("转小写")
        self.trim_check = QCheckBox("去除首尾空白")
        self.compress_check = QCheckBox("压缩空白")
        
        options_layout.addWidget(self.uppercase_check, 0, 0)
        options_layout.addWidget(self.lowercase_check, 0, 1)
        options_layout.addWidget(self.trim_check, 1, 0)
        options_layout.addWidget(self.compress_check, 1, 1)
        
        layout.addWidget(options_group)
        
        # 操作按钮
        button_layout = QHBoxLayout()
        format_button = QPushButton("格式化")
        format_button.clicked.connect(self._format_text)
        swap_button = QPushButton("交换输入/输出")
        swap_button.clicked.connect(self._swap_format_text)
        clear_button = QPushButton("清空")
        clear_button.clicked.connect(lambda: self.format_input_text.clear())
        
        button_layout.addWidget(format_button)
        button_layout.addWidget(swap_button)
        button_layout.addWidget(clear_button)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        # 输出区域
        output_group = QGroupBox("格式化结果")
        output_layout = QVBoxLayout(output_group)
        self.format_output_text = QTextEdit()
        self.format_output_text.setReadOnly(True)
        output_layout.addWidget(self.format_output_text)
        layout.addWidget(output_group)
        
        self.tab_widget.addTab(format_widget, "文本格式化")
        
    def _setup_encoding_tab(self):
        """设置编码转换选项卡"""
        encoding_widget = QWidget()
        layout = QVBoxLayout(encoding_widget)
        
        # 输入区域
        input_group = QGroupBox("输入文本")
        input_layout = QVBoxLayout(input_group)
        self.encoding_input_text = QTextEdit()
        self.encoding_input_text.setPlaceholderText("在此输入要转换的文本...")
        input_layout.addWidget(self.encoding_input_text)
        layout.addWidget(input_group)
        
        # 编码选择
        encoding_layout = QHBoxLayout()
        
        encoding_layout.addWidget(QLabel("从"))
        self.source_encoding = QComboBox()
        self.source_encoding.addItems(["UTF-8", "GBK", "ISO-8859-1", "ASCII"])
        self.source_encoding.setCurrentText("UTF-8")
        encoding_layout.addWidget(self.source_encoding)
        
        encoding_layout.addWidget(QLabel("到"))
        self.target_encoding = QComboBox()
        self.target_encoding.addItems(["UTF-8", "GBK", "ISO-8859-1", "ASCII"])
        encoding_layout.addWidget(self.target_encoding)
        
        layout.addLayout(encoding_layout)
        
        # 特殊编码
        special_layout = QHBoxLayout()
        
        base64_decode_btn = QPushButton("Base64解码")
        base64_decode_btn.clicked.connect(self._decode_base64)
        special_layout.addWidget(base64_decode_btn)
        
        base64_encode_btn = QPushButton("Base64编码")
        base64_encode_btn.clicked.connect(self._encode_base64)
        special_layout.addWidget(base64_encode_btn)
        
        url_decode_btn = QPushButton("URL解码")
        url_decode_btn.clicked.connect(self._decode_url)
        special_layout.addWidget(url_decode_btn)
        
        url_encode_btn = QPushButton("URL编码")
        url_encode_btn.clicked.connect(self._encode_url)
        special_layout.addWidget(url_encode_btn)
        
        layout.addLayout(special_layout)
        
        # 转换按钮
        button_layout = QHBoxLayout()
        convert_button = QPushButton("编码转换")
        convert_button.clicked.connect(self._convert_encoding)
        swap_button = QPushButton("交换输入/输出")
        swap_button.clicked.connect(self._swap_encoding_text)
        clear_button = QPushButton("清空")
        clear_button.clicked.connect(lambda: self.encoding_input_text.clear())
        
        button_layout.addWidget(convert_button)
        button_layout.addWidget(swap_button)
        button_layout.addWidget(clear_button)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        # 输出区域
        output_group = QGroupBox("转换结果")
        output_layout = QVBoxLayout(output_group)
        self.encoding_output_text = QTextEdit()
        self.encoding_output_text.setReadOnly(True)
        output_layout.addWidget(self.encoding_output_text)
        layout.addWidget(output_group)
        
        self.tab_widget.addTab(encoding_widget, "编码转换")
        
    def _setup_regex_tab(self):
        """设置正则表达式选项卡"""
        regex_widget = QWidget()
        layout = QVBoxLayout(regex_widget)
        
        # 正则表达式输入
        regex_group = QGroupBox("正则表达式")
        regex_layout = QVBoxLayout(regex_group)
        
        regex_input_layout = QHBoxLayout()
        regex_input_layout.addWidget(QLabel("表达式:"))
        self.regex_input = QLineEdit()
        self.regex_input.setPlaceholderText("输入正则表达式，如: \\d+")
        regex_input_layout.addWidget(self.regex_input)
        
        self.case_sensitive_check = QCheckBox("区分大小写")
        self.case_sensitive_check.setChecked(False)
        regex_input_layout.addWidget(self.case_sensitive_check)
        
        self.multiline_check = QCheckBox("多行模式")
        regex_input_layout.addWidget(self.multiline_check)
        
        regex_layout.addLayout(regex_input_layout)
        
        # 测试文本
        regex_layout.addWidget(QLabel("测试文本:"))
        self.regex_test_text = QTextEdit()
        self.regex_test_text.setPlaceholderText("在此输入要测试的文本...")
        regex_layout.addWidget(self.regex_test_text)
        
        # 匹配按钮
        match_button = QPushButton("执行匹配")
        match_button.clicked.connect(self._execute_regex)
        regex_layout.addWidget(match_button)
        
        layout.addWidget(regex_group)
        
        # 匹配结果
        result_group = QGroupBox("匹配结果")
        result_layout = QVBoxLayout(result_group)
        
        self.regex_result_text = QTextEdit()
        self.regex_result_text.setReadOnly(True)
        result_layout.addWidget(self.regex_result_text)
        
        layout.addWidget(result_group)
        
        self.tab_widget.addTab(regex_widget, "正则表达式")
        
    def _setup_generator_tab(self):
        """设置文本生成器选项卡"""
        generator_widget = QWidget()
        layout = QVBoxLayout(generator_widget)
        
        # 生成类型
        type_group = QGroupBox("生成类型")
        type_layout = QVBoxLayout(type_group)
        
        # 随机字符串
        random_layout = QHBoxLayout()
        random_layout.addWidget(QLabel("随机字符串长度:"))
        self.random_length = QSpinBox()
        self.random_length.setRange(1, 1000)
        self.random_length.setValue(10)
        random_layout.addWidget(self.random_length)
        
        generate_random_btn = QPushButton("生成随机字符串")
        generate_random_btn.clicked.connect(self._generate_random_string)
        random_layout.addWidget(generate_random_btn)
        
        type_layout.addLayout(random_layout)
        
        # UUID
        uuid_layout = QHBoxLayout()
        generate_uuid_btn = QPushButton("生成UUID")
        generate_uuid_btn.clicked.connect(self._generate_uuid)
        uuid_layout.addWidget(generate_uuid_btn)
        
        generate_uuid_short_btn = QPushButton("生成短UUID")
        generate_uuid_short_btn.clicked.connect(self._generate_short_uuid)
        uuid_layout.addWidget(generate_uuid_short_btn)
        
        type_layout.addLayout(uuid_layout)
        
        # 时间戳
        timestamp_layout = QHBoxLayout()
        generate_timestamp_btn = QPushButton("生成时间戳")
        generate_timestamp_btn.clicked.connect(self._generate_timestamp)
        timestamp_layout.addWidget(generate_timestamp_btn)
        
        generate_datetime_btn = QPushButton("生成日期时间")
        generate_datetime_btn.clicked.connect(self._generate_datetime)
        timestamp_layout.addWidget(generate_datetime_btn)
        
        type_layout.addLayout(timestamp_layout)
        
        layout.addWidget(type_group)
        
        # 结果
        result_group = QGroupBox("生成结果")
        result_layout = QVBoxLayout(result_group)
        
        self.generator_result_text = QTextEdit()
        self.generator_result_text.setReadOnly(True)
        result_layout.addWidget(self.generator_result_text)
        
        layout.addWidget(result_group)
        
        self.tab_widget.addTab(generator_widget, "文本生成器")
        
    def _format_text(self):
        """执行文本格式化"""
        text = self.format_input_text.toPlainText()
        
        if self.uppercase_check.isChecked():
            text = text.upper()
            
        if self.lowercase_check.isChecked():
            text = text.lower()
            
        if self.trim_check.isChecked():
            text = text.strip()
            
        if self.compress_check.isChecked():
            text = re.sub(r'\s+', ' ', text)
            
        self.format_output_text.setPlainText(text)
        
    def _swap_format_text(self):
        """交换格式化的输入和输出"""
        input_text = self.format_input_text.toPlainText()
        output_text = self.format_output_text.toPlainText()
        
        self.format_input_text.setPlainText(output_text)
        self.format_output_text.setPlainText(input_text)
        
    def _convert_encoding(self):
        """执行编码转换"""
        text = self.encoding_input_text.toPlainText()
        if not text:
            return
            
        source_encoding = self.source_encoding.currentText()
        target_encoding = self.target_encoding.currentText()
        
        try:
            # 先解码，再编码
            decoded_text = text.encode(source_encoding, errors='replace').decode(source_encoding)
            encoded_text = decoded_text.encode(target_encoding, errors='replace').decode(target_encoding)
            self.encoding_output_text.setPlainText(encoded_text)
        except Exception as e:
            self.encoding_output_text.setPlainText(f"编码转换失败: {str(e)}")
            
    def _encode_base64(self):
        """Base64编码"""
        text = self.encoding_input_text.toPlainText()
        if not text:
            return
            
        try:
            encoded_bytes = base64.b64encode(text.encode('utf-8'))
            self.encoding_output_text.setPlainText(encoded_bytes.decode('utf-8'))
        except Exception as e:
            self.encoding_output_text.setPlainText(f"Base64编码失败: {str(e)}")
            
    def _decode_base64(self):
        """Base64解码"""
        text = self.encoding_input_text.toPlainText()
        if not text:
            return
            
        try:
            decoded_bytes = base64.b64decode(text.encode('utf-8'))
            self.encoding_output_text.setPlainText(decoded_bytes.decode('utf-8'))
        except Exception as e:
            self.encoding_output_text.setPlainText(f"Base64解码失败: {str(e)}")
            
    def _encode_url(self):
        """URL编码"""
        text = self.encoding_input_text.toPlainText()
        if not text:
            return
            
        try:
            encoded_text = urllib.parse.quote(text)
            self.encoding_output_text.setPlainText(encoded_text)
        except Exception as e:
            self.encoding_output_text.setPlainText(f"URL编码失败: {str(e)}")
            
    def _decode_url(self):
        """URL解码"""
        text = self.encoding_input_text.toPlainText()
        if not text:
            return
            
        try:
            decoded_text = urllib.parse.unquote(text)
            self.encoding_output_text.setPlainText(decoded_text)
        except Exception as e:
            self.encoding_output_text.setPlainText(f"URL解码失败: {str(e)}")
            
    def _swap_encoding_text(self):
        """交换编码转换的输入和输出"""
        input_text = self.encoding_input_text.toPlainText()
        output_text = self.encoding_output_text.toPlainText()
        
        self.encoding_input_text.setPlainText(output_text)
        self.encoding_output_text.setPlainText(input_text)
        
    def _execute_regex(self):
        """执行正则表达式匹配"""
        pattern = self.regex_input.text()
        text = self.regex_test_text.toPlainText()
        
        if not pattern:
            self.regex_result_text.setPlainText("请输入正则表达式")
            return
            
        if not text:
            self.regex_result_text.setPlainText("请输入测试文本")
            return
            
        try:
            flags = 0
            if not self.case_sensitive_check.isChecked():
                flags |= re.IGNORECASE
                
            if self.multiline_check.isChecked():
                flags |= re.MULTILINE
                
            matches = re.findall(pattern, text, flags)
            
            if matches:
                result = f"匹配到 {len(matches)} 个结果:\n\n"
                for i, match in enumerate(matches, 1):
                    result += f"{i}. {str(match)}\n"
                    
                self.regex_result_text.setPlainText(result)
            else:
                self.regex_result_text.setPlainText("没有匹配到结果")
                
        except Exception as e:
            self.regex_result_text.setPlainText(f"正则表达式错误: {str(e)}")
            
    def _generate_random_string(self):
        """生成随机字符串"""
        import random
        import string
        
        length = self.random_length.value()
        chars = string.ascii_letters + string.digits
        random_str = ''.join(random.choice(chars) for _ in range(length))
        
        current_text = self.generator_result_text.toPlainText()
        new_text = f"{current_text}\n随机字符串({length}位): {random_str}" if current_text else f"随机字符串({length}位): {random_str}"
        self.generator_result_text.setPlainText(new_text)
        
    def _generate_uuid(self):
        """生成UUID"""
        import uuid
        
        generated_uuid = str(uuid.uuid4())
        
        current_text = self.generator_result_text.toPlainText()
        new_text = f"{current_text}\nUUID: {generated_uuid}" if current_text else f"UUID: {generated_uuid}"
        self.generator_result_text.setPlainText(new_text)
        
    def _generate_short_uuid(self):
        """生成短UUID"""
        import uuid
        
        generated_uuid = str(uuid.uuid4()).replace('-', '')
        
        current_text = self.generator_result_text.toPlainText()
        new_text = f"{current_text}\n短UUID: {generated_uuid}" if current_text else f"短UUID: {generated_uuid}"
        self.generator_result_text.setPlainText(new_text)
        
    def _generate_timestamp(self):
        """生成时间戳"""
        import time
        
        timestamp = str(int(time.time()))
        
        current_text = self.generator_result_text.toPlainText()
        new_text = f"{current_text}\n时间戳: {timestamp}" if current_text else f"时间戳: {timestamp}"
        self.generator_result_text.setPlainText(new_text)
        
    def _generate_datetime(self):
        """生成日期时间"""
        import datetime
        
        now = datetime.datetime.now()
        datetime_str = now.strftime("%Y-%m-%d %H:%M:%S")
        
        current_text = self.generator_result_text.toPlainText()
        new_text = f"{current_text}\n日期时间: {datetime_str}" if current_text else f"日期时间: {datetime_str}"
        self.generator_result_text.setPlainText(new_text)