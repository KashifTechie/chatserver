from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError
from rag_system.serializers import RequestRagStoreSerializer, ResponseRagStoreSerializer
from rag_system.models import RagStore
import logging

logger = logging.getLogger(__name__)

class RagStoringAPIView(APIView):

    def put(self, request):
        try:

            logger.info("The payload: \n%s", request.data)

            type = request.data.get("type")
            # source = request.data.get("source")
            title = request.data.get("title")
            text_content = request.data.get("text_content", None)
            file_content = request.data.get("file_content", None)
            url_content = request.data.get("url_content", None)

            payload = {
                "title":title,
                "type":type,
                "status":RagStore.StatusChoices.PENDING,
            }

            if text_content:
                payload.update(
                    {
                        "text_content":text_content
                    }
                )
            if file_content:
                payload.update(
                    {
                        "file_content":file_content
                    }
                )
            if url_content:
                payload.update(
                    {
                        "url_content":url_content
                    }
                )

            serializer = RequestRagStoreSerializer(
                data=payload
            )

            serializer.is_valid(raise_exception=True)
            created = serializer.save()
            serialized = ResponseRagStoreSerializer(created).data

            return Response(
                {
                    "message": "The rag storage is initiated successfully.",
                    "data": serialized
                }
            )

        except ValidationError as e:
            errors = e.detail
            message = None
            if isinstance(errors, dict):
                key = next(iter(errors))
                message = errors[key][0]
            elif isinstance(errors, list):
                message = errors[0]
            elif isinstance(errors, str):
                message = errors
            else:
                message = errors 
            return Response(
               { "message": e.detail},
                status=status.HTTP_400_BAD_REQUEST
            )  
            
        except Exception as e:
            logger.info("an error occured: %s", str(e))
            return Response(
                {"message": "an unknown error occured"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        