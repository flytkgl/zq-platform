from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship

from app.base_model import BaseModel


class Province(BaseModel):
    """省份模型"""
    __tablename__ = "core_province"

    code = Column(String(20), unique=True, nullable=False, index=True, comment="省份代码")
    name = Column(String(100), nullable=False, comment="省份名称")
    sort = Column(Integer, default=0, comment="排序")

    # 关联关系
    cities = relationship("City", back_populates="province", cascade="all, delete-orphan")


class City(BaseModel):
    """城市模型"""
    __tablename__ = "core_city"

    code = Column(String(20), unique=True, nullable=False, index=True, comment="城市代码")
    name = Column(String(100), nullable=False, comment="城市名称")
    province_code = Column(String(20), ForeignKey("core_province.code", ondelete="CASCADE"), nullable=False, comment="省份代码")
    sort = Column(Integer, default=0, comment="排序")

    # 关联关系
    province = relationship("Province", back_populates="cities")
    areas = relationship("Area", back_populates="city", cascade="all, delete-orphan")


class Area(BaseModel):
    """区县模型"""
    __tablename__ = "core_area"

    code = Column(String(20), unique=True, nullable=False, index=True, comment="区县代码")
    name = Column(String(100), nullable=False, comment="区县名称")
    province_code = Column(String(20), nullable=False, index=True, comment="省份代码")
    city_code = Column(String(20), ForeignKey("core_city.code", ondelete="CASCADE"), nullable=False, comment="城市代码")
    sort = Column(Integer, default=0, comment="排序")

    # 关联关系
    city = relationship("City", back_populates="areas")
    streets = relationship("Street", back_populates="area", cascade="all, delete-orphan")


class Street(BaseModel):
    """街道/乡镇模型"""
    __tablename__ = "core_street"

    code = Column(String(20), unique=True, nullable=False, index=True, comment="街道代码")
    name = Column(String(100), nullable=False, comment="街道名称")
    province_code = Column(String(20), nullable=False, index=True, comment="省份代码")
    city_code = Column(String(20), nullable=False, index=True, comment="城市代码")
    area_code = Column(String(20), ForeignKey("core_area.code", ondelete="CASCADE"), nullable=False, comment="区县代码")
    sort = Column(Integer, default=0, comment="排序")

    # 关联关系
    area = relationship("Area", back_populates="streets")
    villages = relationship("Village", back_populates="street", cascade="all, delete-orphan")


class Village(BaseModel):
    """村/社区模型"""
    __tablename__ = "core_village"

    code = Column(String(20), unique=True, nullable=False, index=True, comment="村庄代码")
    name = Column(String(100), nullable=False, comment="村庄名称")
    province_code = Column(String(20), nullable=False, index=True, comment="省份代码")
    city_code = Column(String(20), nullable=False, index=True, comment="城市代码")
    area_code = Column(String(20), nullable=False, index=True, comment="区县代码")
    street_code = Column(String(20), ForeignKey("core_street.code", ondelete="CASCADE"), nullable=False, comment="街道代码")
    sort = Column(Integer, default=0, comment="排序")

    # 关联关系
    street = relationship("Street", back_populates="villages")
