"""
Custom Spectacular extensions for better API documentation
"""
from drf_spectacular.extensions import OpenApiSerializerExtension
from drf_spectacular.utils import extend_schema_field
from drf_spectacular.openapi import AutoSchema
from drf_spectacular.generators import SchemaGenerator
from rest_framework import serializers
from rest_framework.fields import Field
import re


class OptionalFieldSerializerExtension(OpenApiSerializerExtension):
    """
    Extension to better handle optional fields in serializers
    """
    target_component = 'core.serializers'
    match_subclasses = True

    def map_serializer(self, auto_schema, direction):
        """
        Override serializer mapping to better handle optional fields
        """
        schema = auto_schema._map_serializer(self.target, direction, bypass_extensions=True)
        
        # Add descriptions for optional fields
        if 'properties' in schema and hasattr(self.target, 'fields'):
            for field_name, field_schema in schema['properties'].items():
                field = self.target.fields.get(field_name)
                if field:
                    # Check if field is optional
                    is_optional = (
                        not field.required or
                        field.allow_null or
                        getattr(field, 'allow_blank', False) or
                        field.default != serializers.empty
                    )
                    
                    if is_optional:
                        # Add optional indicator to description
                        current_desc = field_schema.get('description', '')
                        if current_desc and not current_desc.startswith('(Optional)'):
                            field_schema['description'] = f'(Optional) {current_desc}'
                        elif not current_desc:
                            field_schema['description'] = '(Optional)'
                        
                        # Add nullable property if applicable
                        if field.allow_null:
                            field_schema['nullable'] = True
                            
                        # Add default value if present
                        if field.default != serializers.empty and field.default is not None:
                            field_schema['default'] = field.default
                            
                        # Add format information for specific field types
                        if isinstance(field, serializers.CharField) and getattr(field, 'allow_blank', False):
                            if 'description' in field_schema:
                                field_schema['description'] += ' (Can be empty string)'
        
        return schema


class EnhancedSchemaGenerator(SchemaGenerator):
    """
    Enhanced Schema Generator to better handle optional fields and provide more detailed documentation
    """
    
    def get_schema(self, request=None, public=False):
        """Override to provide enhanced schema generation"""
        schema = super().get_schema(request, public)
        
        # Additional enhancements can be added here
        if 'components' in schema and 'schemas' in schema['components']:
            for schema_name, schema_def in schema['components']['schemas'].items():
                if 'properties' in schema_def:
                    self._enhance_schema_properties(schema_def)
        
        return schema
    
    def _enhance_schema_properties(self, schema_def):
        """Enhance schema properties with better documentation"""
        required_fields = schema_def.get('required', [])
        
        for field_name, field_schema in schema_def['properties'].items():
            # Add field status information
            if field_name not in required_fields:
                current_desc = field_schema.get('description', '')
                if not any(marker in current_desc for marker in ['(Optional)', 'Optional']):
                    field_schema['description'] = f'(Optional) {current_desc}' if current_desc else '(Optional)'
            else:
                current_desc = field_schema.get('description', '')
                if not any(marker in current_desc for marker in ['(Required)', 'Required']):
                    field_schema['description'] = f'(Required) {current_desc}' if current_desc else '(Required)'


def enhance_field_documentation(field, schema):
    """
    Helper function to enhance field documentation with detailed information
    """
    descriptions = []
    
    # Field type information
    if isinstance(field, serializers.CharField):
        if hasattr(field, 'max_length') and field.max_length:
            descriptions.append(f'Maximum length: {field.max_length}')
        if hasattr(field, 'min_length') and field.min_length:
            descriptions.append(f'Minimum length: {field.min_length}')
            
    elif isinstance(field, serializers.IntegerField):
        if hasattr(field, 'max_value') and field.max_value is not None:
            descriptions.append(f'Maximum value: {field.max_value}')
        if hasattr(field, 'min_value') and field.min_value is not None:
            descriptions.append(f'Minimum value: {field.min_value}')
            
    elif isinstance(field, serializers.DecimalField):
        descriptions.append(f'Decimal places: {field.decimal_places}')
        descriptions.append(f'Max digits: {field.max_digits}')
        
    elif isinstance(field, serializers.DateField):
        descriptions.append('Format: YYYY-MM-DD')
        
    elif isinstance(field, serializers.DateTimeField):
        descriptions.append('Format: YYYY-MM-DDTHH:MM:SS')
        
    elif isinstance(field, serializers.EmailField):
        descriptions.append('Must be a valid email address')
        
    elif isinstance(field, serializers.URLField):
        descriptions.append('Must be a valid URL')
        
    elif isinstance(field, serializers.UUIDField):
        descriptions.append('Must be a valid UUID')
        
    # Add choice information
    if hasattr(field, 'choices') and field.choices:
        choice_desc = 'Choices: ' + ', '.join([f'"{choice[0]}"' for choice in field.choices])
        descriptions.append(choice_desc)
    
    # Combine descriptions
    if descriptions:
        additional_info = '. '.join(descriptions)
        current_desc = schema.get('description', '')
        if current_desc:
            schema['description'] = f'{current_desc}. {additional_info}'
        else:
            schema['description'] = additional_info
    
    return schema
