"""
Custom postprocessing hooks for drf-spectacular
"""


def postprocess_schema_enums(result, generator, request, public):
    """
    Postprocessing hook to ensure enums are properly defined
    """
    # Add any enum preprocessing if needed
    return result


def postprocess_optional_fields(result, generator, request, public):
    """
    Postprocessing hook to enhance optional field documentation
    """
    if 'components' in result and 'schemas' in result['components']:
        for schema_name, schema in result['components']['schemas'].items():
            if 'properties' in schema:
                required_fields = schema.get('required', [])
                
                # Add descriptions to indicate optional vs required status
                for field_name, field_schema in schema['properties'].items():
                    current_desc = field_schema.get('description', '')
                    
                    if field_name not in required_fields:
                        # This is an optional field
                        if not current_desc.startswith('(Optional)') and not current_desc.startswith('Optional'):
                            field_schema['description'] = f'(Optional) {current_desc}' if current_desc else '(Optional)'
                            
                        # Add nullable indicator if applicable
                        if field_schema.get('nullable', False):
                            if '(nullable)' not in field_schema['description']:
                                field_schema['description'] += ' (nullable)'
                                
                        # Add default value information
                        if 'default' in field_schema:
                            default_val = field_schema['default']
                            if default_val is None:
                                if '(defaults to null)' not in field_schema['description']:
                                    field_schema['description'] += ' (defaults to null)'
                            else:
                                default_text = f' (default: {default_val})'
                                if default_text not in field_schema['description']:
                                    field_schema['description'] += default_text
                    else:
                        # This is a required field
                        if not current_desc.startswith('(Required)'):
                            field_schema['description'] = f'(Required) {current_desc}' if current_desc else '(Required)'
                
                # Add summary information
                optional_count = len(schema['properties']) - len(required_fields)
                if optional_count > 0:
                    schema['x-optional-fields-count'] = optional_count
                    schema['x-required-fields-count'] = len(required_fields)
    
    return result


def postprocess_add_examples(result, generator, request, public):
    """
    Add examples to the schema for better documentation
    """
    if 'components' in result and 'schemas' in result['components']:
        # Add examples for common patterns
        examples = {
            'UUID': '123e4567-e89b-12d3-a456-426614174000',
            'Date': '2024-12-25',
            'DateTime': '2024-12-25T15:30:00Z',
            'Email': 'user@example.com',
            'Phone': '+1-555-123-4567',
            'URL': 'https://example.com',
        }
        
        for schema_name, schema in result['components']['schemas'].items():
            if 'properties' in schema:
                for field_name, field_schema in schema['properties'].items():
                    field_type = field_schema.get('type')
                    field_format = field_schema.get('format')
                    
                    # Add examples based on field type and format
                    if field_format == 'uuid' and 'example' not in field_schema:
                        field_schema['example'] = examples['UUID']
                    elif field_format == 'date' and 'example' not in field_schema:
                        field_schema['example'] = examples['Date']
                    elif field_format == 'date-time' and 'example' not in field_schema:
                        field_schema['example'] = examples['DateTime']
                    elif field_format == 'email' and 'example' not in field_schema:
                        field_schema['example'] = examples['Email']
                    elif field_format == 'uri' and 'example' not in field_schema:
                        field_schema['example'] = examples['URL']
                    elif 'phone' in field_name.lower() and 'example' not in field_schema:
                        field_schema['example'] = examples['Phone']
                    elif field_name.lower() in ['email', 'email_address'] and 'example' not in field_schema:
                        field_schema['example'] = examples['Email']
    
    return result


def postprocess_enhance_operation_descriptions(result, generator, request, public):
    """
    Enhance operation descriptions with parameter information
    """
    if 'paths' in result:
        for path, path_item in result['paths'].items():
            for method, operation in path_item.items():
                if method in ['get', 'post', 'put', 'patch', 'delete']:
                    # Add parameter summary to operation description
                    parameters = operation.get('parameters', [])
                    request_body = operation.get('requestBody')
                    
                    param_info = []
                    
                    # Count required vs optional parameters
                    if parameters:
                        required_params = [p for p in parameters if p.get('required', False)]
                        optional_params = [p for p in parameters if not p.get('required', False)]
                        
                        if required_params:
                            param_info.append(f"{len(required_params)} required parameter(s)")
                        if optional_params:
                            param_info.append(f"{len(optional_params)} optional parameter(s)")
                    
                    # Add request body info
                    if request_body:
                        if request_body.get('required', False):
                            param_info.append("Request body required")
                        else:
                            param_info.append("Request body optional")
                    
                    # Update operation description
                    if param_info:
                        current_desc = operation.get('description', '')
                        param_summary = f"Parameters: {', '.join(param_info)}"
                        
                        if current_desc:
                            operation['description'] = f"{current_desc}\n\n{param_summary}"
                        else:
                            operation['description'] = param_summary
    
    return result


# Combined postprocessing function
def postprocess_enhanced_schema(result, generator, request, public):
    """
    Combined postprocessing function that applies multiple enhancements
    """
    result = postprocess_schema_enums(result, generator, request, public)
    result = postprocess_optional_fields(result, generator, request, public)
    result = postprocess_add_examples(result, generator, request, public)
    result = postprocess_enhance_operation_descriptions(result, generator, request, public)
    return result
