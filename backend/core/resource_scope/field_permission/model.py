from sqlalchemy import Column, String, Index

from app.base_model import BaseModel


class ResourceFieldPermissionConfig(BaseModel):
    """角色资源字段权限配置（列权限）"""
    __tablename__ = "sys_role_resource_field_permission_config"

    role_id = Column(String(50), nullable=False, comment="角色ID")
    resource_type = Column(String(100), nullable=False, comment="资源类型")
    field_name = Column(String(100), nullable=False, comment="字段名称")
    permission_type = Column(
        String(20),
        nullable=False,
        default="read",
        comment="权限类型: read/write/hidden/masked"
    )
    mask_rule = Column(String(50), nullable=True, comment="脱敏规则: phone/email/id_card/name")

    __table_args__ = (
        Index('idx_role_resource_field', 'role_id', 'resource_type', 'field_name', unique=True),
        Index('idx_role_resource', 'role_id', 'resource_type'),
    )
