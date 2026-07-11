from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.response import Response
# from .langchain.huggingface import huggingface_pipeline
# from .langchain.open_ai import chatgetllm


class HuggingFaceAi(APIView):
    def post(self, request):
        # Temporarily disabled - transformers/torch compatibility issue
        return Response(
            {"error": "HuggingFace AI temporarily disabled due to dependency issues"},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )