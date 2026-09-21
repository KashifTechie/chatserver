from taskmanagers.task.kafka.handler.k_producer import get_producer
from taskmanagers.task.RabbitMQ.publisher import RMQProducer
from django.conf import settings

class TaskManager:
    def __init__(self):
           
        if settings.TASK_SERVICE == "KAFKA":
            self.tool = get_producer()
        elif  settings.TASK_SERVICE == "RABBITMQ":
            self.tool = RMQProducer()
        

    def execute_task(self, task, *args, **kwargs):
        self.tool.execute_task(task, *args, **kwargs)