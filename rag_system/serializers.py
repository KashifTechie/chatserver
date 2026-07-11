from rest_framework import serializers
from rag_system.models import RagStore
from django.conf import settings 
from taskmanagers.task.Task_manager import TaskManager
from rag_system.tasks import store_rag_knowledge
import logging
logger = logging.getLogger(__name__)

class RequestRagStoreSerializer(serializers.Serializer):
    title = serializers.CharField()
    type = serializers.CharField()
    status = serializers.CharField()
    text_content = serializers.CharField(
        required=False,
        allow_null=True
    )
    file_content = serializers.FileField(
        required=False,
        allow_null=True
    )
    url_content = serializers.URLField(
        required=False,
        allow_null=True
    )

    def validate(self, attributes):

        data_sources = [
            bool(attributes.get("text_content", None)),
            bool(attributes.get("file_content", None)),
            bool(attributes.get("url_content", None))
        ]
        count = sum(data_sources)
        if count==0:
            raise serializers.ValidationError(
                "Any one of the data source must be given"
            )

        
        if count > 1:
            raise serializers.ValidationError(
                "Only one data source is allowed."
            )
            
        return attributes

    def create(self, validated_data):
        rag = RagStore.objects.create(**validated_data)

        logger.info("The rag is created")

        task_manager : TaskManager = settings.TASK_MANAGER
        task_manager.execute_task(
            store_rag_knowledge,
            str(rag.uuid)
        )
        return rag
    
    def update(self, instance, validated_data):
        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        instance.save()
        return instance
    

class ResponseRagStoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = RagStore
        fields = ["title", "type", "status"]