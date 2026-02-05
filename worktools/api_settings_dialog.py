# -*- coding: utf-8 -*-

"""
API设置对话框
用于配置百度/高德地图API Key
"""

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QGroupBox, QMessageBox,
                             QTabWidget, QWidget)
from PyQt5.QtCore import Qt, QSettings


class APISettingsDialog(QDialog):
    """API设置对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("API设置")
        self.setMinimumSize(500, 350)
        self.settings = QSettings("WorkTools", "PyQtWorkTools")
        
        self._setup_ui()
        self._load_settings()
        
    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        
        # 说明标签
        tip_label = QLabel("配置地图API Key以获得更精准的IP定位服务")
        tip_label.setStyleSheet("color: gray; padding: 10px;")
        tip_label.setWordWrap(True)
        layout.addWidget(tip_label)
        
        # 使用TabWidget组织不同的API设置
        tab_widget = QTabWidget()
        
        # ===== 百度地图API =====
        baidu_tab = QWidget()
        baidu_layout = QVBoxLayout(baidu_tab)
        
        baidu_info = QLabel(
            "百度地图IP定位API\n"
            "免费额度：10万次/天\n"
            "精度：区县级\n\n"
            "申请步骤：\n"
            "1. 访问 https://lbsyun.baidu.com/\n"
            "2. 注册账号并登录\n"
            "3. 控制台 → 创建应用 → 选择IP定位服务\n"
            "4. 复制AK填入下方"
        )
        baidu_info.setStyleSheet("color: #666; line-height: 1.6;")
        baidu_info.setWordWrap(True)
        baidu_layout.addWidget(baidu_info)
        
        baidu_key_layout = QHBoxLayout()
        baidu_key_layout.addWidget(QLabel("百度AK:"))
        self.baidu_key_input = QLineEdit()
        self.baidu_key_input.setPlaceholderText("请输入百度地图API Key")
        baidu_key_layout.addWidget(self.baidu_key_input)
        baidu_layout.addLayout(baidu_key_layout)
        
        baidu_layout.addStretch()
        tab_widget.addTab(baidu_tab, "百度地图")
        
        # ===== 高德地图API =====
        gaode_tab = QWidget()
        gaode_layout = QVBoxLayout(gaode_tab)
        
        gaode_info = QLabel(
            "高德地图IP定位API\n"
            "免费额度：5000次/天\n"
            "精度：区县级\n\n"
            "申请步骤：\n"
            "1. 访问 https://lbs.amap.com/\n"
            "2. 注册账号并登录\n"
            "3. 控制台 → 创建Key → Web服务 → IP定位\n"
            "4. 复制Key填入下方"
        )
        gaode_info.setStyleSheet("color: #666; line-height: 1.6;")
        gaode_info.setWordWrap(True)
        gaode_layout.addWidget(gaode_info)
        
        gaode_key_layout = QHBoxLayout()
        gaode_key_layout.addWidget(QLabel("高德Key:"))
        self.gaode_key_input = QLineEdit()
        self.gaode_key_input.setPlaceholderText("请输入高德地图API Key")
        gaode_key_layout.addWidget(self.gaode_key_input)
        gaode_layout.addLayout(gaode_key_layout)
        
        gaode_layout.addStretch()
        tab_widget.addTab(gaode_tab, "高德地图")
        
        layout.addWidget(tab_widget)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.save_btn = QPushButton("保存")
        self.save_btn.clicked.connect(self._save_settings)
        button_layout.addWidget(self.save_btn)
        
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
        
    def _load_settings(self):
        """加载已保存的设置"""
        baidu_key = self.settings.value("api/baidu_key", "")
        gaode_key = self.settings.value("api/gaode_key", "")
        
        self.baidu_key_input.setText(baidu_key)
        self.gaode_key_input.setText(gaode_key)
        
    def _save_settings(self):
        """保存设置"""
        baidu_key = self.baidu_key_input.text().strip()
        gaode_key = self.gaode_key_input.text().strip()
        
        self.settings.setValue("api/baidu_key", baidu_key)
        self.settings.setValue("api/gaode_key", gaode_key)
        
        QMessageBox.information(self, "保存成功", "API设置已保存")
        self.accept()
        
    @staticmethod
    def get_api_keys():
        """静态方法获取API Keys"""
        settings = QSettings("WorkTools", "PyQtWorkTools")
        return {
            'baidu': settings.value("api/baidu_key", ""),
            'gaode': settings.value("api/gaode_key", "")
        }
