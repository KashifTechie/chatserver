import logging
from ..models import Conversation, Message
from account.models import AccountUser
from chat.consumers import EventDTO, notify_socket

logger = logging.getLogger(__name__)
def process_message_job(conversation_id, sender_id, message):
    from chat.repository import MessageRepository
    logger.info("The request is recieved to process the message")
    try:
        conversation = Conversation.objects.get(id=conversation_id)
        sender = AccountUser.objects.get(id=sender_id)
        # msg = Message.objects.create(
        #     conversation=conversation,
        #     sender=sender,
        #     text=text
        # )

        message = MessageRepository.create_message(conversation, sender, message)

        data = EventDTO(
                id = str(message.id),   
                sender_id = str(sender.id),
                text = message.content,
                time = message.sent_at.strftime("%I:%M %p")
            )
        
        notify_socket(data, conversation_id)
        # Simulate processing (e.g., logging the message text)
        logger.info("The message is created")
    except Exception as e:
        logger.info(f"Failed to process message: {str(e)}")
    
