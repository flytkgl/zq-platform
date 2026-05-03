from sqlalchemy import Column, String, Text, Boolean, Integer

from app.base_model import BaseModel


class Demo(BaseModel):
    """
    Demo模型 - 演示数据权限和字段权限
    
    数据权限字段：
    - sys_creator_id: 创建人ID（继承自BaseModel）
    - sys_dept_id: 部门ID（继承自BaseModel）
    
    业务字段：
    - title: 标题（必填，不可隐藏）
    - content: 内容（可选，可隐藏）
    - status: 状态（必填，不可隐藏）
    - priority: 优先级（可选，可隐藏）
    - is_active: 是否激活（可选，可隐藏）
    """
    __tablename__ = "demos"

    title = Column(String(100), nullable=False, comment="标题")
    content = Column(Text, nullable=True, comment="内容")
    status = Column(Integer, default=1, comment="状态：0=草稿，1=发布，2=归档")
    priority = Column(Integer, default=0, comment="优先级：0=低，1=中，2=高")
    is_active = Column(Boolean, default=True, comment="是否激活")
