"""
Custom permissions for the offers app
"""
from rest_framework import permissions


class IsAdminOrManagerPermission(permissions.BasePermission):
    """
    Custom permission to only allow admin users and managers to create, update, or delete offers.
    Regular users can only read offers.
    """
    
    def has_permission(self, request, view):
        # Read permissions are allowed for any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Check if user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Allow if user is superuser
        if request.user.is_superuser:
            return True
        
        # Allow if user is admin
        if hasattr(request.user, 'user_type') and request.user.user_type == 'admin':
            return True
        
        # Allow if user is staff (manager) with staff permissions
        if (hasattr(request.user, 'user_type') and 
            request.user.user_type == 'staff' and 
            request.user.is_staff):
            return True
        
        return False
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed for any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Check if user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Allow if user is superuser
        if request.user.is_superuser:
            return True
        
        # Allow if user is admin
        if hasattr(request.user, 'user_type') and request.user.user_type == 'admin':
            return True
        
        # Allow if user is staff (manager) with staff permissions
        if (hasattr(request.user, 'user_type') and 
            request.user.user_type == 'staff' and 
            request.user.is_staff):
            return True
        
        return False


class IsAdminOrManagerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow admin users and managers to create, update, or delete.
    All users can read.
    """
    
    def has_permission(self, request, view):
        # Read permissions are allowed for any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Check if user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Allow if user is superuser
        if request.user.is_superuser:
            return True
        
        # Allow if user is admin
        if hasattr(request.user, 'user_type') and request.user.user_type == 'admin':
            return True
        
        # Allow if user is staff (manager) with staff permissions
        if (hasattr(request.user, 'user_type') and 
            request.user.user_type == 'staff' and 
            request.user.is_staff):
            return True
        
        return False
