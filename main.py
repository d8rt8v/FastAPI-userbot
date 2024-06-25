import os
import io
from fastapi import FastAPI, HTTPException, Form, Depends, UploadFile, File
from pyrogram import Client
from pyrogram.enums import ChatMembersFilter
from pyrogram.types import ChatPrivileges
from pyrogram.errors import PeerIdInvalid, ChatAdminRequired, UserNotParticipant
from contextlib import asynccontextmanager
from fastapi.security import HTTPAuthorizationCredentials

import logging
logging.basicConfig(level=logging.INFO)

from models import CreateSupergroupRequest, AddChatMembersRequest, BanChatMemberRequest, SendMessageRequest, AddContactRequest, PromoteChatMemberRequest, GetChatMembersRequest
from errors import UserNotFoundError, GroupNotFoundError, UsernameNotOccupied
from auth import authenticate
from dotenv import load_dotenv

### Session setup ###
load_dotenv()

API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
PHONE_NUMBER = os.getenv("PHONE_NUMBER")
SESSION_NAME = "my_session"
SESSION_FILE = f"{SESSION_NAME}.session"
app = FastAPI(title="FastAPI Telegram Group Manager Backend")

pyro_client = Client(SESSION_NAME, api_id=API_ID, api_hash=API_HASH, phone_number=PHONE_NUMBER,workdir=os.getcwd())

@asynccontextmanager
async def lifespan(app: FastAPI):
    await pyro_client.start()
    yield
    await pyro_client.stop()

app.router.lifespan_context = lifespan
### Endpoints ###

@app.post("/create_supergroup")
async def create_supergroup(request: CreateSupergroupRequest, credentials: HTTPAuthorizationCredentials = Depends(authenticate)):
    try:
        chat = await pyro_client.create_supergroup(request.title, request.description)
        return {"groupid": chat.id, "title": chat.title, "description": request.description}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/add_chat_members")
async def add_chat_members(request: AddChatMembersRequest, credentials: HTTPAuthorizationCredentials = Depends(authenticate)):
    try:
        await pyro_client.add_chat_members(request.group_id, request.user_ids)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    

@app.delete("/ban_chat_member")
async def ban_chat_member(request: BanChatMemberRequest, credentials: HTTPAuthorizationCredentials = Depends(authenticate)):
    try:
        result = await pyro_client.ban_chat_member(
            request.chat_id,
            request.user_id        )
        return {"status": "success"}
    except ChatAdminRequired:
        raise PermissionError("You need to be an admin to ban users.")
    except UserNotParticipant:
        raise UserNotFoundError(request.user_id)
    except PeerIdInvalid:
        raise GroupNotFoundError(request.chat_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@app.post("/send_message")
async def send_message(request: SendMessageRequest, credentials: HTTPAuthorizationCredentials = Depends(authenticate)):
    try:
        message = await pyro_client.send_message(request.user_id, request.text)
        return {"message_id": message.id, "status": "success"}
    except UserNotParticipant:
        raise UserNotFoundError(request.user_id)
    except PeerIdInvalid:
        raise HTTPException(status_code=400, detail="Invalid user ID.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))    

@app.post("/add_contact")
async def add_contact(request: AddContactRequest, credentials: HTTPAuthorizationCredentials = Depends(authenticate)):
    try:
        user = await pyro_client.add_contact(
            request.user_id,
            request.first_name, 
        )
        return {"user_id": user.id, "status": "success"}
    except UsernameNotOccupied:
        raise HTTPException(status_code=400, detail="Invalid username.")
    except PeerIdInvalid:
        raise HTTPException(status_code=400, detail="Invalid user ID.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@app.post("/promote_chat_member")
async def promote_chat_member(request: PromoteChatMemberRequest, credentials: HTTPAuthorizationCredentials = Depends(authenticate)):
    try:
        privileges = ChatPrivileges(
            can_manage_chat=request.can_manage_chat,
            can_delete_messages=request.can_delete_messages,
            can_manage_video_chats=request.can_manage_video_chats,
            can_restrict_members=request.can_restrict_members,
            can_promote_members=request.can_promote_members,
            can_change_info=request.can_change_info,
            can_post_messages=request.can_post_messages,
            can_edit_messages=request.can_edit_messages,
            can_invite_users=request.can_invite_users,
            can_pin_messages=request.can_pin_messages,
            is_anonymous=request.is_anonymous
        )

        success = await pyro_client.promote_chat_member(
            request.chat_id,
            request.user_id,
            privileges=privileges
        )

        return {"status": "success" if success else "failed"}
    except ChatAdminRequired:
        raise PermissionError("You need to be an admin to promote members.")
    except UserNotParticipant:
        raise UserNotFoundError(request.user_id)
    except PeerIdInvalid:
        raise GroupNotFoundError(request.chat_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    

@app.post("/get_chat_members")
async def get_chat_members(request: GetChatMembersRequest, credentials: HTTPAuthorizationCredentials = Depends(authenticate)):
    try:
        members = []

        # Map the string filter to the actual ChatMembersFilter enum
        filter_mapping = {
            "search": ChatMembersFilter.SEARCH,
            "administrators": ChatMembersFilter.ADMINISTRATORS,
            "restricted": ChatMembersFilter.RESTRICTED,
            "banned": ChatMembersFilter.BANNED,
            "bots": ChatMembersFilter.BOTS,
            "recent": ChatMembersFilter.RECENT
        }

        # Default to SEARCH filter if not provided or if it's an empty string
        chat_filter = filter_mapping.get(request.filter, ChatMembersFilter.SEARCH)

        async for member in pyro_client.get_chat_members(
            request.chat_id,
            limit=request.limit or 1000,
            filter=chat_filter
        ):
            member_dict = {
                "user_id": member.user.id,
                "user_name": member.user.username,
                "status": member.status,
                "is_bot": member.user.is_bot,
                "chat": member.chat.title if member.chat else None,
                "joined_date": member.joined_date.isoformat() if member.joined_date else None,
                "custom_title": member.custom_title,
                "until_date": member.until_date.isoformat() if member.until_date else None,
                "invited_by": member.invited_by.username if member.invited_by else None,
                "promoted_by": member.promoted_by.username if member.promoted_by else None,
                "restricted_by": member.restricted_by.username if member.restricted_by else None,
                "is_member": member.is_member,
                "can_be_edited": member.can_be_edited,
                "permissions": member.permissions.to_dict() if member.permissions else None,
                "privileges": {
                    "can_manage_chat": member.privileges.can_manage_chat,
                    "can_delete_messages": member.privileges.can_delete_messages,
                    "can_manage_video_chats": member.privileges.can_manage_video_chats,
                    "can_restrict_members": member.privileges.can_restrict_members,
                    "can_promote_members": member.privileges.can_promote_members,
                    "can_change_info": member.privileges.can_change_info,
                    "can_post_messages": member.privileges.can_post_messages,
                    "can_edit_messages": member.privileges.can_edit_messages,
                    "can_invite_users": member.privileges.can_invite_users,
                    "can_pin_messages": member.privileges.can_pin_messages,
                    "is_anonymous": member.privileges.is_anonymous
                } if member.privileges else None            }
            members.append(member_dict)

        return {"members": members}
    except ChatAdminRequired:
        raise HTTPException(status_code=403, detail="You need to be an admin to get the members list.")
    except UserNotParticipant:
        raise HTTPException(status_code=404, detail="The user is not a participant in the chat.")
    except PeerIdInvalid:
        raise HTTPException(status_code=400, detail="Invalid chat ID.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    


@app.post("/set_chat_photo")
async def set_chat_photo(chat_id: int = Form(...), file: UploadFile = File(...), credentials: HTTPAuthorizationCredentials = Depends(authenticate)):
    try:
        if file.file is None:
            raise HTTPException(status_code=400, detail="No file uploaded")

        if file.content_type.startswith('image'):
            file_content = await file.read()
            file_like_object = io.BytesIO(file_content)  

            # Directly pass the BytesIO object to Pyrogram
            await pyro_client.set_chat_photo(chat_id, photo=file_like_object) 
                
            # Cleanup
            file_like_object.close() 

        else:
            raise HTTPException(status_code=415, detail="Unsupported Media Type. Please upload an image or video file.")
        return {"status": "success"}
    except ChatAdminRequired:
        raise PermissionError("You need to be an admin to change the chat photo.")
    except PeerIdInvalid:
        raise GroupNotFoundError(chat_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    

@app.post("/get_dialogs")
async def get_dialogs(limit: int = Form(None), credentials: HTTPAuthorizationCredentials = Depends(authenticate)):
    try:
        dialogs = []
        async for dialog in pyro_client.get_dialogs(limit=limit):
            dialogs.append({
                "id": dialog.chat.id, 
                "title": dialog.chat.title if dialog.chat.title else dialog.chat.first_name,
                "type": dialog.chat.type.value,
                "username": dialog.chat.username if dialog.chat.username else None,
                "creator": dialog.chat.is_creator
            })
        return {"dialogs": dialogs}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")