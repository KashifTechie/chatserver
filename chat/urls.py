from django.urls import path
from .views import (
    ContactListView,
    ConversationListView,
    CreateConversationView,
    MessageListView,
    SendMessageView,
    MarkReadView,
    UserSearchView,
)

urlpatterns = [
    path('contacts/', ContactListView.as_view()),
    path('conversations/', ConversationListView.as_view()),
    path('conversations/create/', CreateConversationView.as_view()),
    path('conversations/direct/', CreateConversationView.as_view()),
    path('conversations/<uuid:conversation_id>/messages/', MessageListView.as_view()),
    path('conversations/<uuid:conversation_id>/messages/send/', SendMessageView.as_view()),
    path('conversations/<uuid:conversation_id>/read/', MarkReadView.as_view()),
    path('users/search', UserSearchView.as_view()),
    path('users/search/', UserSearchView.as_view()),

    path('api/contacts/', ContactListView.as_view()),
    path('api/conversations/', ConversationListView.as_view()),
    path('api/conversations/create/', CreateConversationView.as_view()),
    path('api/conversations/direct/', CreateConversationView.as_view()),
    path('api/conversations/<uuid:conversation_id>/messages/', MessageListView.as_view()),
    path('api/conversations/<uuid:conversation_id>/messages/send/', SendMessageView.as_view()),
    path('api/conversations/<uuid:conversation_id>/read/', MarkReadView.as_view()),
    path('api/users/search', UserSearchView.as_view()),
    path('api/users/search/', UserSearchView.as_view()),
]
