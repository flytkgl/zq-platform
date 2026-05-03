from datetime import datetime

from nanoid import generate
from sqlalchemy import Column, String, DateTime, Boolean, Integer
from sqlalchemy.sql import func

from app.database import Base


def generate_nanoid() -> str:
    """生成21位的NanoId"""
    return generate(size=21)


class BaseModel(Base):
    """
    公共基础模型
    所有业务模型都应继承此类
    """
    __abstract__ = True

    id = Column(String(21), primary_key=True, default=generate_nanoid, comment="主键ID(NanoId)")
    sort = Column(Integer, default=0, comment="排序")
    is_deleted = Column(Boolean, default=False, index=True, comment="是否删除")
    sys_create_datetime = Column(DateTime, server_default=func.now(), index=True, comment="创建时间")
    sys_update_datetime = Column(DateTime, server_default=func.now(), onupdate=func.now(), index=True, comment="更新时间")
    sys_creator_id = Column(String(21), nullable=True, index=True, comment="创建人ID（逻辑外键关联core_user）")
    sys_modifier_id = Column(String(21), nullable=True, comment="修改人ID（逻辑外键关联core_user）")
    sys_dept_id = Column(String(21), nullable=True, index=True, comment="部门ID（逻辑外键关联core_dept）")
