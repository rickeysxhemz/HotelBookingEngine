from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import CustomUser, UserProfile


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile"""
    
    class Meta:
        model = UserProfile
        fields = [
            'emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_relationship',
            'preferred_room_type', 'dietary_restrictions', 'accessibility_needs', 'special_requests',
            'total_bookings', 'total_spent', 'created_at', 'updated_at'
        ]
        read_only_fields = ['total_bookings', 'total_spent', 'created_at', 'updated_at']


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user model"""
    profile = UserProfileSerializer(read_only=True)
    full_name = serializers.SerializerMethodField()
    age = serializers.SerializerMethodField()
    
    class Meta:
        model = CustomUser
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name', 'full_name',
            'phone_number', 'date_of_birth', 'age', 'gender', 'user_type',
            'address_line_1', 'address_line_2', 'city', 'state', 'postal_code', 'country',
            'newsletter_subscription', 'profile_picture', 'bio',
            'is_active', 'is_verified', 'date_joined', 'last_updated', 'profile'
        ]
        read_only_fields = [
            'id', 'full_name', 'age', 'is_active', 'is_verified', 
            'date_joined', 'last_updated', 'profile'
        ]
        extra_kwargs = {
            'password': {'write_only': True}
        }
    
    def get_full_name(self, obj):
        return obj.get_full_name()
    
    def get_age(self, obj):
        return obj.age()


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = CustomUser
        fields = [
            'email', 'username', 'first_name', 'last_name', 'phone_number',
            'password', 'password_confirm'
        ]
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = CustomUser.objects.create_user(password=password, **validated_data)
        return user


class LoginSerializer(serializers.Serializer):
    """Serializer for user login"""
    email = serializers.EmailField()
    password = serializers.CharField()
    
    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            try:
                user = CustomUser.objects.get(email=email)
                
                # Check if account is locked
                if user.failed_login_attempts >= 5:
                    raise serializers.ValidationError('Account temporarily locked due to too many failed attempts')
                
                # Authenticate user
                authenticated_user = authenticate(username=email, password=password)
                if not authenticated_user:
                    # Increment failed login attempts
                    user.failed_login_attempts += 1
                    user.save(update_fields=['failed_login_attempts'])
                    raise serializers.ValidationError('Invalid credentials')
                
                if not authenticated_user.is_active:
                    raise serializers.ValidationError('User account is disabled')
                    
                attrs['user'] = authenticated_user
                
            except CustomUser.DoesNotExist:
                # Don't reveal that email doesn't exist
                raise serializers.ValidationError('Invalid credentials')
        else:
            raise serializers.ValidationError('Must include email and password')
        
        return attrs


class PasswordChangeSerializer(serializers.Serializer):
    """Serializer for password change"""
    old_password = serializers.CharField()
    new_password = serializers.CharField(min_length=8)
    new_password_confirm = serializers.CharField()
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("New passwords don't match")
        return attrs
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Old password is incorrect')
        return value
    
    def save(self):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile"""
    profile = UserProfileSerializer(required=False)
    
    class Meta:
        model = CustomUser
        fields = [
            'first_name', 'last_name', 'phone_number', 'date_of_birth', 'gender',
            'address_line_1', 'address_line_2', 'city', 'state', 'postal_code', 'country',
            'newsletter_subscription', 'profile_picture', 'bio', 'profile'
        ]
    
    def update(self, instance, validated_data):
        profile_data = validated_data.pop('profile', {})
        
        # Update user fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update profile fields
        if profile_data:
            profile = instance.profile
            for attr, value in profile_data.items():
                setattr(profile, attr, value)
            profile.save()
        
        return instance
