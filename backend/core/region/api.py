from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.base_schema import ResponseModel
from core.region.service import RegionService
from core.region.model import Province, City, Area, Street, Village
from core.region.schema import (
    ProvinceResponse, CityResponse, AreaResponse, 
    StreetResponse, VillageResponse
)

router = APIRouter(prefix="/regions", tags=["行政区划管理"])


@router.get("/tree", summary="获取行政区划树形数据")
async def get_region_tree(
    level: int = Query(default=3, ge=1, le=5, description="级联层级：1=省，2=省市，3=省市区，4=省市区街道，5=省市区街道村"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取行政区划树形结构数据，用于级联选择器
    
    - level: 1=仅省份，2=省市两级，3=省市区三级，4=省市区街道四级，5=省市区街道村五级
    """
    tree_data = await RegionService.get_tree(db, level=level)
    return tree_data


@router.get("/provinces", response_model=List[ProvinceResponse], summary="获取省份列表")
async def get_provinces(db: AsyncSession = Depends(get_db)):
    """获取所有省份列表"""
    provinces = await RegionService.get_provinces(db)
    return provinces


@router.post("/provinces", response_model=ProvinceResponse, summary="创建省份")
async def create_province(data: dict, db: AsyncSession = Depends(get_db)):
    """创建省份"""
    province = await RegionService.create_province(db, data)
    return province


@router.put("/provinces/{province_id}", response_model=ProvinceResponse, summary="更新省份")
async def update_province(province_id: str, data: dict, db: AsyncSession = Depends(get_db)):
    """更新省份"""
    province = await RegionService.update_province(db, province_id, data)
    if not province:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="省份不存在")
    return province


@router.delete("/provinces/{province_id}", response_model=ResponseModel, summary="删除省份")
async def delete_province(province_id: str, db: AsyncSession = Depends(get_db)):
    """删除省份"""
    success = await RegionService.delete_province(db, province_id)
    if not success:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="省份不存在")
    return ResponseModel(message="删除成功")


@router.get("/cities", response_model=List[CityResponse], summary="获取城市列表")
async def get_cities(
    province_code: str = Query(None, description="省份代码"),
    db: AsyncSession = Depends(get_db)
):
    """根据省份代码获取城市列表"""
    if province_code:
        cities = await RegionService.get_cities_by_province(db, province_code)
    else:
        stmt = select(City).order_by(City.sort, City.code)
        result = await db.execute(stmt)
        cities = result.scalars().all()
    return cities


@router.post("/cities", response_model=CityResponse, summary="创建城市")
async def create_city(data: dict, db: AsyncSession = Depends(get_db)):
    """创建城市"""
    city = await RegionService.create_city(db, data)
    return city


@router.put("/cities/{city_id}", response_model=CityResponse, summary="更新城市")
async def update_city(city_id: str, data: dict, db: AsyncSession = Depends(get_db)):
    """更新城市"""
    city = await RegionService.update_city(db, city_id, data)
    if not city:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="城市不存在")
    return city


@router.delete("/cities/{city_id}", response_model=ResponseModel, summary="删除城市")
async def delete_city(city_id: str, db: AsyncSession = Depends(get_db)):
    """删除城市"""
    success = await RegionService.delete_city(db, city_id)
    if not success:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="城市不存在")
    return ResponseModel(message="删除成功")


@router.get("/areas", response_model=List[AreaResponse], summary="获取区县列表")
async def get_areas(
    city_code: str = Query(None, description="城市代码"),
    db: AsyncSession = Depends(get_db)
):
    """根据城市代码获取区县列表"""
    if city_code:
        areas = await RegionService.get_areas_by_city(db, city_code)
    else:
        stmt = select(Area).order_by(Area.sort, Area.code)
        result = await db.execute(stmt)
        areas = result.scalars().all()
    return areas


@router.post("/areas", response_model=AreaResponse, summary="创建区县")
async def create_area(data: dict, db: AsyncSession = Depends(get_db)):
    """创建区县"""
    area = await RegionService.create_area(db, data)
    return area


@router.put("/areas/{area_id}", response_model=AreaResponse, summary="更新区县")
async def update_area(area_id: str, data: dict, db: AsyncSession = Depends(get_db)):
    """更新区县"""
    area = await RegionService.update_area(db, area_id, data)
    if not area:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="区县不存在")
    return area


@router.delete("/areas/{area_id}", response_model=ResponseModel, summary="删除区县")
async def delete_area(area_id: str, db: AsyncSession = Depends(get_db)):
    """删除区县"""
    success = await RegionService.delete_area(db, area_id)
    if not success:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="区县不存在")
    return ResponseModel(message="删除成功")


@router.get("/streets", response_model=List[StreetResponse], summary="获取街道列表")
async def get_streets(
    area_code: str = Query(None, description="区县代码"),
    db: AsyncSession = Depends(get_db)
):
    """根据区县代码获取街道列表"""
    if area_code:
        streets = await RegionService.get_streets_by_area(db, area_code)
    else:
        stmt = select(Street).order_by(Street.sort, Street.code).limit(1000)
        result = await db.execute(stmt)
        streets = result.scalars().all()
    return streets


@router.post("/streets", response_model=StreetResponse, summary="创建街道")
async def create_street(data: dict, db: AsyncSession = Depends(get_db)):
    """创建街道"""
    street = await RegionService.create_street(db, data)
    return street


@router.put("/streets/{street_id}", response_model=StreetResponse, summary="更新街道")
async def update_street(street_id: str, data: dict, db: AsyncSession = Depends(get_db)):
    """更新街道"""
    street = await RegionService.update_street(db, street_id, data)
    if not street:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="街道不存在")
    return street


@router.delete("/streets/{street_id}", response_model=ResponseModel, summary="删除街道")
async def delete_street(street_id: str, db: AsyncSession = Depends(get_db)):
    """删除街道"""
    success = await RegionService.delete_street(db, street_id)
    if not success:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="街道不存在")
    return ResponseModel(message="删除成功")


@router.get("/villages", response_model=List[VillageResponse], summary="获取村庄列表")
async def get_villages(
    street_code: str = Query(None, description="街道代码"),
    db: AsyncSession = Depends(get_db)
):
    """根据街道代码获取村庄列表"""
    if street_code:
        villages = await RegionService.get_villages_by_street(db, street_code)
    else:
        stmt = select(Village).order_by(Village.sort, Village.code).limit(1000)
        result = await db.execute(stmt)
        villages = result.scalars().all()
    return villages


@router.post("/villages", response_model=VillageResponse, summary="创建村庄")
async def create_village(data: dict, db: AsyncSession = Depends(get_db)):
    """创建村庄"""
    village = await RegionService.create_village(db, data)
    return village


@router.put("/villages/{village_id}", response_model=VillageResponse, summary="更新村庄")
async def update_village(village_id: str, data: dict, db: AsyncSession = Depends(get_db)):
    """更新村庄"""
    village = await RegionService.update_village(db, village_id, data)
    if not village:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="村庄不存在")
    return village


@router.delete("/villages/{village_id}", response_model=ResponseModel, summary="删除村庄")
async def delete_village(village_id: str, db: AsyncSession = Depends(get_db)):
    """删除村庄"""
    success = await RegionService.delete_village(db, village_id)
    if not success:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="村庄不存在")
    return ResponseModel(message="删除成功")


@router.get("/name/{code}", response_model=ResponseModel, summary="根据代码获取名称")
async def get_region_name(
    code: str,
    db: AsyncSession = Depends(get_db)
):
    """根据区域代码获取区域名称"""
    name = await RegionService.get_region_name(db, code)
    return ResponseModel(data={"name": name})
