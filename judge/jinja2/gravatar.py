from django.templatetags.static import static

from . import registry


@registry.function
def gravatar(email, size=80, default=None):
    return static('icons/icon.svg')
