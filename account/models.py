from django.db import models
from django.contrib.auth.models import AbstractUser, PermissionsMixin
import logging
import requests
import tempfile
import hashlib
from django.core.files import File
from django.utils.crypto import get_random_string


logger = logging.getLogger(__name__)
class AccountUser(AbstractUser, PermissionsMixin):

        class RegistrationMethod(models.TextChoices):
                Email = "EMAIL", "Email"
                GOOGLE = "GOOGLE", "Google"
                GITHUB = "GITHUB", "GitHub"
                Facebook = "FACEBOOK", "Facebook"
                X = "X", "X"

        email = models.EmailField(unique=True)
        whatsapp_number = models.CharField(max_length=16, blank=True, null=True)
        registration_method = models.CharField(max_length=16, choices=RegistrationMethod.choices, default=RegistrationMethod.Email)
        avatar_url = models.FileField(upload_to='avatars/', blank=True, null=True)
        username = models.CharField(max_length=150, unique=True,blank=True, null=True)
        is_verified = models.BooleanField(default=False)

        USERNAME_FIELD = "email"
        REQUIRED_FIELDS = ["first_name", "last_name"]


        def __str__(self):
                return self.username
        def save(self, *args, **kwargs):
                is_new = self.pk is None

                if not self.username:
                    self.username = f"{self.first_name}{get_random_string(3, allowed_chars='1234567890')}"

                if is_new  and not self.avatar_url:
                        
                        email_hash = hashlib.md5(self.email.lower().encode('utf-8')).hexdigest()

                        gravatar_url = f"https://www.gravatar.com/avatar/{email_hash}?d=identicon&s=200"

                        response = requests.get(gravatar_url, stream=True, timeout=60)
                        if response.status_code == 200:
                            for block in response.iter_content(1024*8):
                                    if not block:
                                            break
                                    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                                            temp_file.write(block)
                                            self.avatar_url.save(
                                                   f"{self.username}_avatar.jpg", 
                                                   File(temp_file),
                                                   save=False 
                                                   )
                            logger.info("Updated Gravatar for user: %s", self.email)
                        else:
                            logger.error("Failed to update Gravatar for user: %s", self.email)

                super().save(*args, **kwargs)


