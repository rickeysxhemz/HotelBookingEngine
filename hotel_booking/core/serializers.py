from rest_framework import serializers
from .models import ContactMessage


class ContactMessageSerializer(serializers.ModelSerializer):
    """Serializer for ContactMessage model"""

    class Meta:
        model = ContactMessage
        fields = [
            'id',
            'full_name',
            'email',
            'phone',
            'subject',
            'message',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def create(self, validated_data):
        """Create a new contact message"""
        return ContactMessage.objects.create(**validated_data)
