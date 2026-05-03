from datetime import datetime

from sqlalchemy import Column, String, Text, Boolean, Integer, DateTime, Index, JSON
from sqlalchemy.sql import func

from app.base_model import BaseModel


class Conversation(BaseModel):
    """会话表"""
    __tablename__ = "core_conversation"

    type = Column(String(20), nullable=False, default="private", comment="会话类型: private/group")
    name = Column(String(100), nullable=True, comment="群聊名称（单聊为空）")
    avatar = Column(String(500), nullable=True, comment="群头像文件ID")
    owner_id = Column(String(21), nullable=True, comment="群主用户ID（逻辑外键关联core_user）")
    last_message_id = Column(String(21), nullable=True, comment="最后一条消息ID（逻辑外键）")
    last_message_time = Column(DateTime, nullable=True, comment="最后消息时间")
    last_message_preview = Column(String(200), nullable=True, comment="最后消息预览文本")
    member_count = Column(Integer, default=0, comment="成员数")

    __table_args__ = (
        Index("idx_conversation_type", "type"),
        Index("idx_conversation_last_msg_time", "last_message_time"),
    )


class ConversationMember(BaseModel):
    """会话成员表"""
    __tablename__ = "core_conversation_member"

    conversation_id = Column(String(21), nullable=False, comment="会话ID（逻辑外键关联core_conversation）")
    user_id = Column(String(21), nullable=False, comment="用户ID（逻辑外键关联core_user）")
    role = Column(String(20), default="member", comment="角色: owner/admin/member")
    nickname = Column(String(50), nullable=True, comment="群内昵称")
    is_muted = Column(Boolean, default=False, comment="是否免打扰")
    is_pinned = Column(Boolean, default=False, comment="是否置顶")
    unread_count = Column(Integer, default=0, comment="未读消息数")
    last_read_message_id = Column(String(21), nullable=True, comment="最后已读消息ID")
    joined_at = Column(DateTime, server_default=func.now(), comment="加入时间")

    __table_args__ = (
        Index("idx_conv_member_conv_id", "conversation_id"),
        Index("idx_conv_member_user_id", "user_id"),
        Index("idx_conv_member_conv_user", "conversation_id", "user_id", unique=True),
    )


class ChatMessage(BaseModel):
    """聊天消息表"""
    __tablename__ = "core_chat_message"

    conversation_id = Column(String(21), nullable=False, comment="会话ID（逻辑外键关联core_conversation）")
    sender_id = Column(String(21), nullable=False, comment="发送者用户ID（逻辑外键关联core_user）")
    msg_type = Column(String(20), default="text", comment="消息类型: text/image/file/voice/system/recall")
    content = Column(Text, nullable=True, comment="文本内容")
    file_id = Column(String(21), nullable=True, comment="文件ID（逻辑外键关联core_file_manager）")
    reply_to_id = Column(String(21), nullable=True, comment="回复的消息ID（逻辑外键）")
    is_recalled = Column(Boolean, default=False, comment="是否已撤回")
    recalled_at = Column(DateTime, nullable=True, comment="撤回时间")
    extra = Column(JSON, nullable=True, comment="扩展数据（@提醒列表、链接预览等）")

    __table_args__ = (
        Index("idx_chat_msg_conv_id_created", "conversation_id", "sys_create_datetime"),
        Index("idx_chat_msg_sender_id", "sender_id"),
    )
