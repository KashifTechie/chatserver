from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger(__name__)


@api_view(["POST"])
def webhook_receiver(request):
    logger.info("x enviroment header: %s", request.headers.get("x-enviroment"))
    if request.headers.get("x-enviroment") != "sit":
        logger.info("Received webhook payload: %s", request.data)
        # logger.info("payload: %s", request.data)
        logger.info("header %s", request.headers)
        logger.warning("Unauthorized webhook attempt with headers: %s", request.headers)
        return Response(
            {
            "success": True,
            "message": "Webhook received successfully",
            "received_data": request.data,
        },
        status=status.HTTP_200_OK,
    )

    return Response(
        {
            "success": True,
            "message": "Webhook received successfully",
            "received_data": request.data,
        },
        status=status.HTTP_200_OK,
    )