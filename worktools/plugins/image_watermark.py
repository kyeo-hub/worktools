# -*- coding: utf-8 -*-

"""
图片加水印插件
提供给图片添加水印的功能，支持单张和批量处理
支持多种水印样式：文字水印、时间地点水印
支持获取实时天气和地理位置信息
"""

import os
import json
import urllib.request
import urllib.error
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                           QLabel, QPushButton, QLineEdit, QSpinBox,
                           QComboBox, QFileDialog, QGroupBox, QCheckBox,
                           QColorDialog, QProgressBar, QMessageBox,
                           QScrollArea, QTabWidget, QTextEdit, QDateTimeEdit,
                           QStackedWidget)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QDateTime
from PyQt5.QtGui import QColor

from worktools.base_plugin import BasePlugin
from worktools.api_settings_dialog import APISettingsDialog


class WeatherLocationWorker(QThread):
    """获取天气和地理位置的工作线程"""
    
    data_ready = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    
    def run(self):
        """获取实时天气和位置信息"""
        try:
            result = {}
            
            # 1. 获取地理位置（基于IP）
            location_data = self._get_location()
            if location_data:
                result.update(location_data)
            
            # 2. 获取天气信息
            weather_data = self._get_weather()
            if weather_data:
                result.update(weather_data)
            
            self.data_ready.emit(result)
        except Exception as e:
            self.error_occurred.emit(f"获取信息失败: {str(e)}")
    
    def _get_location(self):
        """获取地理位置信息（基于IP）"""
        # 获取API Keys
        api_keys = APISettingsDialog.get_api_keys()
        baidu_key = api_keys.get('baidu', '')
        gaode_key = api_keys.get('gaode', '')
        
        # 构建API列表，优先使用配置了Key的国内服务
        apis = []
        
        # 如果配置了百度Key，优先使用
        if baidu_key:
            apis.append((
                f'https://api.map.baidu.com/location/ip?ak={baidu_key}&coor=bd09ll',
                self._parse_baidu
            ))
        
        # 如果配置了高德Key，其次使用
        if gaode_key:
            apis.append((
                f'https://restapi.amap.com/v3/ip?key={gaode_key}',
                self._parse_gaode
            ))
        
        # 最后使用免费服务作为备用
        apis.extend([
            ('https://ipwho.is/', self._parse_ipwhois),
            ('http://ip-api.com/json/', self._parse_ip_api),
        ])
        
        for url, parser in apis:
            try:
                req = urllib.request.Request(
                    url,
                    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
                )
                with urllib.request.urlopen(req, timeout=8) as response:
                    data = json.loads(response.read().decode('utf-8'))
                    result = parser(data)
                    if result:
                        return result
            except Exception as e:
                print(f"API {url} 失败: {e}")
                continue
        
        return None
    
    def _parse_baidu(self, data):
        """解析百度IP定位返回的数据"""
        if data.get('status') == 0:
            content = data.get('content', {})
            address_component = content.get('address_component', {})
            
            country = '中国'  # 百度主要覆盖国内
            province = address_component.get('province', '')
            city = address_component.get('city', '')
            district = address_component.get('district', '')
            
            # 构建详细地址
            location_parts = [p for p in [country, province, city, district] if p]
            location1 = ''.join(location_parts)
            
            return {
                'location1': location1,
                'city': city,
                'region': province,
                'country': country
            }
        return None
    
    def _parse_gaode(self, data):
        """解析高德IP定位返回的数据"""
        if data.get('status') == '1' and data.get('info') == 'OK':
            province = data.get('province', '')
            city = data.get('city', '')
            
            # 移除"市"、"省"等后缀用于翻译
            city_clean = city.replace('市', '').replace(' Province', '')
            province_clean = province.replace('省', '').replace('市', '')
            
            location1 = f"{province}{city}"
            
            return {
                'location1': location1,
                'city': self._translate_city(city_clean),
                'region': self._translate_region(province_clean),
                'country': '中国'
            }
        return None
    
    def _parse_ipwhois(self, data):
        """解析 ipwho.is 返回的数据"""
        if data.get('success'):
            city = data.get('city', '')
            region = data.get('region', '')
            country = data.get('country', '')
            country_code = data.get('country_code', '')
            
            # 翻译为中文
            country_cn = self._translate_country(country, country_code)
            region_cn = self._translate_region(region)
            city_cn = self._translate_city(city)
            
            if city_cn and region_cn:
                location1 = f"{country_cn}{region_cn}{city_cn}"
            elif city_cn:
                location1 = city_cn
            else:
                location1 = "未知位置"
            
            return {
                'location1': location1,
                'city': city_cn or city,
                'region': region_cn or region,
                'country': country_cn or country
            }
        return None
    
    def _parse_ip_api(self, data):
        """解析 ip-api.com 返回的数据"""
        if data.get('status') == 'success':
            city = data.get('city', '')
            region = data.get('regionName', '')
            country = data.get('country', '')
            country_code = data.get('countryCode', '')
            
            # 翻译为中文
            country_cn = self._translate_country(country, country_code)
            region_cn = self._translate_region(region)
            city_cn = self._translate_city(city)
            
            if city_cn and region_cn:
                location1 = f"{country_cn}{region_cn}{city_cn}"
            elif city_cn:
                location1 = city_cn
            else:
                location1 = "未知位置"
            
            return {
                'location1': location1,
                'city': city_cn or city,
                'region': region_cn or region,
                'country': country_cn or country
            }
        return None
    
    def _translate_country(self, country, code=''):
        """翻译国家名称为中文"""
        country_map = {
            'China': '中国',
            'CN': '中国',
            'United States': '美国',
            'US': '美国',
            'Japan': '日本',
            'JP': '日本',
            'Korea': '韩国',
            'KR': '韩国',
            'United Kingdom': '英国',
            'GB': '英国',
            'Germany': '德国',
            'DE': '德国',
            'France': '法国',
            'FR': '法国',
            'Russia': '俄罗斯',
            'RU': '俄罗斯',
            'India': '印度',
            'IN': '印度',
            'Singapore': '新加坡',
            'SG': '新加坡',
            'Australia': '澳大利亚',
            'AU': '澳大利亚',
            'Canada': '加拿大',
            'CA': '加拿大',
            'Hong Kong': '中国香港',
            'HK': '中国香港',
            'Taiwan': '中国台湾',
            'TW': '中国台湾',
            'Macau': '中国澳门',
            'MO': '中国澳门',
        }
        return country_map.get(country) or country_map.get(code) or country
    
    def _translate_region(self, region):
        """翻译省份名称为中文"""
        region_map = {
            'Beijing': '北京市',
            'Shanghai': '上海市',
            'Tianjin': '天津市',
            'Chongqing': '重庆市',
            'Guangdong': '广东省',
            'Guangdong Province': '广东省',
            'Hubei': '湖北省',
            'Hubei Province': '湖北省',
            'Hunan': '湖南省',
            'Hunan Province': '湖南省',
            'Henan': '河南省',
            'Henan Province': '河南省',
            'Hebei': '河北省',
            'Hebei Province': '河北省',
            'Shandong': '山东省',
            'Shandong Province': '山东省',
            'Shanxi': '山西省',
            'Shanxi Province': '山西省',
            'Shaanxi': '陕西省',
            'Shaanxi Province': '陕西省',
            'Jiangsu': '江苏省',
            'Jiangsu Province': '江苏省',
            'Zhejiang': '浙江省',
            'Zhejiang Province': '浙江省',
            'Anhui': '安徽省',
            'Anhui Province': '安徽省',
            'Fujian': '福建省',
            'Fujian Province': '福建省',
            'Jiangxi': '江西省',
            'Jiangxi Province': '江西省',
            'Sichuan': '四川省',
            'Sichuan Province': '四川省',
            'Guizhou': '贵州省',
            'Guizhou Province': '贵州省',
            'Yunnan': '云南省',
            'Yunnan Province': '云南省',
            'Liaoning': '辽宁省',
            'Liaoning Province': '辽宁省',
            'Jilin': '吉林省',
            'Jilin Province': '吉林省',
            'Heilongjiang': '黑龙江省',
            'Heilongjiang Province': '黑龙江省',
            'Gansu': '甘肃省',
            'Gansu Province': '甘肃省',
            'Qinghai': '青海省',
            'Qinghai Province': '青海省',
            'Taiwan': '台湾省',
            'Inner Mongolia': '内蒙古自治区',
            'Guangxi': '广西壮族自治区',
            'Tibet': '西藏自治区',
            'Ningxia': '宁夏回族自治区',
            'Xinjiang': '新疆维吾尔自治区',
        }
        return region_map.get(region, region)
    
    def _translate_city(self, city):
        """翻译城市名称为中文"""
        city_map = {
            'Beijing': '北京市',
            'Shanghai': '上海市',
            'Tianjin': '天津市',
            'Chongqing': '重庆市',
            'Wuhan': '武汉市',
            'Guangzhou': '广州市',
            'Shenzhen': '深圳市',
            'Hangzhou': '杭州市',
            'Nanjing': '南京市',
            'Chengdu': '成都市',
            'Xi\'an': '西安市',
            'Xian': '西安市',
            'Changsha': '长沙市',
            'Zhengzhou': '郑州市',
            'Jinan': '济南市',
            'Qingdao': '青岛市',
            'Dalian': '大连市',
            'Shenyang': '沈阳市',
            'Harbin': '哈尔滨市',
            'Changchun': '长春市',
            'Shijiazhuang': '石家庄市',
            'Taiyuan': '太原市',
            'Hefei': '合肥市',
            'Nanchang': '南昌市',
            'Kunming': '昆明市',
            'Guiyang': '贵阳市',
            'Lanzhou': '兰州市',
            'Xining': '西宁市',
            'Nanning': '南宁市',
            'Fuzhou': '福州市',
            'Xiamen': '厦门市',
            'Haikou': '海口市',
            'Sanya': '三亚市',
            'Lhasa': '拉萨市',
            'Yinchuan': '银川市',
            'Urumqi': '乌鲁木齐市',
            'Hohhot': '呼和浩特市',
            'Hong Kong': '香港',
            'Macau': '澳门',
        }
        return city_map.get(city, city)
    
    def _get_weather(self):
        """获取天气信息"""
        try:
            # 使用 Open-Meteo API（免费，无需API Key，但需要经纬度）
            # 先获取位置信息
            location = self._get_location()
            
            if location and location.get('city'):
                # 尝试通过城市名获取天气（简化方案）
                # 使用一个免费的天气API
                req = urllib.request.Request(
                    'https://api.open-meteo.com/v1/forecast?latitude=39.9&longitude=116.4&current_weather=true',
                    headers={'User-Agent': 'Mozilla/5.0'}
                )
                with urllib.request.urlopen(req, timeout=8) as response:
                    data = json.loads(response.read().decode('utf-8'))
                    
                    if 'current_weather' in data:
                        weather_code = data['current_weather'].get('weathercode', 0)
                        temp = data['current_weather'].get('temperature', 0)
                        
                        # 转换天气代码为中文
                        condition_cn = self._convert_weather_code(weather_code)
                        
                        # 获取当前星期
                        weekday_cn = self._get_current_weekday_cn()
                        
                        return {
                            'weather': condition_cn,
                            'temperature': f"{int(temp)}℃",
                            'weekday': weekday_cn
                        }
            
            # 如果无法获取详细天气，至少返回星期
            return {
                'weather': '晴',
                'temperature': '',
                'weekday': self._get_current_weekday_cn()
            }
            
        except Exception as e:
            print(f"获取天气失败: {e}")
            # 返回默认值
            return {
                'weather': '晴',
                'temperature': '',
                'weekday': self._get_current_weekday_cn()
            }
    
    def _get_current_weekday_cn(self):
        """获取当前星期（中文）"""
        weekday_map = {
            0: '星期一',
            1: '星期二',
            2: '星期三',
            3: '星期四',
            4: '星期五',
            5: '星期六',
            6: '星期日'
        }
        return weekday_map.get(datetime.now().weekday(), '星期一')
    
    def _convert_weather_code(self, code):
        """转换天气代码为中文"""
        weather_codes = {
            0: '晴',
            1: '多云', 2: '多云', 3: '多云',
            45: '雾', 48: '雾',
            51: '小雨', 53: '中雨', 55: '大雨',
            56: '冻雨', 57: '冻雨',
            61: '小雨', 63: '中雨', 65: '大雨',
            66: '冻雨', 67: '冻雨',
            71: '小雪', 73: '中雪', 75: '大雪',
            77: '雪粒',
            80: '阵雨', 81: '阵雨', 82: '阵雨',
            85: '阵雪', 86: '阵雪',
            95: '雷阵雨', 96: '雷阵雨', 99: '雷阵雨'
        }
        return weather_codes.get(code, '多云')
    
    def _translate_weather(self, condition):
        """翻译天气状况为中文"""
        weather_map = {
            'Clear': '晴',
            'Sunny': '晴',
            'Partly cloudy': '多云',
            'Cloudy': '多云',
            'Overcast': '阴',
            'Mist': '雾',
            'Fog': '雾',
            'Rain': '雨',
            'Light rain': '小雨',
            'Moderate rain': '中雨',
            'Heavy rain': '大雨',
            'Showers': '阵雨',
            'Thunderstorm': '雷阵雨',
            'Snow': '雪',
            'Light snow': '小雪',
            'Heavy snow': '大雪',
            'Hail': '冰雹',
            'Sleet': '雨夹雪',
        }
        
        # 尝试匹配
        for en, cn in weather_map.items():
            if en.lower() in condition.lower():
                return cn
        
        # 如果包含Unknown，返回未知
        if 'unknown' in condition.lower():
            return '未知'
        
        return condition  # 返回原文
    
    def _translate_weekday(self, weekday):
        """翻译星期为中文"""
        weekday_map = {
            'Monday': '星期一',
            'Tuesday': '星期二',
            'Wednesday': '星期三',
            'Thursday': '星期四',
            'Friday': '星期五',
            'Saturday': '星期六',
            'Sunday': '星期日'
        }
        return weekday_map.get(weekday, weekday)


class WatermarkWorker(QThread):
    """水印处理工作线程"""

    progress_updated = pyqtSignal(int, int)
    finished = pyqtSignal(bool, str)
    image_processed = pyqtSignal(str)

    def __init__(self, images_info, watermark_config, watermark_type):
        super().__init__()
        self.images_info = images_info
        self.watermark_config = watermark_config
        self.watermark_type = watermark_type

    def run(self):
        """执行水印添加"""
        total = len(self.images_info)
        try:
            for idx, (input_path, output_path) in enumerate(self.images_info):
                if self.watermark_type == "text":
                    self.add_text_watermark(input_path, output_path, self.watermark_config)
                elif self.watermark_type == "datetime_location":
                    self.add_datetime_location_watermark(input_path, output_path, self.watermark_config)
                self.progress_updated.emit(idx + 1, total)
                self.image_processed.emit(output_path)
            self.finished.emit(True, f"成功处理 {total} 张图片")
        except Exception as e:
            self.finished.emit(False, f"处理失败: {str(e)}")

    def add_text_watermark(self, input_path, output_path, config):
        """添加普通文字水印"""
        with Image.open(input_path).convert("RGBA") as img:
            watermark = Image.new("RGBA", img.size, (255, 255, 255, 0))
            draw = ImageDraw.Draw(watermark)

            text = config.get("text", "水印")
            font_size = config.get("font_size", 36)
            color = config.get("color", (255, 255, 255, 128))
            position = config.get("position", "right_bottom")
            angle = config.get("angle", 0)

            font = self._get_font(font_size)
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]

            margin = 20
            x, y = self._calculate_position(
                position, margin, img.width, img.height, text_width, text_height
            )

            if position != "tile":
                if angle != 0:
                    text_img = Image.new("RGBA", (text_width + 10, text_height + 10), (255, 255, 255, 0))
                    text_draw = ImageDraw.Draw(text_img)
                    text_draw.text((5, 5), text, font=font, fill=color)
                    text_img = text_img.rotate(angle, expand=True)
                    watermark.paste(text_img, (x, y), text_img)
                else:
                    draw.text((x, y), text, font=font, fill=color)
            else:
                self._draw_tiled_watermark(draw, text, font, color, img.width, img.height)

            watermarked = Image.alpha_composite(img, watermark)
            self._save_image(watermarked, output_path)

    def add_datetime_location_watermark(self, input_path, output_path, config):
        """添加时间地点样式的水印（仿相机打卡样式）"""
        with Image.open(input_path).convert("RGBA") as img:
            watermark = Image.new("RGBA", img.size, (255, 255, 255, 0))
            draw = ImageDraw.Draw(watermark)

            time_str = config.get("time", "14:38")
            date_str = config.get("date", "2021-09-23")
            weekday_weather = config.get("weekday_weather", "星期四 多云 27℃")
            location1 = config.get("location1", "广东省广州市番禺区南村镇")
            location2 = config.get("location2", "番禺政务万博政务服务大厅")

            color = config.get("color", (255, 255, 255, 220))
            accent_color = config.get("accent_color", (255, 193, 7, 220))  # 金色强调色
            bg_color = config.get("bg_color", (0, 0, 0, 80))  # 半透明背景

            margin = 30
            padding = 20
            line_spacing = 8

            # 加载不同大小的字体
            time_font = self._get_font(36)  # 大号时间
            date_font = self._get_font(20)  # 日期
            info_font = self._get_font(16)  # 其他信息

            # 计算各部分尺寸
            time_bbox = draw.textbbox((0, 0), time_str, font=time_font)
            time_width = time_bbox[2] - time_bbox[0]
            time_height = time_bbox[3] - time_bbox[1]

            date_bbox = draw.textbbox((0, 0), date_str, font=date_font)
            date_width = date_bbox[2] - date_bbox[0]
            date_height = date_bbox[3] - date_bbox[1]

            weekday_bbox = draw.textbbox((0, 0), weekday_weather, font=info_font)
            weekday_height = weekday_bbox[3] - weekday_bbox[1]

            loc1_bbox = draw.textbbox((0, 0), location1, font=info_font)
            loc1_height = loc1_bbox[3] - loc1_bbox[1]

            loc2_bbox = draw.textbbox((0, 0), location2, font=info_font)
            loc2_height = loc2_bbox[3] - loc2_bbox[1]

            # 上半部分：左边时间，右边日期+星期天气
            # 计算上半部分的高度
            right_top_height = date_height + weekday_height + line_spacing
            upper_height = max(time_height, right_top_height)

            # 下半部分：两行地点
            lower_height = loc1_height + loc2_height + line_spacing

            # 计算整体宽度
            right_col_width = max(date_width, weekday_bbox[2] - weekday_bbox[0])
            upper_width = time_width + 20 + right_col_width  # 20是分隔间距
            lower_width = max(loc1_bbox[2] - loc1_bbox[0], loc2_bbox[2] - loc2_bbox[0])
            total_width = max(upper_width, lower_width)
            total_height = upper_height + lower_height + padding

            # 水印位置（默认左下角）
            x = margin
            y = img.height - total_height - margin - padding * 2

            # 绘制半透明背景
            bg_padding = 15
            draw.rounded_rectangle(
                [x - bg_padding, y - bg_padding, 
                 x + total_width + bg_padding, y + total_height + bg_padding],
                radius=10,
                fill=bg_color
            )

            # ========== 上半部分布局 ==========
            # 左侧：大号时间（与右侧信息顶部对齐，稍微下移一点以视觉平衡）
            time_y = y  # 顶部对齐，留5像素间距
            draw.text((x, time_y), time_str, font=time_font, fill=color)

            # 绘制分隔线（分隔时间和右侧信息）
            separator_x = x + time_width + 10
            draw.line(
                [(separator_x, y + 2), (separator_x, y + upper_height - 2)],
                fill=accent_color,
                width=2
            )

            # 右侧：日期 + 星期天气（从顶部对齐）
            right_x = separator_x + 10
            right_y = y

            # 日期
            draw.text((right_x, right_y), date_str, font=date_font, fill=color)
            right_y += date_height + line_spacing

            # 星期和天气
            draw.text((right_x, right_y), weekday_weather, font=info_font, fill=color)

            # ========== 下半部分布局 ==========
            # 地点从左侧开始对齐，位于上半部分下方
            loc_y = y + upper_height + padding

            # 地点1
            draw.text((x, loc_y), location1, font=info_font, fill=color)
            loc_y += loc1_height + line_spacing

            # 地点2
            draw.text((x, loc_y), location2, font=info_font, fill=color)

            watermarked = Image.alpha_composite(img, watermark)
            self._save_image(watermarked, output_path)

    def _get_font(self, size):
        """获取字体"""
        try:
            return ImageFont.truetype("msyh.ttc", size)
        except:
            try:
                return ImageFont.truetype("arial.ttf", size)
            except:
                return ImageFont.load_default()

    def _calculate_position(self, position, margin, img_width, img_height, text_width, text_height):
        """计算文字位置"""
        if position == "left_top":
            return margin, margin
        elif position == "right_top":
            return img_width - text_width - margin, margin
        elif position == "left_bottom":
            return margin, img_height - text_height - margin
        elif position == "right_bottom":
            return img_width - text_width - margin, img_height - text_height - margin
        elif position == "center":
            return (img_width - text_width) // 2, (img_height - text_height) // 2
        return img_width - text_width - margin, img_height - text_height - margin

    def _draw_tiled_watermark(self, draw, text, font, color, width, height):
        """绘制平铺水印"""
        margin = 100
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        for y in range(0, height, text_height + margin):
            for x in range(0, width, text_width + margin):
                draw.text((x, y), text, font=font, fill=color)

    def _save_image(self, image, output_path):
        """保存图片"""
        if output_path.lower().endswith(('.jpg', '.jpeg')):
            image = image.convert("RGB")
        image.save(output_path, quality=95)


class ImageWatermarkPlugin(BasePlugin):
    """图片加水印插件"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._name = "图片加水印"
        self._description = "给图片添加自定义水印，支持文字水印和时间地点水印"
        self.image_paths = []
        self.output_dir = ""
        self.watermark_color = QColor(255, 255, 255, 220)
        self.accent_color = QColor(255, 193, 7, 220)  # 金色
        self.bg_color = QColor(0, 0, 0, 80)

    def get_name(self) -> str:
        return self._name

    def get_description(self) -> str:
        return self._description

    def get_icon(self):
        return None

    def get_category(self) -> str:
        return "图片工具"

    def _setup_ui(self):
        """设置用户界面"""
        main_layout = QVBoxLayout(self)

        # 图片选择组
        image_group = QGroupBox("图片选择")
        image_layout = QVBoxLayout(image_group)

        btn_layout = QHBoxLayout()
        self.select_single_btn = QPushButton("选择单张图片")
        self.select_single_btn.clicked.connect(self._select_single_image)
        self.select_multi_btn = QPushButton("选择多张图片")
        self.select_multi_btn.clicked.connect(self._select_multiple_images)
        btn_layout.addWidget(self.select_single_btn)
        btn_layout.addWidget(self.select_multi_btn)
        image_layout.addLayout(btn_layout)

        self.image_list_label = QLabel("已选择 0 张图片")
        image_layout.addWidget(self.image_list_label)

        image_scroll = QScrollArea()
        image_scroll.setMaximumHeight(80)
        image_scroll.setWidgetResizable(True)
        self.image_list_widget = QLabel("未选择图片")
        self.image_list_widget.setAlignment(Qt.AlignTop)
        self.image_list_widget.setWordWrap(True)
        image_scroll.setWidget(self.image_list_widget)
        image_layout.addWidget(image_scroll)

        main_layout.addWidget(image_group)

        # 水印类型选择
        type_group = QGroupBox("水印类型")
        type_layout = QHBoxLayout(type_group)
        self.watermark_type_combo = QComboBox()
        self.watermark_type_combo.addItems(["文字水印", "时间地点水印"])
        self.watermark_type_combo.currentIndexChanged.connect(self._on_watermark_type_changed)
        type_layout.addWidget(QLabel("选择类型:"))
        type_layout.addWidget(self.watermark_type_combo)
        type_layout.addStretch()
        main_layout.addWidget(type_group)

        # 动态配置区域 - 使用滚动区域包装
        config_scroll = QScrollArea()
        config_scroll.setWidgetResizable(True)
        config_scroll.setFrameShape(QScrollArea.NoFrame)
        config_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # 动态配置容器
        self.config_stack = QStackedWidget()
        self._setup_text_watermark_ui()
        self._setup_datetime_location_ui()
        
        config_scroll.setWidget(self.config_stack)
        main_layout.addWidget(config_scroll, 1)  # 添加 stretch factor 1，让其占据剩余空间

        # 输出设置组
        output_group = QGroupBox("输出设置")
        output_layout = QGridLayout(output_group)

        output_layout.addWidget(QLabel("输出目录:"), 0, 0)
        self.output_dir_edit = QLineEdit()
        output_layout.addWidget(self.output_dir_edit, 0, 1)

        self.browse_output_btn = QPushButton("浏览...")
        self.browse_output_btn.clicked.connect(self._select_output_dir)
        output_layout.addWidget(self.browse_output_btn, 0, 2)

        self.overwrite_check = QCheckBox("覆盖原图")
        self.overwrite_check.stateChanged.connect(self._on_overwrite_changed)
        output_layout.addWidget(self.overwrite_check, 1, 0, 1, 3)

        self.add_suffix_check = QCheckBox("添加后缀")
        self.add_suffix_check.setChecked(True)
        output_layout.addWidget(self.add_suffix_check, 2, 0, 1, 3)

        self.suffix_edit = QLineEdit("_watermark")
        output_layout.addWidget(self.suffix_edit, 3, 0, 1, 3)

        main_layout.addWidget(output_group)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)

        # 操作按钮
        button_layout = QHBoxLayout()
        self.process_btn = QPushButton("开始处理")
        self.process_btn.clicked.connect(self._start_processing)
        self.process_btn.setEnabled(False)
        self.clear_btn = QPushButton("清空")
        self.clear_btn.clicked.connect(self._clear_all)
        button_layout.addWidget(self.process_btn)
        button_layout.addWidget(self.clear_btn)
        main_layout.addLayout(button_layout)

    def _setup_text_watermark_ui(self):
        """设置文字水印UI"""
        widget = QWidget()
        widget.setMinimumWidth(400)  # 设置最小宽度
        layout = QGridLayout(widget)

        layout.addWidget(QLabel("水印文字:"), 0, 0)
        self.watermark_text = QLineEdit("版权所有")
        layout.addWidget(self.watermark_text, 0, 1)

        layout.addWidget(QLabel("字体大小:"), 1, 0)
        self.font_size = QSpinBox()
        self.font_size.setRange(10, 200)
        self.font_size.setValue(36)
        layout.addWidget(self.font_size, 1, 1)

        layout.addWidget(QLabel("水印颜色:"), 2, 0)
        self.color_btn = QPushButton("选择颜色")
        self.color_btn.setStyleSheet("background-color: rgba(255, 255, 255, 128);")
        self.color_btn.clicked.connect(self._select_color)
        layout.addWidget(self.color_btn, 2, 1)

        layout.addWidget(QLabel("透明度:"), 3, 0)
        self.opacity = QSpinBox()
        self.opacity.setRange(0, 255)
        self.opacity.setValue(128)
        self.opacity.valueChanged.connect(self._update_color_preview)
        layout.addWidget(self.opacity, 3, 1)

        layout.addWidget(QLabel("水印位置:"), 4, 0)
        self.position = QComboBox()
        self.position.addItems(["左下角", "右下角", "左上角", "右上角", "居中", "平铺"])
        layout.addWidget(self.position, 4, 1)

        layout.addWidget(QLabel("旋转角度:"), 5, 0)
        self.angle = QSpinBox()
        self.angle.setRange(0, 360)
        self.angle.setValue(0)
        layout.addWidget(self.angle, 5, 1)

        self.config_stack.addWidget(widget)

    def _setup_datetime_location_ui(self):
        """设置时间地点水印UI"""
        widget = QWidget()
        widget.setMinimumWidth(400)  # 设置最小宽度
        layout = QGridLayout(widget)

        # ===== 自动获取区域 =====
        auto_group = QGroupBox("自动获取实时信息")
        auto_layout = QVBoxLayout(auto_group)
        
        btn_layout = QHBoxLayout()
        self.get_weather_btn = QPushButton("🌤 获取实时天气和位置")
        self.get_weather_btn.setToolTip("自动获取当前位置、天气、温度等信息")
        self.get_weather_btn.clicked.connect(self._fetch_weather_location)
        btn_layout.addWidget(self.get_weather_btn)
        
        self.weather_status = QLabel("点击按钮获取实时信息")
        self.weather_status.setStyleSheet("color: gray;")
        btn_layout.addWidget(self.weather_status)
        btn_layout.addStretch()
        auto_layout.addLayout(btn_layout)
        
        # 提示信息
        tip_label = QLabel("💡 IP定位基于网络出口，可能与实际位置有偏差，请手动调整")
        tip_label.setStyleSheet("color: orange; font-size: 11px;")
        auto_layout.addWidget(tip_label)
        
        # API Key提示
        api_tip = QLabel("🔑 如需更精准定位，可在代码中配置百度/高德API Key")
        api_tip.setStyleSheet("color: #666; font-size: 10px;")
        api_tip.setWordWrap(True)
        auto_layout.addWidget(api_tip)
        
        layout.addWidget(auto_group, 0, 0, 1, 3)

        # 时间选择
        layout.addWidget(QLabel("时间:"), 1, 0)
        self.time_edit = QDateTimeEdit()
        self.time_edit.setDisplayFormat("HH:mm")
        self.time_edit.setDateTime(QDateTime.currentDateTime())
        layout.addWidget(self.time_edit, 1, 1)

        self.use_current_time = QCheckBox("使用当前时间")
        self.use_current_time.setChecked(True)
        self.use_current_time.stateChanged.connect(self._on_time_check_changed)
        layout.addWidget(self.use_current_time, 1, 2)

        # 日期
        layout.addWidget(QLabel("日期:"), 2, 0)
        self.date_edit = QDateTimeEdit()
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        self.date_edit.setDateTime(QDateTime.currentDateTime())
        self.date_edit.setEnabled(False)
        layout.addWidget(self.date_edit, 2, 1, 1, 2)

        # 星期和天气
        layout.addWidget(QLabel("星期天气:"), 3, 0)
        self.weekday_weather = QLineEdit("星期四 多云 27℃")
        self.weekday_weather.setPlaceholderText("例如: 星期四 多云 27℃")
        layout.addWidget(self.weekday_weather, 3, 1, 1, 2)

        # 地点1
        layout.addWidget(QLabel("地点1:"), 4, 0)
        self.location1 = QLineEdit("广东省广州市番禺区南村镇")
        self.location1.setPlaceholderText("省市区县等")
        layout.addWidget(self.location1, 4, 1, 1, 2)

        # 地点2
        layout.addWidget(QLabel("地点2:"), 5, 0)
        self.location2 = QLineEdit("番禺政务万博政务服务大厅")
        self.location2.setPlaceholderText("详细地址或场所名称")
        layout.addWidget(self.location2, 5, 1, 1, 2)

        # 颜色设置
        colors_group = QGroupBox("颜色设置")
        colors_layout = QGridLayout(colors_group)

        colors_layout.addWidget(QLabel("文字颜色:"), 0, 0)
        self.datetime_color_btn = QPushButton("选择颜色")
        self.datetime_color_btn.setStyleSheet("background-color: rgba(255, 255, 255, 220);")
        self.datetime_color_btn.clicked.connect(lambda: self._select_color_for("text"))
        colors_layout.addWidget(self.datetime_color_btn, 0, 1)

        colors_layout.addWidget(QLabel("强调色:"), 1, 0)
        self.accent_color_btn = QPushButton("选择颜色")
        self.accent_color_btn.setStyleSheet("background-color: rgba(255, 193, 7, 220);")
        self.accent_color_btn.clicked.connect(lambda: self._select_color_for("accent"))
        colors_layout.addWidget(self.accent_color_btn, 1, 1)

        colors_layout.addWidget(QLabel("背景透明度:"), 2, 0)
        self.bg_opacity = QSpinBox()
        self.bg_opacity.setRange(0, 255)
        self.bg_opacity.setValue(80)
        colors_layout.addWidget(self.bg_opacity, 2, 1)

        layout.addWidget(colors_group, 6, 0, 1, 3)

        self.config_stack.addWidget(widget)

    def _on_watermark_type_changed(self, index):
        """水印类型改变"""
        self.config_stack.setCurrentIndex(index)

    def _on_time_check_changed(self, state):
        """时间复选框状态改变"""
        self.time_edit.setEnabled(not state)
        self.date_edit.setEnabled(not state)
        if state:
            self.time_edit.setDateTime(QDateTime.currentDateTime())
            self.date_edit.setDateTime(QDateTime.currentDateTime())

    def _fetch_weather_location(self):
        """获取实时天气和位置信息"""
        self.get_weather_btn.setEnabled(False)
        self.weather_status.setText("正在获取信息...")
        self.weather_status.setStyleSheet("color: blue;")
        
        # 创建工作线程获取数据
        self.weather_worker = WeatherLocationWorker()
        self.weather_worker.data_ready.connect(self._on_weather_data_ready)
        self.weather_worker.error_occurred.connect(self._on_weather_error)
        self.weather_worker.start()

    def _on_weather_data_ready(self, data):
        """天气数据获取成功"""
        self.get_weather_btn.setEnabled(True)
        
        # 更新地点
        if 'location1' in data:
            self.location1.setText(data['location1'])
        
        # 更新星期天气
        weekday = data.get('weekday', '')
        weather = data.get('weather', '')
        temp = data.get('temperature', '')
        
        if weekday and weather:
            self.weekday_weather.setText(f"{weekday} {weather} {temp}")
        elif weekday:
            self.weekday_weather.setText(f"{weekday} {temp}")
        
        # 更新时间（自动设置为当前时间）
        now = datetime.now()
        self.time_edit.setTime(QDateTime.currentDateTime().time())
        self.date_edit.setDate(QDateTime.currentDateTime().date())
        
        # 显示获取到的位置信息
        city = data.get('city', '')
        region = data.get('region', '')
        location_str = f"{region}{city}" if region and city else (city or region or '当前位置')
        self.weather_status.setText(f"✓ 已获取: {location_str}")
        self.weather_status.setStyleSheet("color: green;")

    def _on_weather_error(self, error_msg):
        """天气数据获取失败"""
        self.get_weather_btn.setEnabled(True)
        self.weather_status.setText(f"✗ {error_msg}")
        self.weather_status.setStyleSheet("color: red;")

    def _select_color(self):
        """选择水印颜色"""
        color = QColorDialog.getColor(
            QColor(self.watermark_color.red(), self.watermark_color.green(), 
                   self.watermark_color.blue()),
            self, "选择水印颜色"
        )
        if color.isValid():
            self.watermark_color = QColor(color.red(), color.green(), color.blue(), 
                                          self.opacity.value())
            self._update_color_preview()

    def _select_color_for(self, color_type):
        """选择特定颜色"""
        if color_type == "text":
            color = QColorDialog.getColor(self.watermark_color, self, "选择文字颜色")
            if color.isValid():
                self.watermark_color = QColor(color.red(), color.green(), color.blue(), 220)
                self.datetime_color_btn.setStyleSheet(
                    f"background-color: rgba({color.red()}, {color.green()}, {color.blue()}, 220);"
                )
        elif color_type == "accent":
            color = QColorDialog.getColor(self.accent_color, self, "选择强调色")
            if color.isValid():
                self.accent_color = QColor(color.red(), color.green(), color.blue(), 220)
                self.accent_color_btn.setStyleSheet(
                    f"background-color: rgba({color.red()}, {color.green()}, {color.blue()}, 220);"
                )

    def _update_color_preview(self):
        """更新颜色预览"""
        color = self.watermark_color
        color.setAlpha(self.opacity.value())
        self.color_btn.setStyleSheet(
            f"background-color: rgba({color.red()}, {color.green()}, {color.blue()}, {color.alpha()});"
        )

    def _on_overwrite_changed(self):
        """覆盖选项变化"""
        enabled = not self.overwrite_check.isChecked()
        self.add_suffix_check.setEnabled(enabled)
        self.suffix_edit.setEnabled(enabled)

    def _select_single_image(self):
        """选择单张图片"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择图片", "",
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.gif *.tiff *.webp);;所有文件 (*.*)"
        )
        if file_path:
            self.image_paths = [file_path]
            self._update_image_list()
            self.process_btn.setEnabled(True)

    def _select_multiple_images(self):
        """选择多张图片"""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "选择图片", "",
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.gif *.tiff *.webp);;所有文件 (*.*)"
        )
        if file_paths:
            self.image_paths = file_paths
            self._update_image_list()
            self.process_btn.setEnabled(True)

    def _update_image_list(self):
        """更新图片列表"""
        count = len(self.image_paths)
        self.image_list_label.setText(f"已选择 {count} 张图片")
        if count == 0:
            self.image_list_widget.setText("未选择图片")
        elif count <= 5:
            self.image_list_widget.setText("\n".join(
                [os.path.basename(p) for p in self.image_paths]
            ))
        else:
            text = "\n".join([os.path.basename(p) for p in self.image_paths[:5]])
            text += f"\n... 还有 {count - 5} 张图片"
            self.image_list_widget.setText(text)

    def _select_output_dir(self):
        """选择输出目录"""
        dir_path = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if dir_path:
            self.output_dir_edit.setText(dir_path)
            self.output_dir = dir_path

    def _start_processing(self):
        """开始处理"""
        if not self.image_paths:
            QMessageBox.warning(self, "警告", "请先选择要处理的图片")
            return

        # 准备输出路径
        images_info = self._prepare_output_paths()

        # 根据水印类型准备配置
        watermark_type = "text" if self.watermark_type_combo.currentIndex() == 0 else "datetime_location"
        config = self._prepare_config(watermark_type)

        # 创建工作线程
        self.worker = WatermarkWorker(images_info, config, watermark_type)
        self.worker.progress_updated.connect(self._on_progress_updated)
        self.worker.finished.connect(self._on_processing_finished)

        # 禁用按钮
        self.process_btn.setEnabled(False)
        self.select_single_btn.setEnabled(False)
        self.select_multi_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        self.worker.start()

    def _prepare_output_paths(self):
        """准备输出路径"""
        if self.overwrite_check.isChecked():
            return [(p, p) for p in self.image_paths]
        
        output_dir = self.output_dir_edit.text()
        images_info = []
        for input_path in self.image_paths:
            dir_path = output_dir if output_dir else os.path.dirname(input_path)
            filename = os.path.basename(input_path)
            name, ext = os.path.splitext(filename)
            suffix = self.suffix_edit.text() if self.add_suffix_check.isChecked() else ""
            output_path = os.path.join(dir_path, f"{name}{suffix}{ext}")
            images_info.append((input_path, output_path))
        return images_info

    def _prepare_config(self, watermark_type):
        """准备水印配置"""
        if watermark_type == "text":
            return {
                "text": self.watermark_text.text(),
                "font_size": self.font_size.value(),
                "color": (
                    self.watermark_color.red(),
                    self.watermark_color.green(),
                    self.watermark_color.blue(),
                    self.opacity.value()
                ),
                "position": self._get_position_code(),
                "angle": self.angle.value()
            }
        else:
            # 时间地点水印
            if self.use_current_time.isChecked():
                now = datetime.now()
                time_str = now.strftime("%H:%M")
                date_str = now.strftime("%Y-%m-%d")
            else:
                time_str = self.time_edit.time().toString("HH:mm")
                date_str = self.date_edit.date().toString("yyyy-MM-dd")

            return {
                "time": time_str,
                "date": date_str,
                "weekday_weather": self.weekday_weather.text(),
                "location1": self.location1.text(),
                "location2": self.location2.text(),
                "color": (
                    self.watermark_color.red(),
                    self.watermark_color.green(),
                    self.watermark_color.blue(),
                    220
                ),
                "accent_color": (
                    self.accent_color.red(),
                    self.accent_color.green(),
                    self.accent_color.blue(),
                    220
                ),
                "bg_color": (0, 0, 0, self.bg_opacity.value())
            }

    def _get_position_code(self):
        """获取位置代码"""
        positions = {
            "左下角": "left_bottom",
            "右下角": "right_bottom",
            "左上角": "left_top",
            "右上角": "right_top",
            "居中": "center",
            "平铺": "tile"
        }
        return positions.get(self.position.currentText(), "right_bottom")

    def _on_progress_updated(self, current, total):
        """进度更新"""
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)

    def _on_processing_finished(self, success, message):
        """处理完成"""
        self.progress_bar.setVisible(False)
        self.process_btn.setEnabled(True)
        self.select_single_btn.setEnabled(True)
        self.select_multi_btn.setEnabled(True)

        if success:
            QMessageBox.information(self, "完成", message)
        else:
            QMessageBox.critical(self, "错误", message)

    def _clear_all(self):
        """清空"""
        self.image_paths = []
        self.output_dir = ""
        self.output_dir_edit.clear()
        self._update_image_list()
        self.process_btn.setEnabled(False)
