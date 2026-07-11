from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .serializer import ( 
    CustomTokenObtainPairSerializer,
    RecaptchaSerializer
)
from rest_framework.response import Response
import logging

logger = logging.getLogger(__name__)    

class CustomTokenObtainPairView(TokenObtainPairView):

    serializer_class = CustomTokenObtainPairSerializer  

    def post(self, request, *args, **kwargs):
        try:
            recaptcha = request.data.get("recaptcha_token")
            logger.info("recaptcha_token received: %s", recaptcha)

            recaptcha_serializer = RecaptchaSerializer(data={"recaptcha_token": recaptcha})
            recaptcha_serializer.is_valid(raise_exception=True)
            response = super().post(request, *args, **kwargs)
            if response.status_code == 200:
                from django.contrib.auth import get_user_model

                user = get_user_model().objects.get(
                    email=request.data["email"]
                )

                response.data["user_id"] = user.id
                response.data["email"] = user.email

            return response
        except Exception as e:
            logger.error("CustomTokenObtainPairView: Error during authentication - %s", str(e))
            return Response(
                {
                    "message": "An error occurred during authentication. Please try again."
                    }, 
                    status=400
            )


class LogoutView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        try:
            refresh_token = request.data.get("refresh")
            if refresh_token:
                token = self.get_token(refresh_token)
                logger.info("LogoutView: Blacklisting token for user - %s", token.payload.get("user_id"))
                token.blacklist()
                return Response({"message": "Logout successful."}, status=200)
            else:
                return Response({"message": "Refresh token is required."}, status=400)
        except Exception as e:
            logger.error("LogoutView: Error during logout - %s", str(e))
            return Response(
                {
                    "message": "An error occurred during logout. Please try again."
                    }, 
                    status=400
            )