from django import template

register = template.Library()

@register.filter(name='default_none')
def default_none(value):
    """
    Заменяет None на null, чтобы избежать ошибок при сериализации JSON.
    """
    return value if value is not None else None