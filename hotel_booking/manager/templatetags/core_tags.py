from django import template
from django.forms import (
    CheckboxInput, Textarea, Select, DateInput, 
    FileInput, ClearableFileInput, URLInput, EmailInput,
    NumberInput
)

register = template.Library()

@register.filter
def is_checkbox(field):
    """Returns True if the field is a checkbox."""
    return isinstance(field.field.widget, CheckboxInput)

@register.filter
def is_textarea(field):
    """Returns True if the field is a textarea."""
    return isinstance(field.field.widget, Textarea)

@register.filter
def is_select(field):
    """Returns True if the field is a select dropdown."""
    return isinstance(field.field.widget, Select)

@register.filter
def is_date(field):
    """Returns True if the field is a date input."""
    return isinstance(field.field.widget, DateInput)

@register.filter
def is_file(field):
    """Returns True if the field is a file upload."""
    return isinstance(field.field.widget, (FileInput, ClearableFileInput))

@register.filter
def is_url(field):
    """Returns True if the field is a URL input."""
    return isinstance(field.field.widget, URLInput)

@register.filter
def is_email(field):
    """Returns True if the field is an email input."""
    return isinstance(field.field.widget, EmailInput)

@register.filter
def is_number(field):
    """Returns True if the field is a number input."""
    return isinstance(field.field.widget, NumberInput)

@register.filter
def field_type(field):
    """Returns the field type as a string."""
    widget = field.field.widget
    if isinstance(widget, CheckboxInput):
        return 'checkbox'
    elif isinstance(widget, Textarea):
        return 'textarea'
    elif isinstance(widget, Select):
        return 'select'
    elif isinstance(widget, DateInput):
        return 'date'
    elif isinstance(widget, (FileInput, ClearableFileInput)):
        return 'file'
    elif isinstance(widget, URLInput):
        return 'url'
    elif isinstance(widget, EmailInput):
        return 'email'
    elif isinstance(widget, NumberInput):
        return 'number'
    else:
        return 'text'

@register.filter
def attr(obj, attr_name):
    """A simple filter to access an object's attribute by name."""
    return getattr(obj, attr_name, None)

@register.filter
def add_class(field, css_class):
    """Add a CSS class to a form field."""
    if hasattr(field, 'field') and hasattr(field.field, 'widget') and hasattr(field.field.widget, 'attrs'):
        field.field.widget.attrs['class'] = field.field.widget.attrs.get('class', '') + ' ' + css_class
    return field

@register.filter
def is_boolean_field(field):
    """Returns True if the field is a BooleanField."""
    return field.field.__class__.__name__ == 'BooleanField'

@register.filter
def is_checkbox_select_multiple(field):
    """Returns True if the field is a CheckboxSelectMultiple widget."""
    from django.forms.widgets import CheckboxSelectMultiple
    return isinstance(field.field.widget, CheckboxSelectMultiple)


