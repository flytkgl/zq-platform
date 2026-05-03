from datetime import datetime
from typing import Optional, List, Dict, Any

from pydantic import BaseModel, ConfigDict, Field


# ============ 会话 Schema ============

class ConversationBase(BaseModel):
    """会话基础Schema"""
    type: str = Field(default="private", description="会话类型: private/group")
    name: Optional[str] = Field(default=None, max_length=100, description="群聊名称")
    avatar: Optional[str] = Field(default=None, description="群头像文件ID")


class CreatePrivateConversationIn(BaseModel):
    """创建单聊会话"""
    user_id: str = Field(..., description="对方用户ID")


class CreateGroupConversationIn(BaseModel):
    """创建群聊会话"""
    name: str = Field(..., max_length=100, description="群聊名称")
    member_ids: List[str] = Field(..., description="成员用户ID列表")
    avatar: Optional[str] = Field(default=None, description="群头像文件ID")


class UpdateConversationIn(BaseModel):
    """更新群聊信息"""
    name: Optional[str] = Field(default=None, max_length=100, description="群聊名称")
    avatar: Optional[str] = Field(default=None, description="群头像文件ID")


class ConversationMemberOut(BaseModel):
    """会话成员输出"""
    id: str
    user_id: str
    role: str
    nickname: Optional[str] = None
    is_muted: bool = False
    is_pinned: bool = False
    unread_count: int = 0
    joined_at: Optional[datetime] = None
    # 关联用户信息（由API填充）
    user_name: Optional[str] = None
    user_avatar: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ConversationOut(BaseModel):
    """会话输出"""
    id: str
    type: str
    name: Optional[str] = None
    avatar: Optional[str] = None
    owner_id: Optional[str] = None
    last_message_time: Optional[datetime] = None
    last_message_preview: Optional[str] = None
    member_count: int = 0
    sys_create_datetime: Optional[datetime] = None
    # 当前用户相关（由API填充）
    unread_count: int = 0
    is_muted: bool = False
    is_pinned: bool = False
    # 单聊对方信息（由API填充）
    peer_user_id: Optional[str] = None
    peer_user_name: Optional[str] = None
    peer_user_avatar: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ConversationListOut(BaseModel):
    """会话列表输出"""
    items: List[ConversationOut]
    total: int


# ============ 成员操作 Schema ============

class AddMembersIn(BaseModel):
    """添加成员"""
    user_ids: List[str] = Field(..., description="用户ID列表")


class ConversationSettingIn(BaseModel):
    """会话设置（置顶/免打扰）"""
    value: bool = Field(..., description="设置值")


# ============ 消息 Schema ============

class SendMessageIn(BaseModel):
    """发送消息"""
    msg_type: str = Field(default="text", description="消息类型: text/image/file/voice")
    content: Optional[str] = Field(default=None, description="文本内容")
    file_id: Optional[str] = Field(default=None, description="文件ID")
    reply_to_id: Optional[str] = Field(default=None, description="回复的消息ID")
    extra: Optional[Dict[str, Any]] = Field(default=None, description="扩展数据")


class ChatMessageOut(BaseModel):
    """消息输出"""
    id: str
    conversation_id: str
    sender_id: str
    msg_type: str
    content: Optional[str] = None
    file_id: Optional[str] = None
    reply_to_id: Optional[str] = None
    is_recalled: bool = False
    recalled_at: Optional[datetime] = None
    extra: Optional[Dict[str, Any]] = None
    sys_create_datetime: Optional[datetime] = None
    # 关联信息（由API填充）
    sender_name: Optional[str] = None
    sender_avatar: Optional[str] = None
    # 回复消息预览（由API填充）
    reply_to_preview: Optional[str] = None
    reply_to_sender_name: Optional[str] = None
    # 文件信息（由API填充）
    file_name: Optional[str] = None
    file_url: Optional[str] = None
    file_size: Optional[int] = None
    file_ext: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ChatMessageListOut(BaseModel):
    """消息列表输出（游标分页）"""
    items: List[ChatMessageOut]
    has_more: bool = False


class RecallMessageIn(BaseModel):
    """撤回消息"""
    pass


class MarkReadIn(BaseModel):
    """标记已读"""
    message_id: str = Field(..., description="已读到的消息ID")
