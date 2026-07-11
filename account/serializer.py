from rest_framework import serializers
from drf_recaptcha.fields import ReCaptchaV2Field
from .repository.AccountUserRepo import AccountUserRepository
import logging
from .models import AccountUser

logger = logging.getLogger(__name__)

class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)

    def validate_email(self, value):
        if AccountUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email is already registered.")
        return value
    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match.")
        return data
    def create(self, validated_data):
        logger.info("Creating user with email: %s",validated_data['email'])
        account_repo = AccountUserRepository()
        return account_repo.create_user(
                email=validated_data['email'],
                password=validated_data['password'],
                first_name=validated_data.get('first_name', None),
                last_name=validated_data.get('last_name', None),
                registration_method=AccountUser.RegistrationMethod.Email,
                whatsapp_number=validated_data.get('whatsapp_number', None)

            )

class RecaptchaSerializer(serializers.Serializer):
    recaptcha = ReCaptchaV2Field()

    def validate(self, data):
        # The ReCaptchaField will automatically validate the reCAPTCHA response.
        recaptcha_response = data.get('recaptcha')
        if not recaptcha_response:
            raise serializers.ValidationError({"recaptcha": "reCAPTCHA response is missing."})
        logger.info(f"Received reCAPTCHA response: {recaptcha_response}")
        return data
    
class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.CharField()
    otp = serializers.CharField(max_length=10)