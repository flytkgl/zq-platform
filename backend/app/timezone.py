"""
时区工具模块
提供全局统一的时区配置和日期格式化工具
"""
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo

from app.config import settings

# 根据配置加载时区
APP_TIMEZONE = ZoneInfo(settings.TIMEZONE)


def format_datetime(dt: datetime, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """将 datetime 格式化为指定格式的字符串，自动处理时区转换"""
    if dt is None:
        return ""
    if dt.tzinfo is not None:
        dt = dt.astimezone(APP_TIMEZONE)
    return dt.strftime(fmt)


def convert_to_app_timezone(dt: datetime) -> datetime:
    """将 datetime 转换为应用配置的时区"""
    if dt is None:
        return dt
    if dt.tzinfo is not None:
        return dt.astimezone(APP_TIMEZONE)
    return dt
