from django import template
from django.urls import reverse

register = template.Library()

@register.inclusion_tag('manager/templatetags/sidebar_link.html', takes_context=True)
def sidebar_link(context, url_name, icon_class, link_text):
    request = context['request']
    url = reverse(url_name)
    active_class = 'active' if request.path == url else ''
    return {
        'url': url,
        'active_class': active_class,
        'icon_class': icon_class,
        'link_text': link_text,
    }
