from django import template

register = template.Library()

@register.filter
def status_color(status):
    """Return a Bootstrap color name for a booking status."""
    mapping = {
        'checked_in': 'success',
        'checked_out': 'secondary',
        'cancelled': 'danger',
        'pending': 'warning',
        'confirmed': 'primary',
        'no_show': 'danger',
    }
    return mapping.get(status, 'secondary')
