from django import template
from django.forms import CheckboxInput

register = template.Library()

@register.filter
def is_checkbox(field):
    """Returns True if the field is a checkbox."""
    return isinstance(field.field.widget, CheckboxInput)

@register.filter
def attr(obj, attr_name):
    """A simple filter to access an object's attribute by name."""
    return getattr(obj, attr_name, None)
