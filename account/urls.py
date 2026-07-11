from django.urls import path
from .views import RegisterUserView, ResendOTPView, VerifyOTPView
from .user_ino_api import search_users
urlpatterns = [
    path("/register", RegisterUserView.as_view(), name="register"),
    path("/verify-otp", VerifyOTPView.as_view(), name="verify-otp"),
    path("/resend-otp", ResendOTPView.as_view(), name="resend-otp"),
    path("/users/search", search_users),
]
