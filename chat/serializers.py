from rest_framework import serializers
from account.models import AccountUser
from .models import (
    Contact,
    Conversation,
    ConversationParticipant,
    Message,
    MessageAttachment,
)


# ===========================================================================
# REQUEST SERIALIZERS  (serializers.Serializer)
# ===========================================================================

class CreateConversationRequestSerializer(serializers.Serializer):
    """Validates the payload for POST /api/conversations/create/"""
    participant_id = serializers.IntegerField(
        required=False,
        help_text="ID of the user you want to start a conversation with.",
    )
    user = serializers.IntegerField(required=False, help_text="Alias for participant_id.")

    def validate(self, attrs):
        participant_id = attrs.get("participant_id") or attrs.get("user")
        if not participant_id:
            raise serializers.ValidationError({"participant_id": "This field is required."})
        attrs["participant_id"] = participant_id
        return attrs


class SendMessageRequestSerializer(serializers.Serializer):
    """Validates the payload for POST /api/conversations/<id>/messages/"""
    content = serializers.CharField(
        required=True,
        allow_blank=False,
        help_text="Text content of the message.",
    )
    type = serializers.ChoiceField(
        choices=["text", "image", "video", "file", "audio", "voice", "gif", "location", "contact", "sticker"],
        default="text",
        required=False,
    )
    reply_to = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text="UUID of the message being replied to (Message uses UUID PK).",
    )


class MarkReadRequestSerializer(serializers.Serializer):
    """Validates the payload for POST /api/conversations/<id>/read/
       Body is optional — no fields required.
    """
    pass


class UserSearchRequestSerializer(serializers.Serializer):
    """Validates query params for GET /users/search/"""
    q = serializers.CharField(
        required=True,
        min_length=1,
        help_text="Search keyword — matched against first_name and last_name.",
    )


class ContactCreateRequestSerializer(serializers.Serializer):
    contact_user_id = serializers.IntegerField(required=True)
    display_name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    nickname = serializers.CharField(max_length=255, required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)


# ===========================================================================
# RESPONSE SERIALIZERS  (serializers.ModelSerializer)
# ===========================================================================

class UserResponseSerializer(serializers.ModelSerializer):
    """Minimal user representation used inside conversation/message responses."""

    class Meta:
        model = AccountUser
        fields = ["id", "first_name", "last_name", "email"]
        read_only_fields = fields


class ContactResponseSerializer(serializers.ModelSerializer):
    contact_user = UserResponseSerializer(read_only=True)

    class Meta:
        model = Contact
        fields = [
            "id",
            "contact_user",
            "display_name",
            "nickname",
            "notes",
            "favorite",
            "archived",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class MessageAttachmentResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = MessageAttachment
        fields = ["id", "url", "filename", "mime_type", "size", "width", "height", "duration"]
        read_only_fields = fields


class MessageResponseSerializer(serializers.ModelSerializer):
    """Full message representation returned from the API."""
    sender = UserResponseSerializer(read_only=True)
    sent_at_formatted = serializers.SerializerMethodField()
    attachments = MessageAttachmentResponseSerializer(many=True, read_only=True)

    class Meta:
        model = Message
        fields = [
            "id",
            "conversation",
            "sender",
            "type",
            "content",
            "reply_to",
            "forward_from",
            "edited",
            "edited_at",
            "deleted_for_everyone",
            "sent_at",
            "sent_at_formatted",
            "attachments",
        ]
        read_only_fields = fields

    def get_sent_at_formatted(self, obj):
        return obj.sent_at.strftime("%I:%M %p") if obj.sent_at else None


class ConversationParticipantResponseSerializer(serializers.ModelSerializer):
    """Participant entry including user details and role inside a conversation."""
    user = UserResponseSerializer(read_only=True)

    class Meta:
        model = ConversationParticipant
        fields = ["id", "user", "role", "joined_at", "pinned", "muted_until"]
        read_only_fields = fields


class ConversationResponseSerializer(serializers.ModelSerializer):
    """Full conversation representation returned from the API."""
    participants = ConversationParticipantResponseSerializer(many=True, read_only=True)
    last_message = MessageResponseSerializer(read_only=True)
    unread_count = serializers.SerializerMethodField()
    created_by = UserResponseSerializer(read_only=True)

    class Meta:
        model = Conversation
        fields = [
            "id",
            "type",
            "name",
            "image",
            "description",
            "created_by",
            "participants",
            "last_message",
            "last_message_at",
            "unread_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_unread_count(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return 0
        # Count messages that were sent after the user's last-read message
        participant = obj.participants.filter(user=request.user).first()
        if not participant or not participant.last_read_message:
            return obj.messages.exclude(sender=request.user).count()
        return obj.messages.filter(
            sent_at__gt=participant.last_read_message.sent_at
        ).exclude(sender=request.user).count()
