from ..models import AccountUser

class AccountUserRepository:

    @staticmethod
    def create_user(email, password, first_name=None, last_name=None, registration_method=None, whatsapp_number=None):
        user = AccountUser.objects.create_user(
            username=email,  # Set username to email for uniqueness
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            registration_method=registration_method,
            whatsapp_number=whatsapp_number,
        )
        return user

    @staticmethod
    def get_user_by_email(email):
        try:
            return AccountUser.objects.get(email=email)
        except AccountUser.DoesNotExist:
            return None

    @staticmethod
    def get_user_by_id(user_id):
        try:
            return AccountUser.objects.get(id=user_id)
        except AccountUser.DoesNotExist:
            return None

    @staticmethod
    def delete_user(user_id):
        user = AccountUserRepository.get_user_by_id(user_id)
        if user:
            user.delete()
            return True
        return False
    
    @staticmethod
    def get_or_create(**kwargs):
        pass