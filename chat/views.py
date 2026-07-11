import logging

from django.contrib.auth import get_user_model
from django.db import models, transaction
from django.db.models import Q

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from .models import Contact, Conversation, ConversationParticipant, Message
from .serializers import (
    # Request serializers
    CreateConversationRequestSerializer,
    SendMessageRequestSerializer,
    MarkReadRequestSerializer,
    UserSearchRequestSerializer,
    ContactCreateRequestSerializer,
    # Response serializers
    ContactResponseSerializer,
    ConversationResponseSerializer,
    MessageResponseSerializer,
    UserResponseSerializer,
)

logger = logging.getLogger(__name__)
User = get_user_model()


class ContactListView(APIView):
    """
    GET /api/v1/contacts/
    POST /api/v1/contacts/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        contacts = Contact.objects.filter(owner=request.user, archived=False).select_related("contact_user")
        search = request.query_params.get("search")
        if search:
            contacts = contacts.filter(
                Q(display_name__icontains=search)
                | Q(nickname__icontains=search)
                | Q(contact_user__first_name__icontains=search)
                | Q(contact_user__last_name__icontains=search)
                | Q(contact_user__email__icontains=search)
            )
        serializer = ContactResponseSerializer(contacts.order_by("-favorite", "display_name"), many=True)
        return Response({"message": "Contacts fetched successfully.", "data": serializer.data}, status=status.HTTP_200_OK)

    def post(self, request):
        request_serializer = ContactCreateRequestSerializer(data=request.data)
        if not request_serializer.is_valid():
            return Response(
                {"message": "Validation error.", "errors": request_serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        contact_user_id = request_serializer.validated_data["contact_user_id"]
        if str(contact_user_id) == str(request.user.id):
            return Response({"message": "Cannot add yourself as a contact."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            contact_user = User.objects.get(id=contact_user_id)
        except User.DoesNotExist:
            return Response({"message": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        display_name = request_serializer.validated_data.get("display_name") or (
            contact_user.get_full_name() or contact_user.email
        )
        contact, created = Contact.objects.get_or_create(
            owner=request.user,
            contact_user=contact_user,
            defaults={
                "display_name": display_name,
                "nickname": request_serializer.validated_data.get("nickname", ""),
                "notes": request_serializer.validated_data.get("notes", ""),
            },
        )
        if not created:
            return Response({"message": "Contact already exists.", "data": ContactResponseSerializer(contact).data}, status=status.HTTP_200_OK)

        return Response(
            {"message": "Contact created successfully.", "data": ContactResponseSerializer(contact).data},
            status=status.HTTP_201_CREATED,
        )


# ===========================================================================
# Conversation APIs
# ===========================================================================

class ConversationListView(APIView):
    """
    GET /api/v1/chat/api/conversations/
    Returns all conversations the authenticated user is part of.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        conversations = (
            Conversation.objects.filter(
                participants__user=request.user
            )
            .prefetch_related("participants__user", "last_message__sender")
            .order_by("-last_message_at", "-created_at")
            .distinct()
        )
        serializer = ConversationResponseSerializer(
            conversations,
            many=True,
            context={"request": request},
        )
        return Response(
            {"message": "Conversations fetched successfully.", "data": serializer.data},
            status=status.HTTP_200_OK,
        )


class CreateConversationView(APIView):
    """
    POST /api/v1/chat/api/conversations/create/
    Creates a new direct conversation between the authenticated user and another user.
    Returns the existing conversation if one already exists.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # --- Validate request ---
        request_serializer = CreateConversationRequestSerializer(data=request.data)
        if not request_serializer.is_valid():
            return Response(
                {"message": "Validation error.", "errors": request_serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        participant_id = request_serializer.validated_data["participant_id"]

        if str(participant_id) == str(request.user.id):
            return Response(
                {"message": "Cannot start a conversation with yourself."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            other_user = User.objects.get(id=participant_id)
        except User.DoesNotExist:
            return Response(
                {"message": "User not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # --- Check for existing conversation + create inside one atomic block ---
        with transaction.atomic():
            existing = (
                Conversation.objects.filter(
                    type=Conversation.ConversationType.DIRECT,
                    participants__user=request.user,
                )
                .filter(participants__user=other_user)
                .annotate(participant_count=models.Count("participants"))
                .filter(participant_count=2)
                # .select_for_update()
                .first()
            )

            if existing:
                serializer = ConversationResponseSerializer(
                    existing, context={"request": request}
                )
                return Response(
                    {"message": "Conversation already exists.", "data": serializer.data},
                    status=status.HTTP_200_OK,
                )

            # Create new conversation
            conversation = Conversation.objects.create(
                type=Conversation.ConversationType.DIRECT,
                created_by=request.user,
            )
            ConversationParticipant.objects.create(
                conversation=conversation,
                user=request.user,
                role=ConversationParticipant.ParticipantRole.MEMBER,
            )
            ConversationParticipant.objects.create(
                conversation=conversation,
                user=other_user,
                role=ConversationParticipant.ParticipantRole.MEMBER,
            )

        serializer = ConversationResponseSerializer(
            conversation, context={"request": request}
        )
        return Response(
            {"message": "Conversation created successfully.", "data": serializer.data},
            status=status.HTTP_201_CREATED,
        )


# ===========================================================================
# Message APIs
# ===========================================================================

class MessageListView(APIView):
    """
    GET /api/v1/chat/api/conversations/<conversation_id>/messages/
    Returns paginated messages for a conversation.
    Supports cursor-based pagination via ?cursor=<sent_at>&page_size=<n>.
    """
    permission_classes = [IsAuthenticated]
    PAGE_SIZE = 40

    def get(self, request, conversation_id):
        # Verify conversation exists and user is a participant
        try:
            conversation = Conversation.objects.get(
                id=conversation_id,
                participants__user=request.user,
            )
        except Conversation.DoesNotExist:
            return Response(
                {"message": "Conversation not found or access denied."},
                status=status.HTTP_404_NOT_FOUND,
            )

        page_size = int(request.query_params.get("page_size", self.PAGE_SIZE))
        cursor = request.query_params.get("cursor")  # ISO timestamp of last seen message

        qs = Message.objects.filter(conversation=conversation).select_related(
            "sender", "reply_to"
        ).prefetch_related("attachments")

        if cursor:
            qs = qs.filter(sent_at__lt=cursor)

        messages = qs.order_by("-sent_at")[:page_size]
        messages = list(reversed(messages))  # restore chronological order

        serializer = MessageResponseSerializer(
            messages,
            many=True,
            context={"request": request},
        )

        next_cursor = messages[0].sent_at.isoformat() if len(messages) == page_size else None

        return Response(
            {
                "message": "Messages fetched successfully.",
                "next_cursor": next_cursor,
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )


class SendMessageView(APIView):
    """
    POST /api/v1/chat/api/conversations/<conversation_id>/messages/
    Sends a new message in a conversation.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, conversation_id):
        # --- Validate request ---
        request_serializer = SendMessageRequestSerializer(data=request.data)
        if not request_serializer.is_valid():
            return Response(
                {"message": "Validation error.", "errors": request_serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Verify conversation and membership
        try:
            conversation = Conversation.objects.get(
                id=conversation_id,
                participants__user=request.user,
            )
        except Conversation.DoesNotExist:
            return Response(
                {"message": "Conversation not found or access denied."},
                status=status.HTTP_404_NOT_FOUND,
            )

        data = request_serializer.validated_data
        reply_to = None

        if data.get("reply_to"):
            try:
                reply_to = Message.objects.get(
                    id=data["reply_to"], conversation=conversation
                )
            except Message.DoesNotExist:
                return Response(
                    {"message": "Reply-to message not found in this conversation."},
                    status=status.HTTP_404_NOT_FOUND,
                )

        # Create the message
        msg = Message.objects.create(
            conversation=conversation,
            sender=request.user,
            type=data.get("type", "text"),
            content=data["content"],
            reply_to=reply_to,
        )

        # Update conversation's last_message pointer
        conversation.last_message = msg
        conversation.last_message_at = msg.sent_at
        conversation.save(update_fields=["last_message", "last_message_at"])

        response_serializer = MessageResponseSerializer(msg, context={"request": request})
        return Response(
            {"message": "Message sent successfully.", "data": response_serializer.data},
            status=status.HTTP_201_CREATED,
        )


class MarkReadView(APIView):
    """
    POST /api/v1/chat/api/conversations/<conversation_id>/read/
    Marks all unread messages in the conversation as read for the requesting user.
    Updates the participant's last_read_message pointer.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, conversation_id):
        # Request body is intentionally empty — validate anyway for consistency
        request_serializer = MarkReadRequestSerializer(data=request.data)
        if not request_serializer.is_valid():
            return Response(
                {"message": "Validation error.", "errors": request_serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            participant = ConversationParticipant.objects.select_related(
                "conversation"
            ).get(
                conversation_id=conversation_id,
                user=request.user,
            )
        except ConversationParticipant.DoesNotExist:
            return Response(
                {"message": "Conversation not found or access denied."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Find the latest message not sent by the requesting user
        last_msg = (
            Message.objects.filter(conversation_id=conversation_id)
            .exclude(sender=request.user)
            .order_by("-sent_at")
            .first()
        )

        if last_msg:
            participant.last_read_message = last_msg
            participant.save(update_fields=["last_read_message"])

        return Response(
            {"message": "Conversation marked as read.", "last_read_message_id": str(last_msg.id) if last_msg else None},
            status=status.HTTP_200_OK,
        )


# ===========================================================================
# User Search API
# ===========================================================================

class UserSearchView(APIView):
    """
    GET /api/v1/chat/users/search/?q=<keyword>
    Searches users by first_name or last_name. Excludes the requesting user.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Validate query params
        request_serializer = UserSearchRequestSerializer(data=request.query_params)
        if not request_serializer.is_valid():
            return Response(
                {"message": "Validation error.", "errors": request_serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        q = request_serializer.validated_data["q"].strip()
        logger.info("UserSearchView: Searching for keyword='%s'", q)

        from django.db.models import Q
        users = (
            User.objects.filter(
                Q(first_name__icontains=q) | Q(last_name__icontains=q)
            )
            .exclude(id=request.user.id)[:20]
        )

        response_serializer = UserResponseSerializer(users, many=True)
        return Response(
            {"message": "Users fetched successfully.", "data": response_serializer.data},
            status=status.HTTP_200_OK,
        )
