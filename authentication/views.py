"""
Authentication views - organized by feature.

Provides endpoints for:
- User registration
- Login / Logout
- Token refresh
- Profile management
"""

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from .serializer import CustomTokenObtainPairSerializer
from .jwt_auth import CustomTokenObtainPairView as BaseLoginView
from django.contrib.auth.password_validation import validate_password
from rest_framework.exceptions import ValidationError
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class RegisterView(generics.CreateAPIView):
    """
    Register a new user account.
    
    POST /auth/register/
    {
        "email": "user@example.com",
        "password": "secure_password",
        "first_name": "John",
        "last_name": "Doe"
    }
    """
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    
    def create(self, request, *args, **kwargs):
        email = request.data.get('email')
        password = request.data.get('password')
        first_name = request.data.get('first_name', '')
        last_name = request.data.get('last_name', '')
        
        # Validation
        if not email or not password:
            return Response(
                {"error": "Email and password are required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if User.objects.filter(email=email).exists():
            return Response(
                {"error": "User with this email already exists."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            validate_password(password)
        except ValidationError as e:
            return Response(
                {"error": e.messages},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create user
        user = User.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )
        
        logger.info(f"User registered: {email}")
        
        return Response(
            {
                "message": "User registered successfully.",
                "user_id": str(user.id),
                "email": user.email
            },
            status=status.HTTP_201_CREATED
        )


class LoginView(BaseLoginView):
    """
    Login with email and password.
    
    POST /auth/login/
    {
        "email": "user@example.com",
        "password": "password",
        "recaptcha_token": "token"
    }
    
    Returns: access and refresh tokens
    """
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [AllowAny]


class LogoutView(generics.GenericAPIView):
    """
    Logout the current user by blacklisting the refresh token.
    
    POST /auth/logout/
    {
        "refresh": "refresh_token"
    }
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if not refresh_token:
                return Response(
                    {"error": "Refresh token is required."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            logger.info(f"User logged out: {request.user.id}")
            
            return Response(
                {"message": "Logout successful."},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Logout error: {str(e)}")
            return Response(
                {"error": "Error during logout."},
                status=status.HTTP_400_BAD_REQUEST
            )


class RefreshTokenView(TokenRefreshView):
    """
    Refresh the access token using the refresh token.
    
    POST /auth/refresh/
    {
        "refresh": "refresh_token"
    }
    
    Returns: new access token
    """
    permission_classes = [AllowAny]


class CurrentUserView(generics.RetrieveAPIView):
    """
    Get the current authenticated user's profile.
    
    GET /auth/me/
    
    Returns: user profile data
    """
    permission_classes = [IsAuthenticated]
    serializer_class = None  # Define in your serializer module
    
    def get_object(self):
        return self.request.user
    
    def get(self, request, *args, **kwargs):
        user = request.user
        return Response({
            "id": str(user.id),
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "username": user.username,
            "is_verified": getattr(user, 'is_verified', False),
            "avatar_url": str(user.avatar_url.url) if user.avatar_url else None,
        })


class ProfileUpdateView(generics.UpdateAPIView):
    """
    Update the current user's profile.
    
    PATCH /auth/profile/
    {
        "first_name": "Jane",
        "last_name": "Smith",
        "whatsapp_number": "+1234567890",
        "username": "janesmith"
    }
    
    Returns: updated user profile
    """
    permission_classes = [IsAuthenticated]
    serializer_class = None  # Define in your serializer module
    
    def get_object(self):
        return self.request.user
    
    def partial_update(self, request, *args, **kwargs):
        user = request.user
        
        # Update allowed fields
        if 'first_name' in request.data:
            user.first_name = request.data['first_name']
        if 'last_name' in request.data:
            user.last_name = request.data['last_name']
        if 'whatsapp_number' in request.data:
            user.whatsapp_number = request.data['whatsapp_number']
        if 'username' in request.data:
            # Check uniqueness
            if User.objects.filter(username=request.data['username']).exclude(id=user.id).exists():
                return Response(
                    {"error": "Username already taken."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            user.username = request.data['username']
        if 'avatar_url' in request.FILES:
            user.avatar_url = request.FILES['avatar_url']
        
        user.save()
        logger.info(f"User profile updated: {user.email}")
        
        return Response({
            "id": str(user.id),
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "username": user.username,
            "whatsapp_number": user.whatsapp_number,
            "is_verified": getattr(user, 'is_verified', False),
            "avatar_url": str(user.avatar_url.url) if user.avatar_url else None,
            "message": "Profile updated successfully."
        })
