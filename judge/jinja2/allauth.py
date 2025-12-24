from allauth.socialaccount.templatetags.socialaccount import provider_login_url as allauth_provider_login_url, \
    get_providers as allauth_get_providers, providers_media_js as allauth_providers_media_js
import jinja2
from . import registry


@registry.function
@jinja2.pass_context
def provider_login_url(*args, **kwargs):
    return allauth_provider_login_url(*args, **kwargs)


@registry.function
@jinja2.pass_context
def get_providers(*args, **kwargs):
    return allauth_get_providers(*args, **kwargs)


@registry.function
@jinja2.pass_context
def providers_media_js(*args, **kwargs):
    return allauth_providers_media_js(*args, **kwargs)
