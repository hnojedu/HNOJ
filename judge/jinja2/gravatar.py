import hashlib

from django.contrib.auth.models import AbstractUser
from django.templatetags.static import static
from django.utils.http import urlencode

from judge.models import Profile
from judge.utils.unicode import utf8bytes
from . import registry


@registry.function
def gravatar(email, size=80, default=None):
    gravatar_url = static('icons/favicon.svg')
    return gravatar_url
