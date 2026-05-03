from typing import List, Dict, Any, Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.region.model import Province, City, Area, Street, Village
from core.region.schema import RegionTreeNode


class RegionService:
    """省市区街道村五级行政区划服务类"""

    # ========== 省份 CRUD ==========
    @classmethod
    async def create_province(cls, db: AsyncSession, data: Dict[str, Any]) -> Province:
        """创建省份"""
        province = Province(**data)
        db.add(province)
        await db.commit()
        await db.refresh(province)
        return province

    @classmethod
    async def update_province(cls, db: AsyncSession, province_id: str, data: Dict[str, Any]) -> Optional[Province]:
        """更新省份"""
        stmt = select(Province).where(Province.id == province_id)
        result = await db.execute(stmt)
        province = result.scalar_one_or_none()
        if province:
            for key, value in data.items():
                setattr(province, key, value)
            await db.commit()
            await db.refresh(province)
        return province

    @classmethod
    async def delete_province(cls, db: AsyncSession, province_id: str) -> bool:
        """删除省份"""
        stmt = select(Province).where(Province.id == province_id)
        result = await db.execute(stmt)
        province = result.scalar_one_or_none()
        if province:
            await db.delete(province)
            await db.commit()
            return True
        return False

    # ========== 城市 CRUD ==========
    @classmethod
    async def create_city(cls, db: AsyncSession, data: Dict[str, Any]) -> City:
        """创建城市"""
        city = City(**data)
        db.add(city)
        await db.commit()
        await db.refresh(city)
        return city

    @classmethod
    async def update_city(cls, db: AsyncSession, city_id: str, data: Dict[str, Any]) -> Optional[City]:
        """更新城市"""
        stmt = select(City).where(City.id == city_id)
        result = await db.execute(stmt)
        city = result.scalar_one_or_none()
        if city:
            for key, value in data.items():
                setattr(city, key, value)
            await db.commit()
            await db.refresh(city)
        return city

    @classmethod
    async def delete_city(cls, db: AsyncSession, city_id: str) -> bool:
        """删除城市"""
        stmt = select(City).where(City.id == city_id)
        result = await db.execute(stmt)
        city = result.scalar_one_or_none()
        if city:
            await db.delete(city)
            await db.commit()
            return True
        return False

    # ========== 区县 CRUD ==========
    @classmethod
    async def create_area(cls, db: AsyncSession, data: Dict[str, Any]) -> Area:
        """创建区县"""
        area = Area(**data)
        db.add(area)
        await db.commit()
        await db.refresh(area)
        return area

    @classmethod
    async def update_area(cls, db: AsyncSession, area_id: str, data: Dict[str, Any]) -> Optional[Area]:
        """更新区县"""
        stmt = select(Area).where(Area.id == area_id)
        result = await db.execute(stmt)
        area = result.scalar_one_or_none()
        if area:
            for key, value in data.items():
                setattr(area, key, value)
            await db.commit()
            await db.refresh(area)
        return area

    @classmethod
    async def delete_area(cls, db: AsyncSession, area_id: str) -> bool:
        """删除区县"""
        stmt = select(Area).where(Area.id == area_id)
        result = await db.execute(stmt)
        area = result.scalar_one_or_none()
        if area:
            await db.delete(area)
            await db.commit()
            return True
        return False

    # ========== 街道 CRUD ==========
    @classmethod
    async def create_street(cls, db: AsyncSession, data: Dict[str, Any]) -> Street:
        """创建街道"""
        street = Street(**data)
        db.add(street)
        await db.commit()
        await db.refresh(street)
        return street

    @classmethod
    async def update_street(cls, db: AsyncSession, street_id: str, data: Dict[str, Any]) -> Optional[Street]:
        """更新街道"""
        stmt = select(Street).where(Street.id == street_id)
        result = await db.execute(stmt)
        street = result.scalar_one_or_none()
        if street:
            for key, value in data.items():
                setattr(street, key, value)
            await db.commit()
            await db.refresh(street)
        return street

    @classmethod
    async def delete_street(cls, db: AsyncSession, street_id: str) -> bool:
        """删除街道"""
        stmt = select(Street).where(Street.id == street_id)
        result = await db.execute(stmt)
        street = result.scalar_one_or_none()
        if street:
            await db.delete(street)
            await db.commit()
            return True
        return False

    # ========== 村庄 CRUD ==========
    @classmethod
    async def create_village(cls, db: AsyncSession, data: Dict[str, Any]) -> Village:
        """创建村庄"""
        village = Village(**data)
        db.add(village)
        await db.commit()
        await db.refresh(village)
        return village

    @classmethod
    async def update_village(cls, db: AsyncSession, village_id: str, data: Dict[str, Any]) -> Optional[Village]:
        """更新村庄"""
        stmt = select(Village).where(Village.id == village_id)
        result = await db.execute(stmt)
        village = result.scalar_one_or_none()
        if village:
            for key, value in data.items():
                setattr(village, key, value)
            await db.commit()
            await db.refresh(village)
        return village

    @classmethod
    async def delete_village(cls, db: AsyncSession, village_id: str) -> bool:
        """删除村庄"""
        stmt = select(Village).where(Village.id == village_id)
        result = await db.execute(stmt)
        village = result.scalar_one_or_none()
        if village:
            await db.delete(village)
            await db.commit()
            return True
        return False

    @classmethod
    async def get_tree(cls, db: AsyncSession, level: int = 3) -> List[Dict[str, Any]]:
        """
        获取行政区划树形结构数据
        
        Args:
            db: 数据库会话
            level: 级联层级 1=省 2=省市 3=省市区 4=省市区街道 5=省市区街道村
            
        Returns:
            树形结构数据列表
        """
        # 查询所有省份
        stmt = select(Province).order_by(Province.sort, Province.code)
        result = await db.execute(stmt)
        provinces = result.scalars().all()

        tree_data = []
        for province in provinces:
            province_node = {
                "code": province.code,
                "name": province.name,
            }

            if level >= 2:
                # 查询该省份下的所有城市
                city_stmt = select(City).where(
                    City.province_code == province.code
                ).order_by(City.sort, City.code)
                city_result = await db.execute(city_stmt)
                cities = city_result.scalars().all()

                city_nodes = []
                for city in cities:
                    city_node = {
                        "code": city.code,
                        "name": city.name,
                    }

                    if level >= 3:
                        # 查询该城市下的所有区县
                        area_stmt = select(Area).where(
                            Area.city_code == city.code
                        ).order_by(Area.sort, Area.code)
                        area_result = await db.execute(area_stmt)
                        areas = area_result.scalars().all()

                        area_nodes = []
                        for area in areas:
                            area_node = {
                                "code": area.code,
                                "name": area.name,
                            }

                            if level >= 4:
                                # 查询该区县下的所有街道
                                street_stmt = select(Street).where(
                                    Street.area_code == area.code
                                ).order_by(Street.sort, Street.code)
                                street_result = await db.execute(street_stmt)
                                streets = street_result.scalars().all()

                                street_nodes = []
                                for street in streets:
                                    street_node = {
                                        "code": street.code,
                                        "name": street.name,
                                    }

                                    if level >= 5:
                                        # 查询该街道下的所有村庄
                                        village_stmt = select(Village).where(
                                            Village.street_code == street.code
                                        ).order_by(Village.sort, Village.code)
                                        village_result = await db.execute(village_stmt)
                                        villages = village_result.scalars().all()

                                        village_nodes = [
                                            {
                                                "code": village.code,
                                                "name": village.name,
                                            }
                                            for village in villages
                                        ]

                                        if village_nodes:
                                            street_node["children"] = village_nodes

                                    street_nodes.append(street_node)

                                if street_nodes:
                                    area_node["children"] = street_nodes

                            area_nodes.append(area_node)

                        if area_nodes:
                            city_node["children"] = area_nodes

                    city_nodes.append(city_node)

                if city_nodes:
                    province_node["children"] = city_nodes

            tree_data.append(province_node)

        return tree_data

    @classmethod
    async def get_provinces(cls, db: AsyncSession) -> List[Province]:
        """获取所有省份"""
        stmt = select(Province).order_by(Province.sort, Province.code)
        result = await db.execute(stmt)
        return result.scalars().all()

    @classmethod
    async def get_cities_by_province(cls, db: AsyncSession, province_code: str) -> List[City]:
        """根据省份代码获取城市列表"""
        stmt = select(City).where(
            City.province_code == province_code
        ).order_by(City.sort, City.code)
        result = await db.execute(stmt)
        return result.scalars().all()

    @classmethod
    async def get_areas_by_city(cls, db: AsyncSession, city_code: str) -> List[Area]:
        """根据城市代码获取区县列表"""
        stmt = select(Area).where(
            Area.city_code == city_code
        ).order_by(Area.sort, Area.code)
        result = await db.execute(stmt)
        return result.scalars().all()

    @classmethod
    async def get_streets_by_area(cls, db: AsyncSession, area_code: str) -> List[Street]:
        """根据区县代码获取街道列表"""
        stmt = select(Street).where(
            Street.area_code == area_code
        ).order_by(Street.sort, Street.code)
        result = await db.execute(stmt)
        return result.scalars().all()

    @classmethod
    async def get_villages_by_street(cls, db: AsyncSession, street_code: str) -> List[Village]:
        """根据街道代码获取村庄列表"""
        stmt = select(Village).where(
            Village.street_code == street_code
        ).order_by(Village.sort, Village.code)
        result = await db.execute(stmt)
        return result.scalars().all()

    @classmethod
    async def get_region_name(cls, db: AsyncSession, code: str) -> str:
        """根据区域代码获取名称"""
        # 尝试从省份查找
        stmt = select(Province).where(Province.code == code)
        result = await db.execute(stmt)
        province = result.scalar_one_or_none()
        if province:
            return province.name

        # 尝试从城市查找
        stmt = select(City).where(City.code == code)
        result = await db.execute(stmt)
        city = result.scalar_one_or_none()
        if city:
            return city.name

        # 尝试从区县查找
        stmt = select(Area).where(Area.code == code)
        result = await db.execute(stmt)
        area = result.scalar_one_or_none()
        if area:
            return area.name

        # 尝试从街道查找
        stmt = select(Street).where(Street.code == code)
        result = await db.execute(stmt)
        street = result.scalar_one_or_none()
        if street:
            return street.name

        # 尝试从村庄查找
        stmt = select(Village).where(Village.code == code)
        result = await db.execute(stmt)
        village = result.scalar_one_or_none()
        if village:
            return village.name

        return ""
