# Standard library imports
from datetime import timedelta

# Django imports
from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone

# Third-party imports
from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

# Local imports
from .models import CustomUser, EmailVerificationToken, PasswordResetToken
from .serializers import (
    UserSerializer, UserRegistrationSerializer, LoginSerializer,
    PasswordChangeSerializer, UserUpdateSerializer,
)
from .services import TokenBlacklistService


class RegisterAPIView(generics.CreateAPIView):
    """User registration API endpoint"""
    queryset = CustomUser.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        with transaction.atomic():
            user = serializer.save()
            user.is_active = True
            user.save()
            
            # User profile is automatically created by signal
            
            # Send verification email if needed
            if not user.is_verified:
                self.send_verification_email(user)
        
        return Response({
            'message': 'Registration successful! Please check your email to verify your account.',
            'user': UserSerializer(user).data
        }, status=status.HTTP_201_CREATED)
    
    def send_verification_email(self, user):
        """Send email verification"""
        try:
            # Check for existing unexpired tokens
            existing_tokens = EmailVerificationToken.objects.filter(
                user=user,
                used=False,
                expires_at__gt=timezone.now()
            )
            if existing_tokens.exists():
                # Use existing token instead of creating new one
                token = existing_tokens.first()
            else:
                token = EmailVerificationToken.objects.create(
                    user=user,
                    expires_at=timezone.now() + timedelta(hours=24)
                )
            
            verification_url = self.request.build_absolute_uri(
                f'/api/accounts/verify-email/{token.token}/'
            )
            
            subject = 'Verify your email address'
            message = f'Please click the following link to verify your email: {verification_url}'
            
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL or 'noreply@hotel.com',
                [user.email],
                fail_silently=False,  # Don't fail silently in production
            )
        except Exception as e:
            # Log email sending errors
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to send verification email to {user.email}: {e}")


@api_view(['POST'])
@permission_classes([AllowAny])
def login_api_view(request):
    """Login API endpoint"""
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    user = serializer.validated_data['user']
    
    # Check for account lockout due to failed attempts
    if user.failed_login_attempts >= 5:
        return Response({
            'error': 'Account temporarily locked due to too many failed login attempts. Please try again later or reset your password.'
        }, status=status.HTTP_423_LOCKED)
    
    # Update last login IP and reset failed attempts
    user.last_login_ip = get_client_ip(request)
    user.failed_login_attempts = 0
    user.save(update_fields=['last_login_ip', 'failed_login_attempts'])
    
    # Generate JWT tokens
    refresh = RefreshToken.for_user(user)
    
    return Response({
        'message': f'Welcome back, {user.get_short_name()}!',
        'tokens': {
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        },
        'user': UserSerializer(user).data
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_api_view(request):
    """Logout API endpoint with token blacklisting"""
    refresh_token = request.data.get("refresh")
    if not refresh_token:
        return Response({'error': 'Refresh token is required for logout'}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    # Get access token from Authorization header
    access_token = None
    auth_header = request.META.get('HTTP_AUTHORIZATION')
    if auth_header and auth_header.startswith('Bearer '):
        access_token = auth_header.split(' ')[1]
    
    try:
        # Use the service to blacklist tokens
        refresh_blacklisted, access_blacklisted = TokenBlacklistService.blacklist_token_pair(
            refresh_token_str=refresh_token,
            access_token_str=access_token,
            user=request.user,
            reason='logout'
        )
        
        if not refresh_blacklisted:
            return Response({'error': 'Invalid refresh token'}, 
                           status=status.HTTP_400_BAD_REQUEST)
        
        return Response({'message': 'Successfully logged out. Tokens have been blacklisted.'}, 
                       status=status.HTTP_200_OK)
                
    except Exception as e:
        return Response({'error': f'Logout failed: {str(e)}'}, 
                       status=status.HTTP_400_BAD_REQUEST)


class ProfileAPIView(generics.RetrieveAPIView):
    """User profile retrieval API endpoint"""
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        return self.request.user


class ProfileUpdateAPIView(generics.UpdateAPIView):
    """User profile update API endpoint"""
    serializer_class = UserUpdateSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        return self.request.user
    
    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        response.data = {'message': 'Profile updated successfully!', 'user': response.data}
        return response


class PasswordChangeAPIView(generics.GenericAPIView):
    """Password change API endpoint"""
    serializer_class = PasswordChangeSerializer
    permission_classes = [IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'message': 'Password changed successfully!'})


@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_request(request):
    """Password reset request API endpoint"""
    email = request.data.get('email')
    if not email:
        return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = CustomUser.objects.get(email=email)
        
        # Check for existing unexpired tokens to prevent spam
        existing_tokens = PasswordResetToken.objects.filter(
            user=user,
            used=False,
            expires_at__gt=timezone.now()
        )
        
        if existing_tokens.exists():
            # Rate limiting: Don't create new token if one exists within last 5 minutes
            recent_token = existing_tokens.filter(
                created_at__gt=timezone.now() - timedelta(minutes=5)
            ).first()
            if recent_token:
                return Response({
                    'message': 'If the email exists, a password reset link has been sent.'
                })
        
        # Create password reset token
        token = PasswordResetToken.objects.create(
            user=user,
            expires_at=timezone.now() + timedelta(hours=1)
        )
        
        # Send password reset email
        reset_url = request.build_absolute_uri(
            f'/api/accounts/password-reset-confirm/{token.token}/'
        )
        
        subject = 'Password Reset Request'
        message = f'Please click the following link to reset your password: {reset_url}'
        
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL or 'noreply@hotel.com',
                [user.email],
                fail_silently=False,
            )
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to send password reset email: {e}")
        
    except CustomUser.DoesNotExist:
        pass  # Don't reveal whether email exists
    
    return Response({'message': 'If the email exists, a password reset link has been sent.'})


@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_confirm(request, token):
    """Password reset confirmation API endpoint"""
    reset_token = get_object_or_404(
        PasswordResetToken, 
        token=token,
        used=False
    )
    
    if reset_token.is_expired():
        return Response({'error': 'Password reset link has expired.'}, status=status.HTTP_400_BAD_REQUEST)
    
    password = request.data.get('password')
    if not password:
        return Response({'error': 'Password is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Enhanced password validation
    from django.contrib.auth.password_validation import validate_password
    from django.core.exceptions import ValidationError as DjangoValidationError
    
    try:
        validate_password(password, user=reset_token.user)
    except DjangoValidationError as e:
        return Response({'error': e.messages}, status=status.HTTP_400_BAD_REQUEST)
    
    with transaction.atomic():
        user = reset_token.user
        user.set_password(password)
        user.failed_login_attempts = 0
        user.save(update_fields=['password', 'failed_login_attempts'])
        
        # Mark token as used
        reset_token.used = True
        reset_token.save(update_fields=['used'])
        
        # Invalidate all existing password reset tokens for this user
        PasswordResetToken.objects.filter(
            user=user,
            used=False
        ).update(used=True)
    
    return Response({'message': 'Password reset successfully!'})


@api_view(['GET'])
@permission_classes([AllowAny])
def verify_email(request, token):
    """Email verification API endpoint"""
    try:
        verification_token = EmailVerificationToken.objects.get(
            token=token,
            used=False
        )
        
        if verification_token.is_expired():
            return Response({'error': 'Verification link has expired.'}, status=status.HTTP_400_BAD_REQUEST)
        
        with transaction.atomic():
            user = verification_token.user
            user.is_verified = True
            user.save()
            
            verification_token.used = True
            verification_token.save()
        
        return Response({'message': 'Email verified successfully!'})
        
    except EmailVerificationToken.DoesNotExist:
        return Response({'error': 'Invalid verification link.'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_account(request):
    """Account deletion API endpoint"""
    user = request.user
    user.delete()
    return Response({'message': 'Your account has been deleted successfully.'})


def get_client_ip(request):
    """Get client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
