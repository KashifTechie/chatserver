# from channels.generic.websocket import WebsocketConsumer
# from asgiref.sync import AsyncToSync
# import json
import logging

logger = logging.getLogger(__name__)
# class SingleChatConsumer(WebsocketConsumer):

#     def connect(self):
#         self.accept()
#         self.send(
#             text_data=json.dumps(
#                 {"message": "connacted successfully"}
#             )
#         )
#     def receive(self, text_data=None, bytes_data=None):
#         # 🔐 Safety check
#         if not text_data:
#             print("Empty message received — ignoring")
#             return

#         try:
#             data = json.loads(text_data)
#         except json.JSONDecodeError:
#             print("Invalid JSON received:", text_data)
#             self.send(text_data=json.dumps({
#                 "error": "Invalid JSON format"
#             }))
#             return

#         message = data.get("message")
#         print("Received:", message)

#         self.send(text_data=json.dumps({
#             "message": message
#         }))



# class GroupChatConsumer(WebsocketConsumer):

#     def connect(self):
#         self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
#         self.room_group_name = f"chat_{self.room_name}"
#         logger.info("the group name is %s",self.room_group_name)

#         AsyncToSync(self.channel_layer.group_add)(
#             self.room_group_name,
#             self.channel_name
#         )

#         self.accept()

#     def receive(self, text_data):
#         data = json.loads(text_data)
#         message = data["message"]
#         logger.info("received %s", message)

#         print(f"received : {message}")

#         AsyncToSync(self.channel_layer.group_send)(
#             self.room_group_name,
#             {
#                 "type": "chat.message",
#                 "message": message,
#             }
#         )

#     def chat_message(self, event):
#         self.send(
#             text_data=json.dumps(
#                 {"message": event["message"]}
#             )
#         )

#     def disconnect(self, close_code):

#         print("websocked is disconnected")
#         AsyncToSync(self.channel_layer.group_discard)(
#             self.room_group_name,
#             self.channel_name
#         )
# from channels.layers import get_channel_layer
# def notify(data):

#     channel_layer = get_channel_layer()
#     room_group_name  = 'chat_test'
#     AsyncToSync(channel_layer.group_send)(
#         room_group_name,
#         {
#             "type": "chat.message",
#             "message": data,
#         }
#     )

#     return "the socket is notified"
from dataclasses import dataclass, asdict

@dataclass
class EventDTO:
    id : str
    sender_id : str
    text : str
    time : str

    def to_json(self):
        return asdict(self)




import uuid
import json
from channels.generic.websocket import WebsocketConsumer, AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from asgiref.sync import AsyncToSync
from .models import Conversation, Message
from taskmanagers.task.Task_manager import TaskManager
from django.conf import settings
from .tasks import process_message
from asgiref.sync import sync_to_async
from channels.layers import get_channel_layer


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        self.conv_id = self.scope["url_route"]["kwargs"]["conversation_id"]
        self.group = f"chat_{self.conv_id}"

        print("USER:", self.user)
        print("USER ID:", self.user.id)
        print("CONV ID:", self.conv_id)

        allowed = await database_sync_to_async(
                    lambda: Conversation.objects.filter(
                        id=self.conv_id,
                        created_by=self.user.id
                    ).exists()
                )()
        print("ALLOWED:", allowed)
        print("ACCEPTING SOCKET")
        if not allowed:
            await self.close()
            return


        await self.channel_layer.group_add(self.group, self.channel_name)
        await self.accept()

         # Mark user online in Redis
        await self.channel_layer.group_add(f"presence_{self.user.id}", self.channel_name)
        await self._broadcast_presence(online=True)

    # async def receive(self, text_data):
    #     data = json.loads(text_data)
    #     text = data.get("content", "").strip()
    #     if not text:
    #         return

    #     task_manager : TaskManager = settings.TASK_MANAGER
    #     logger.info("The task is being initiated")
    #     await sync_to_async(task_manager.execute_task)(
    #         process_message,
    #         conversation_id=self.conv_id,
    #         sender_id=self.user.id,
    #         message=text
    #     )

       
    async def chat_message(self, event):
        # Called by channel layer when worker pushes to this group
        await self.send(text_data=json.dumps({
            "type": "chat_message",
            "message": event["message"]
        }))

    async def disconnect(self, close_code):

        logger.info("The websocket is disconnected")
        await self.channel_layer.group_discard(self.group, self.channel_name)
        await self._broadcast_presence(online=False)

    async def _broadcast_presence(self, online: bool):
        logger.info("broad casting the messages to the user")
        await self.channel_layer.group_send(
            f"conv_presence_{self.conv_id}",
            {"type": "presence_update", "user_id": self.user.id, "online": online}
        )
    
    async def presence_update(self, event):
        await self.send(text_data=json.dumps({
            "type": "presence",
            "user_id": event["user_id"],
            "online": event["online"]
        }))

    
def notify_socket(event: EventDTO, conversation_id):
    from asgiref.sync import async_to_sync
    logger.info("The client is being notififed")
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"chat_{conversation_id}",
        {"type": "chat_message", "message": event.to_json()}
    )

