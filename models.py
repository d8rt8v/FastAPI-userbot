from pydantic import BaseModel
from typing import Optional


class CreateSupergroupRequest(BaseModel):
    title: str
    description: str = None

class AddChatMembersRequest(BaseModel):
    group_id: int
    user_ids: list[str]

class BanChatMemberRequest(BaseModel):
    chat_id: int
    user_id: int

class SendMessageRequest(BaseModel):
    user_id: int
    text: str

class AddContactRequest(BaseModel):
    user_id: int  
    first_name: str

class PromoteChatMemberRequest(BaseModel):
    chat_id: int
    user_id: int
    can_manage_chat: bool = True
    can_delete_messages: bool = True
    can_manage_video_chats: bool = True
    can_restrict_members: bool = True
    can_promote_members: bool = True
    can_change_info: bool = True
    can_post_messages: bool = True
    can_edit_messages: bool = True
    can_invite_users: bool = True
    can_pin_messages: bool = True
    is_anonymous: bool = False
 

class GetChatMembersRequest(BaseModel):
    chat_id: int
    limit: Optional[int] = None
    filter: Optional[str] = None
