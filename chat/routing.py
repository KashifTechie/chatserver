from django.urls import re_path
# from chat.consumers import SingleChatConsumer , GroupChatConsumer
from chat.consumers import ChatConsumer

# websocket_urlpatterns = [
#     re_path(r"ws/single/$", SingleChatConsumer.as_asgi()),
#     re_path(r"ws/group/(?P<room_name>\w+)/$", GroupChatConsumer.as_asgi()),
# ]
websocket_urlpatterns = [
    re_path(r"ws/chat/(?P<conversation_id>[0-9a-f-]+)/$", ChatConsumer.as_asgi())
]
