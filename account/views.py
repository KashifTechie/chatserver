from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializer import RecaptchaSerializer, VerifyOTPSerializer, RegisterSerializer
from taskmanagers.redis.redis_functions import set_register_otp, get_register_otp
from .utils import generate_otp
from .services.email_service import send_otp_email
from rest_framework.exceptions import ValidationError
from .models import AccountUser
from rest_framework_simplejwt.tokens import RefreshToken

import logging

logger = logging.getLogger(__name__)

class RegisterUserView(APIView):
    def post(self, request):
        try:
            email = request.data.get("email")
            if not email:
                return Response({"message": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)
      
            r_serializer = RegisterSerializer(data=request.data)
            r_serializer.is_valid(raise_exception=True)
            r_serializer.save()
        
            otp = generate_otp()
            set_register_otp(email, otp)
            send_otp_email(email, otp)
            
            return Response({"message": "Check your email for the OTP."}, status=status.HTTP_201_CREATED)
        except ValidationError as ve:
            logger.info(f"Validation error during registration: {str(ve)}")
            error = ve.detail
            error_message = "Validation error"
            if isinstance(error,list):
                error_message = error[0]
            elif isinstance(error,dict):
                error_message = list(error.values())[0][0]
            else:
                error_message = "Validation error"
            return Response({"message": error_message}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.info(f"Error during registration: {str(e)}")
            return Response({"message": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class VerifyOTPView(APIView):

    def post(self, request):
        try:
            logger.info(f"Received OTP verification request with data: {request.data}")
            serializer = VerifyOTPSerializer(data=request.data)
            if serializer.is_valid():
                # Process the valid OTP verification
                email = serializer.validated_data['email']
                otp = serializer.validated_data['otp']
                stored_otp = get_register_otp(email)
                logger.info(f"Retrieved stored OTP for {email}: {stored_otp}")
                if stored_otp is None:
                    return Response({"message": "OTP has expired or re-generate the OTP."}, status=status.HTTP_400_BAD_REQUEST)
                logger.info(f"Verifying OTP for {email}. Provided OTP: {otp}, Stored OTP: {stored_otp}")

                logger.info("Type of provided OTP: %s, Type of stored OTP: %s", type(otp), type(stored_otp))
                if otp == stored_otp:
                    logger.info("otps are being compared")
                    user = AccountUser.objects.filter(email=email).first()
                    if user:
                        user.is_verified = True
                        user.is_active = True
                        user.save(update_fields=['is_verified', 'is_active'])

                    # Auto login after registration.
                    refresh_token = RefreshToken.for_user(user)
                    access_token = refresh_token.access_token
                    return Response(
                            {
                                "message": "OTP verified successfully.",
                                "data": {
                                    "access_token": str(access_token),
                                    "refresh_token": str(refresh_token),
                                }
                            }, status=status.HTTP_200_OK)
                else:
                    logger.info(f"OTP verification failed for {email}. Provided OTP: {otp} does not match stored OTP.")
                    return Response({"message": "Invalid OTP."}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ResendOTPView(APIView):

    def post(self, request):
        try:
            email = request.data.get("email")
            if not email:
                return Response({"message": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)
            user = AccountUser.objects.filter(email=email).first()
            if not user:
                return Response({"message": "User with this email does not exist."}, status=status.HTTP_404_NOT_FOUND)
            otp = generate_otp()
            set_register_otp(email, otp)
            send_otp_email(email, otp)
            return Response({"message": "A new OTP has been sent to your email."}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)