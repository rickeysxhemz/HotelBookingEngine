# Django imports
from django.utils import timezone

# Third-party imports
from rest_framework_simplejwt.tokens import RefreshToken, UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

# Local imports
from .models import BlacklistedToken


class TokenBlacklistService:
    """Service class for managing JWT token blacklisting"""
    
    @staticmethod
    def blacklist_token_pair(refresh_token_str, access_token_str=None, user=None, reason='logout'):
        """
        Blacklist both refresh and access tokens
        
        Args:
            refresh_token_str: The refresh token string
            access_token_str: The access token string (optional)
            user: The user object (optional)
            reason: Reason for blacklisting (default: 'logout')
            
        Returns:
            tuple: (refresh_blacklisted, access_blacklisted) - booleans indicating success
        """
        refresh_blacklisted = False
        access_blacklisted = False
        
        # Blacklist refresh token
        try:
            refresh_token = RefreshToken(refresh_token_str)
            refresh_jti = str(refresh_token['jti'])
            _, refresh_blacklisted = BlacklistedToken.blacklist_token(
                jti=refresh_jti,
                user=user,
                token_type='refresh',
                reason=reason
            )
        except (InvalidToken, TokenError):
            pass
        
        # Blacklist access token if provided
        if access_token_str:
            try:
                access_token = UntypedToken(access_token_str)
                access_jti = str(access_token['jti'])
                _, access_blacklisted = BlacklistedToken.blacklist_token(
                    jti=access_jti,
                    user=user,
                    token_type='access',
                    reason=reason
                )
            except (InvalidToken, TokenError):
                pass
        
        return refresh_blacklisted, access_blacklisted
    
    @staticmethod
    def is_token_blacklisted(token_str):
        """
        Check if a token is blacklisted
        
        Args:
            token_str: The token string to check
            
        Returns:
            bool: True if blacklisted, False otherwise
        """
        try:
            token = UntypedToken(token_str)
            jti = str(token['jti'])
            return BlacklistedToken.is_blacklisted(jti)
        except (InvalidToken, TokenError):
            return False
    
    @staticmethod
    def extract_jti_from_token(token_str):
        """
        Extract JTI from a token string
        
        Args:
            token_str: The token string
            
        Returns:
            str or None: The JTI if valid, None otherwise
        """
        try:
            token = UntypedToken(token_str)
            return str(token['jti'])
        except (InvalidToken, TokenError):
            return None
    
    @staticmethod
    def cleanup_expired_tokens(days_old=30):
        """
        Clean up old blacklisted tokens
        
        Args:
            days_old: Remove tokens older than this many days
            
        Returns:
            int: Number of tokens deleted
        """
        cutoff_date = timezone.now() - timezone.timedelta(days=days_old)
        deleted_count, _ = BlacklistedToken.objects.filter(
            blacklisted_at__lt=cutoff_date
        ).delete()
        return deleted_count
