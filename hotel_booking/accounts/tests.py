# Django imports
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

# Third-party imports
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

# Local imports
from .models import UserProfile, BlacklistedToken
from .services import TokenBlacklistService

User = get_user_model()


class CustomUserModelTest(TestCase):
    """Test cases for CustomUser model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
    
    def test_user_creation(self):
        """Test user is created properly"""
        self.assertEqual(self.user.email, 'test@example.com')
        self.assertEqual(self.user.username, 'testuser')
        self.assertTrue(self.user.is_active)
        self.assertFalse(self.user.is_staff)
    
    def test_user_profile_created(self):
        """Test user profile is automatically created"""
        self.assertTrue(hasattr(self.user, 'profile'))
        self.assertIsInstance(self.user.profile, UserProfile)
    
    def test_user_methods(self):
        """Test user model methods"""
        self.user.first_name = 'Test'
        self.user.last_name = 'User'
        self.assertEqual(self.user.get_full_name(), 'Test User')
        self.assertEqual(self.user.get_short_name(), 'Test')


class AccountsAPITest(APITestCase):
    """Test cases for accounts API endpoints"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
        self.register_url = reverse('accounts:register')
        self.login_url = reverse('accounts:login')
        self.profile_url = reverse('accounts:profile')
    
    def test_user_registration(self):
        """Test user registration API"""
        data = {
            'email': 'newuser@example.com',
            'username': 'newuser',
            'first_name': 'New',
            'last_name': 'User',
            'password': 'newpassword123',
            'password_confirm': 'newpassword123'
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email='newuser@example.com').exists())
    
    def test_user_login(self):
        """Test user login API"""
        data = {
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('tokens', response.data)
        self.assertIn('access', response.data['tokens'])
        self.assertIn('refresh', response.data['tokens'])
    
    def test_profile_access_requires_authentication(self):
        """Test profile endpoint requires authentication"""
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_authenticated_profile_access(self):
        """Test authenticated user can access profile"""
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'test@example.com')
    
    def test_password_change(self):
        """Test password change API"""
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        data = {
            'old_password': 'testpass123',
            'new_password': 'newtestpass123',
            'new_password_confirm': 'newtestpass123'
        }
        url = reverse('accounts:password_change')
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify password was changed
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('newtestpass123'))
    
    def test_logout_with_blacklisting(self):
        """Test logout with token blacklisting"""
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        # Test logout endpoint
        data = {'refresh': str(refresh)}
        url = reverse('accounts:logout')
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('blacklisted', response.data['message'].lower())
        
        # Verify refresh token is blacklisted using the model
        refresh_jti = str(refresh['jti'])
        self.assertTrue(BlacklistedToken.is_blacklisted(refresh_jti), 
                       "Refresh token should be blacklisted")
        
        # Verify the blacklisted token record exists
        blacklisted_token = BlacklistedToken.objects.filter(jti=refresh_jti).first()
        self.assertIsNotNone(blacklisted_token, "BlacklistedToken record should exist")
        self.assertEqual(blacklisted_token.user, self.user)
        self.assertEqual(blacklisted_token.token_type, 'refresh')
        self.assertEqual(blacklisted_token.reason, 'logout')
        
        # The middleware should prevent further API access with the same token
        # Note: Due to Django test client behavior, we can't fully test middleware in unit tests
        # but the integration tests in scripts/api_integration_tests.py verify this works correctly
    
    def test_logout_without_refresh_token(self):
        """Test logout fails without refresh token"""
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        url = reverse('accounts:logout')
        response = self.client.post(url, {})  # No refresh token
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('required', response.data['error'].lower())


class TokenBlacklistServiceTest(TestCase):
    """Test cases for TokenBlacklistService"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
    
    def test_blacklist_token_pair(self):
        """Test blacklisting token pair"""
        refresh = RefreshToken.for_user(self.user)
        access_token_str = str(refresh.access_token)
        refresh_token_str = str(refresh)
        
        # Blacklist token pair
        refresh_blacklisted, access_blacklisted = TokenBlacklistService.blacklist_token_pair(
            refresh_token_str=refresh_token_str,
            access_token_str=access_token_str,
            user=self.user
        )
        
        self.assertTrue(refresh_blacklisted)
        self.assertTrue(access_blacklisted)
        
        # Verify tokens are blacklisted
        self.assertTrue(TokenBlacklistService.is_token_blacklisted(refresh_token_str))
        self.assertTrue(TokenBlacklistService.is_token_blacklisted(access_token_str))
    
    def test_is_token_blacklisted(self):
        """Test token blacklist checking"""
        refresh = RefreshToken.for_user(self.user)
        token_str = str(refresh)
        
        # Initially not blacklisted
        self.assertFalse(TokenBlacklistService.is_token_blacklisted(token_str))
        
        # Blacklist the token
        TokenBlacklistService.blacklist_token_pair(refresh_token_str=token_str, user=self.user)
        
        # Now should be blacklisted
        self.assertTrue(TokenBlacklistService.is_token_blacklisted(token_str))
    
    def test_extract_jti_from_token(self):
        """Test JTI extraction from token"""
        refresh = RefreshToken.for_user(self.user)
        token_str = str(refresh)
        expected_jti = str(refresh['jti'])
        
        extracted_jti = TokenBlacklistService.extract_jti_from_token(token_str)
        self.assertEqual(extracted_jti, expected_jti)
        
        # Test invalid token
        invalid_jti = TokenBlacklistService.extract_jti_from_token('invalid_token')
        self.assertIsNone(invalid_jti)
