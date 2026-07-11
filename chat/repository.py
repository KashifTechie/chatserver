from .models import Message

class MessageRepository:
    @staticmethod
    def create_message(conversation,sender, text):
        return Message.objects.create(
                conversation=conversation,
                sender=sender,
                content=text
            )
    
    @staticmethod
    def get_all_messages():
        return Message.objects.all()
    
    @staticmethod
    def get_message_by_id(message_id):
        return Message.objects.get(id=message_id)
    
    @staticmethod
    def delete_message(message_id):
        message = Message.objects.get(id=message_id)
        message.delete()
        return True
    
