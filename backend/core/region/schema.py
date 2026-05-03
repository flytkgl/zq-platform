from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class RegionBase(BaseModel):
    """区域基础 Schema"""
    code: str
    name: str


class ProvinceResponse(RegionBase):
    """省份响应 Schema"""
    id: str
    sort: int = 0

    model_config = ConfigDict(from_attributes=True)


class CityResponse(RegionBase):
    """城市响应 Schema"""
    id: str
    province_code: str
    sort: int = 0

    model_config = ConfigDict(from_attributes=True)


class AreaResponse(RegionBase):
    """区县响应 Schema"""
    id: str
    province_code: str
    city_code: str
    sort: int = 0

    model_config = ConfigDict(from_attributes=True)


class StreetResponse(RegionBase):
    """街道响应 Schema"""
    id: str
    province_code: str
    city_code: str
    area_code: str
    sort: int = 0

    model_config = ConfigDict(from_attributes=True)


class VillageResponse(RegionBase):
    """村庄响应 Schema"""
    id: str
    province_code: str
    city_code: str
    area_code: str
    street_code: str
    sort: int = 0

    model_config = ConfigDict(from_attributes=True)


class RegionTreeNode(BaseModel):
    """区域树节点 Schema（用于级联选择器）"""
    code: str
    name: str
    children: Optional[List['RegionTreeNode']] = None

    model_config = ConfigDict(from_attributes=True)
