import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Contact(BaseModel):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="contacts")
    contact_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="contact_of")
    display_name = models.CharField(max_length=255)
    nickname = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)
    favorite = models.BooleanField(default=False)
    archived = models.BooleanField(default=False)

    class Meta:
        ordering = ["display_name"]
        constraints = [
            models.UniqueConstraint(fields=["owner", "contact_user"], name="unique_contact"),
        ]
        indexes = [
            models.Index(fields=["owner"]),
            models.Index(fields=["contact_user"]),
        ]

    def __str__(self):
        return f"{self.owner} -> {self.display_name}"


class ContactRequest(BaseModel):
    class ContactRequestStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        ACCEPTED = "accepted", "Accepted"
        DECLINED = "declined", "Declined"
        CANCELLED = "cancelled", "Cancelled"
        EXPIRED = "expired", "Expired"

    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sent_contact_requests")
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="received_contact_requests")
    first_message = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=ContactRequestStatus.choices, default=ContactRequestStatus.PENDING)
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["sender", "receiver"], name="unique_contact_request"),
        ]
        indexes = [
            models.Index(fields=["receiver", "status"]),
            models.Index(fields=["sender"]),
        ]

    def accept(self):
        self.status = ContactRequest.ContactRequestStatus.ACCEPTED
        self.responded_at = timezone.now()
        self.save(update_fields=["status", "responded_at"])

    def decline(self):
        self.status = ContactRequest.ContactRequestStatus.DECLINED
        self.responded_at = timezone.now()
        self.save(update_fields=["status", "responded_at"])

    def __str__(self):
        return f"{self.sender} -> {self.receiver}"


class UserBlock(BaseModel):
    blocker = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="blocked_users")
    blocked = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="blocked_by_users")
    reason = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["blocker", "blocked"], name="unique_user_block"),
        ]
        indexes = [
            models.Index(fields=["blocker"]),
            models.Index(fields=["blocked"]),
        ]

    def __str__(self):
        return f"{self.blocker} blocked {self.blocked}"


class Conversation(BaseModel):
    class ConversationType(models.TextChoices):
        DIRECT = "direct", "Direct"
        GROUP = "group", "Group"
        CHANNEL = "channel", "Channel"

    type = models.CharField(max_length=20, choices=ConversationType.choices, default=ConversationType.DIRECT)
    name = models.CharField(max_length=255, blank=True)
    image = models.TextField(blank=True)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_conversations",
    )
    last_message = models.ForeignKey("Message", on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    last_message_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-last_message_at", "-created_at"]
        indexes = [
            models.Index(fields=["type"]),
            models.Index(fields=["last_message_at"]),
        ]

    def __str__(self):
        if self.type == Conversation.ConversationType.DIRECT:
            return f"Direct Chat ({self.pk})"
        return self.name or f"{self.get_type_display()} ({self.pk})"


class ConversationParticipant(BaseModel):
    class ParticipantRole(models.TextChoices):
        OWNER = "owner", "Owner"
        ADMIN = "admin", "Admin"
        MEMBER = "member", "Member"

    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="participants")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="conversation_participants")
    role = models.CharField(max_length=20, choices=ParticipantRole.choices, default=ParticipantRole.MEMBER)
    joined_at = models.DateTimeField(auto_now_add=True)
    left_at = models.DateTimeField(null=True, blank=True)
    last_read_message = models.ForeignKey("Message", on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    muted_until = models.DateTimeField(null=True, blank=True)
    pinned = models.BooleanField(default=False)

    class Meta:
        ordering = ["joined_at"]
        constraints = [
            models.UniqueConstraint(fields=["conversation", "user"], name="unique_conversation_participant"),
        ]
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["conversation"]),
            models.Index(fields=["role"]),
        ]

    def __str__(self):
        return f"{self.user} ({self.conversation})"


class ConversationSettings(BaseModel):
    participant = models.OneToOneField(ConversationParticipant, on_delete=models.CASCADE, related_name="settings")
    notifications = models.BooleanField(default=True)
    disappearing_messages = models.BooleanField(default=False)
    wallpaper = models.CharField(max_length=500, blank=True)
    custom_name = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name = "Conversation Settings"
        verbose_name_plural = "Conversation Settings"

    def __str__(self):
        return f"Settings - {self.participant}"


class MessageType(models.TextChoices):
    TEXT = "text", "Text"
    IMAGE = "image", "Image"
    VIDEO = "video", "Video"
    FILE = "file", "File"
    AUDIO = "audio", "Audio"
    VOICE = "voice", "Voice"
    GIF = "gif", "GIF"
    LOCATION = "location", "Location"
    CONTACT = "contact", "Contact"
    STICKER = "sticker", "Sticker"
    SYSTEM = "system", "System"


class Message(BaseModel):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="sent_messages")
    reply_to = models.ForeignKey("self", on_delete=models.SET_NULL, null=True, blank=True, related_name="replies")
    forward_from = models.ForeignKey("self", on_delete=models.SET_NULL, null=True, blank=True, related_name="forwarded_messages")
    type = models.CharField(max_length=20, choices=MessageType.choices, default=MessageType.TEXT)
    content = models.TextField(blank=True)
    edited = models.BooleanField(default=False)
    edited_at = models.DateTimeField(null=True, blank=True)
    deleted_for_everyone = models.BooleanField(default=False)
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["sent_at"]
        indexes = [
            models.Index(fields=["conversation", "-sent_at"]),
            models.Index(fields=["sender"]),
            models.Index(fields=["type"]),
        ]

    @property
    def text(self):
        return self.content

    @property
    def created_at_formatted(self):
        return self.sent_at

    @property
    def has_attachment(self):
        return self.attachments.exists()

    def __str__(self):
        return f"{self.sender} - {self.get_type_display()}"


class MessageAttachment(BaseModel):
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name="attachments")
    url = models.TextField()
    filename = models.CharField(max_length=255)
    mime_type = models.CharField(max_length=100)
    size = models.BigIntegerField()
    width = models.IntegerField(null=True, blank=True)
    height = models.IntegerField(null=True, blank=True)
    duration = models.IntegerField(null=True, blank=True, help_text="Duration in seconds")

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return self.filename


class MessageReaction(BaseModel):
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name="reactions")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="message_reactions")
    emoji = models.CharField(max_length=20)
    reacted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["message", "user"], name="unique_message_reaction"),
        ]
        indexes = [
            models.Index(fields=["message"]),
            models.Index(fields=["user"]),
        ]

    def __str__(self):
        return f"{self.user} reacted {self.emoji}"


class ReadReceipt(BaseModel):
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name="read_receipts")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="read_receipts")
    delivered_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["message", "user"], name="unique_read_receipt"),
        ]
        indexes = [
            models.Index(fields=["user", "message"]),
        ]

    def __str__(self):
        return f"{self.user} - {self.message_id}"


class MessageDelete(BaseModel):
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name="deleted_for_users")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="deleted_messages")
    deleted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["message", "user"], name="unique_deleted_message"),
        ]
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["message"]),
        ]

    def __str__(self):
        return f"{self.user} deleted {self.message_id}"
