"""
插件包初始化文件
用于管理和注册所有功能插件
"""

# 导入所有插件类，以便插件管理器可以发现它们
from .plugin1 import TextProcessor
from .plugin2 import FileManager
from .plugin3 import SystemTools
from .monthly_summary import MonthlySummary
from .excel_merger import ExcelMerger
from .excel_deduplication import ExcelDeduplication
from .image_watermark import ImageWatermarkPlugin

# 插件列表
__all__ = [
    'TextProcessor',
    'FileManager', 
    'SystemTools',
    'MonthlySummary',
    'ExcelMerger',
    'ExcelDeduplication',
    'ImageWatermarkPlugin'
]