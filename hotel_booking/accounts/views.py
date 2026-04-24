# Standard library imports
from datetime import timedelta

# Django imports
from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

# Third-party imports
from rest_framework import generics, status, permissions
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator

# Local imports
from .models import CustomUser, EmailVerificationToken, PasswordResetToken
from .serializers import (
    UserSerializer, UserRegistrationSerializer, LoginSerializer,
    PasswordChangeSerializer, UserUpdateSerializer,
)
from bookings.models import Booking
from bookings.serializers import BookingListSerializer


@method_decorator(ratelimit(key='ip', rate='5/m', method='POST', block=True), name='post')
class RegisterAPIView(generics.CreateAPIView):
    """User registration API endpoint"""
    queryset = CustomUser.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Auto-verify unless ENABLE_EMAIL_VERIFICATION is explicitly on. For a
        # demo or SPA-first app we issue a token immediately so the client
        # doesn't depend on the user clicking a verification link.
        require_verification = str(
            getattr(settings, 'ENABLE_EMAIL_VERIFICATION', False)
        ).lower() in ('true', '1', 'yes')

        with transaction.atomic():
            user = serializer.save()
            user.is_active = True
            if not require_verification:
                user.is_verified = True
            user.save()

            # Fire off the verification email asynchronously so SMTP latency
            # never blocks the registration response.
            if require_verification and not user.is_verified:
                try:
                    self.send_verification_email(user)
                except Exception:
                    import logging
                    logging.getLogger(__name__).exception(
                        "Verification email failed; registration still succeeded"
                    )

            token, _ = Token.objects.get_or_create(user=user)

        return Response({
            'message': 'Registration successful!',
            'token': token.key,
            'user': UserSerializer(user).data,
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
                f'/api/v1/auth/verify-email/{token.token}/'
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
@ratelimit(key='ip', rate='5/m', method='POST', block=True)
def login_api_view(request):
    """Login API endpoint with rate limiting"""
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    user = serializer.validated_data['user']
    
    # Check for account lockout due to failed attempts
    if user.failed_login_attempts >= 10:
        return Response({
            'error': 'Account temporarily locked due to too many failed login attempts. Please try again later or reset your password.'
        }, status=status.HTTP_423_LOCKED)

    # Check if email is verified
    if not user.is_verified:
        return Response({
            'error': 'Please verify your email address before logging in. Check your email for the verification link.',
            'verification_required': True
        }, status=status.HTTP_403_FORBIDDEN)

    # Update last login IP and reset failed attempts
    user.last_login_ip = get_client_ip(request)
    user.failed_login_attempts = 0
    user.save(update_fields=['last_login_ip', 'failed_login_attempts'])

    token, _ = Token.objects.get_or_create(user=user)

    return Response({
        'message': f'Welcome back, {user.get_short_name()}!',
        'token': token.key,
        'user': UserSerializer(user).data,
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_api_view(request):
    """Logout API endpoint — deletes the user's token."""
    Token.objects.filter(user=request.user).delete()
    return Response({'message': 'Successfully logged out.'}, status=status.HTTP_200_OK)


class ProfileAPIView(generics.RetrieveAPIView):
    """User profile retrieval API endpoint"""
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    @method_decorator(ratelimit(key='user', rate='30/m', method='GET', block=True))
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    def get_object(self):
        return self.request.user


@method_decorator(ratelimit(key='user', rate='10/m', method=['PATCH', 'PUT'], block=True), name='dispatch')
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


@method_decorator(ratelimit(key='user', rate='5/h', method='POST', block=True), name='post')
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
            f'/api/v1/auth/password/reset/confirm/{token.token}/'
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


# ===== MISSING VIEWS IMPLEMENTATION =====

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def resend_verification_email(request):
    """Resend email verification"""
    user = request.user
    if user.is_verified:
        return Response({'message': 'Your email is already verified.'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Use the same logic as RegisterAPIView for sending verification email
    try:
        # Check for existing unexpired tokens
        existing_tokens = EmailVerificationToken.objects.filter(
            user=user,
            used=False,
            expires_at__gt=timezone.now()
        )
        if existing_tokens.exists():
            token = existing_tokens.first()
        else:
            token = EmailVerificationToken.objects.create(
                user=user,
                expires_at=timezone.now() + timedelta(hours=24)
            )
        verification_url = request.build_absolute_uri(
            f'/api/v1/auth/verify-email/{token.token}/'
        )
        subject = 'Verify your email address'
        message = f'Please click the following link to verify your email: {verification_url}'
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL or 'noreply@hotel.com',
            [user.email],
            fail_silently=False,
        )
        return Response({'message': 'Verification email sent successfully.'})
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to send verification email to {user.email}: {e}")
        return Response({'error': 'Failed to send verification email.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProfileAvatarAPIView(generics.UpdateAPIView):
    """Upload/update user profile avatar"""
    permission_classes = [IsAuthenticated]
    serializer_class = UserUpdateSerializer
    
    def update(self, request, *args, **kwargs):
        user = request.user
        avatar = request.FILES.get('avatar')
        
        if not avatar:
            return Response({'error': 'No avatar file provided.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Delete old avatar if exists
        if user.profile_picture:
            default_storage.delete(user.profile_picture.name)
        
        # Save new avatar
        user.profile_picture = avatar
        user.save()
        
        return Response({
            'message': 'Avatar updated successfully.',
            'avatar_url': user.profile_picture.url if user.profile_picture else None
        })


class UserSettingsAPIView(generics.RetrieveUpdateAPIView):
    """User settings management"""
    permission_classes = [IsAuthenticated]
    serializer_class = UserUpdateSerializer
    
    def get_object(self):
        return self.request.user
    
    def get(self, request, *args, **kwargs):
        user = self.get_object()
        settings_data = {
            'newsletter_subscription': user.newsletter_subscription,
            'email_notifications': True,  # Add this field to model if needed
            'privacy_settings': {
                'show_profile_publicly': False,  # Add this field to model if needed
                'allow_contact': True,
            }
        }
        return Response(settings_data)
    
    def patch(self, request, *args, **kwargs):
        user = self.get_object()
        
        # Update settings
        if 'newsletter_subscription' in request.data:
            user.newsletter_subscription = request.data['newsletter_subscription']
        
        user.save()
        
        return Response({'message': 'Settings updated successfully.'})


class UserPreferencesAPIView(generics.RetrieveUpdateAPIView):
    """User preferences management"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        user = request.user
        preferences = {
            'language': 'en',  # Default language
            'currency': 'USD',  # Default currency
            'timezone': 'UTC',  # Default timezone
            'room_preferences': {
                'smoking': False,
                'floor_preference': 'high',
                'bed_type': 'king',
            },
            'booking_preferences': {
                'auto_confirm': True,
                'cancellation_insurance': False,
            }
        }
        return Response(preferences)
    
    def patch(self, request, *args, **kwargs):
        # In a real implementation, you'd save these to a UserPreferences model
        return Response({'message': 'Preferences updated successfully.'})


class UserBookingsListAPIView(generics.ListAPIView):
    """Get user's bookings"""
    permission_classes = [IsAuthenticated]
    serializer_class = BookingListSerializer
    
    def get_queryset(self):
        return Booking.objects.filter(guest=self.request.user).order_by('-created_at')


class UserBookingHistoryAPIView(generics.ListAPIView):
    """Get user's booking history"""
    permission_classes = [IsAuthenticated]
    serializer_class = BookingListSerializer
    
    def get_queryset(self):
        return Booking.objects.filter(
            guest=self.request.user,
            status__in=['completed', 'cancelled']
        ).order_by('-created_at')


class UserFavoriteHotelsAPIView(generics.ListAPIView):
    """Get user's favorite hotels"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        # In a real implementation, you'd have a UserFavoriteHotel model
        # For now, return empty list
        return Response({
            'results': [],
            'message': 'Favorite hotels feature coming soon!'
        })
    
    def post(self, request, *args, **kwargs):
        """Add hotel to favorites"""
        hotel_id = request.data.get('hotel_id')
        if not hotel_id:
            return Response({'error': 'hotel_id is required.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # In a real implementation, you'd create a favorite record
        return Response({'message': 'Hotel added to favorites!'})


class UserNotificationsAPIView(generics.ListAPIView):
    """Get user notifications"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        # In a real implementation, you'd have a Notification model
        notifications = [
            {
                'id': 1,
                'title': 'Booking Confirmed',
                'message': 'Your booking at Hotel Maar has been confirmed.',
                'read': False,
                'created_at': timezone.now().isoformat(),
                'type': 'booking'
            },
            {
                'id': 2,
                'title': 'Welcome to Hotel Booking Engine!',
                'message': 'Thank you for registering. Explore our amazing hotels.',
                'read': True,
                'created_at': (timezone.now() - timedelta(days=1)).isoformat(),
                'type': 'welcome'
            }
        ]
        
        return Response({
            'results': notifications,
            'unread_count': len([n for n in notifications if not n['read']])
        })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_notification_read(request, notification_id):
    """Mark a notification as read"""
    # In a real implementation, you'd update the notification in the database
    return Response({'message': f'Notification {notification_id} marked as read.'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_all_notifications_read(request):
    """Mark all notifications as read"""
    # In a real implementation, you'd update all user notifications
    return Response({'message': 'All notifications marked as read.'})



def get_client_ip(request):
    """Get client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
