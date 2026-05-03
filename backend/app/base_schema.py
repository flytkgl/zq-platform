from datetime import datetime
from typing import Annotated, Generic, TypeVar, List, Optional

from pydantic import BaseModel
from pydantic.functional_serializers import PlainSerializer

from app.timezone import APP_TIMEZONE

T = TypeVar("T")


def _format_datetime(v: datetime) -> str | None:
    """将 datetime 转换为配置时区并格式化为字符串"""
    if v is None:
        return None
    if v.tzinfo is not None:
        v = v.astimezone(APP_TIMEZONE)
    return v.strftime("%Y-%m-%d %H:%M:%S")


CSTDatetime = Annotated[datetime, PlainSerializer(_format_datetime, return_type=str)]


class PaginatedResponse(BaseModel, Generic[T]):
    """通用分页响应模型"""
    items: List[T]
    total: int


class ResponseModel(BaseModel):
    """通用响应模型"""
    message: str = "success"
    data: Optional[dict | list] = None
