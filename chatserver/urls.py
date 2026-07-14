"""
URL configuration for chatserver project.

The URL structure is organized by FEATURE/DOMAIN rather than by model,
providing an intuitive and scalable API structure.

API v1 routes all feature-based endpoints:
- /api/v1/auth/                  - Authentication
- /api/v1/contacts/              - Contact management
- /api/v1/contact-requests/      - Contact request workflow
- /api/v1/blocks/                - User blocking
- /api/v1/conversations/         - Conversations & groups
- /api/v1/messages/              - Messaging
- /api/v1/attachments/           - File uploads
- /api/v1/reactions/             - Message reactions
- /api/v1/read-receipts/         - Read receipts
- /api/v1/search/                - Universal search
- /api/v1/users/                 - User management
"""

from django.contrib import admin
from django.urls import path, include
from .view import webhook_receiver

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    path('api/v1/users',include("account.urls")),
    path('api/v1/authentication',include("authentication.urls")),
    path('api/v1/', include("chat.urls")),
    path('api/v1/chat/',include("chat.urls")),
    path('api/v1/rag',include("rag_system.urls")),
    
    # Webhooks
    path('api/webhook', webhook_receiver),
]
