from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
import requests
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):

    username_field = 'email'

    def validate(self, attrs):

        logger.info("CustomTokenObtainPairSerializer: Starting validation for email: %s", attrs.get(self.username_field))
        try:

            data = super().validate(attrs)
            logger.info("CustomTokenObtainPairSerializer: Validation successful for email: %s", attrs.get(self.username_field))
            return data
        except AuthenticationFailed as e:
            logger.warning("CustomTokenObtainPairSerializer: Authentication failed for email: %s - %s", attrs.get(self.username_field), str(e))
            raise AuthenticationFailed(
                {
                    "message":
                    "No active account found with the given credentials."
                }
            )
        except Exception as e:
            logger.error("CustomTokenObtainPairSerializer: Unexpected error during validation for email: %s - %s", attrs.get(self.username_field), str(e))
            raise AuthenticationFailed(
                {
                    "message":
                    "An unexpected error occurred during authentication."
                }
            )
        
class RecaptchaSerializer(serializers.Serializer):
    recaptcha_token = serializers.CharField(required=True, write_only=True) 

    def validate(self, attrs):
        try:
            recaptcha_token = attrs.get('recaptcha_token')
            recaptcha_url = settings.DRF_RECAPTCHA_VERIFY_ENDPOINT
            recaptcha_Secrete = settings.DRF_RECAPTCHA_SECRET_KEY
            response = requests.post(
                recaptcha_url,
                data={
                    "secret" : recaptcha_Secrete,
                    "response" : recaptcha_token
                },
                timeout=10
            )

            result = response.json()
            logger.info("RecaptchaSerializer: reCAPTCHA validation response - %s", result)
            if not result.get("success", False):
                raise serializers.ValidationError("Invalid reCAPTCHA. Please try again.")
            return attrs
        except requests.RequestException as e:
            logger.error("RecaptchaSerializer: Error validating reCAPTCHA - %s", str(e))
            raise serializers.ValidationError("Error validating reCAPTCHA. Please try again later.")