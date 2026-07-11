from chat.tasks import process_message
from rag_system.tasks import store_rag_knowledge

CONSUMER_GROUP_MAPPINGS = {
    "message": {
        "process_message": process_message,
    },
    "rag": {
        "store_rag_knowledge":store_rag_knowledge
    },
    "group3": {
        "payment.received": "handle_payment_received",
        "payment.failed": "handle_payment_failed",
        "refund.processed": "handle_refund_processed",
    },
    "group_all": {
        "user.created": "handle_user_created",
        "order.placed": "handle_order_placed",
        "payment.received": "handle_payment_received",
    }
}