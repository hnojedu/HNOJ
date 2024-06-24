import logging
import re
from operator import itemgetter
from urllib.parse import quote

from django import forms
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.translation import gettext, gettext_lazy as _
from registration.backends.simple.views import RegistrationView as SimpleRegistrationView
from requests import HTTPError
from social_core.backends.github import GithubOAuth2
from social_core.exceptions import InvalidEmail, SocialAuthBaseException
from social_core.pipeline.partial import partial
from social_django.middleware import SocialAuthExceptionMiddleware as OldSocialAuthExceptionMiddleware

from judge.views.register import CustomRegistrationForm, RegistrationMixin

logger = logging.getLogger('judge.social_auth')


class GitHubSecureEmailOAuth2(GithubOAuth2):
    name = 'github-secure'

    def user_data(self, access_token, *args, **kwargs):
        data = self._user_data(access_token)
        try:
            emails = self._user_data(access_token, '/emails')
        except (HTTPError, ValueError, TypeError):
            emails = []

        emails = [(e.get('email'), e.get('primary'), 0) for e in emails if isinstance(e, dict) and e.get('verified')]
        emails.sort(key=itemgetter(1), reverse=True)
        emails = list(map(itemgetter(0), emails))

        if emails:
            data['email'] = emails[0]
        else:
            data['email'] = None

        return data


def slugify_username(username, renotword=re.compile(r'[^\w]')):
    return renotword.sub('', username.replace('-', '_'))


def verify_email(backend, details, *args, **kwargs):
    if not details['email']:
        raise InvalidEmail(backend)


class SocialAuthRegistrationForm(CustomRegistrationForm):
    def clean_email(self):
        # This check is not required
        if User.objects.filter(email=self.cleaned_data['email']).exists():
            raise forms.ValidationError(gettext('The email address "%s" is already taken. Only one registration '
                                                'is allowed per address.') % self.cleaned_data['email'])
        return self.cleaned_data['email']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Prevent the user from changing the email field
        self.fields['email'].disabled = True


class SocialAuthRegistrationView(RegistrationMixin, SimpleRegistrationView):
    title = _('Setup your account')
    form_class = SocialAuthRegistrationForm
    associated_email = ''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initial['email'] = self.associated_email

    def form_valid(self, form):
        return {'id_new': True, 'user': self.register(form)}


@partial
def make_user(backend, details, user, *args, **kwargs):
    if user:
        return {'id_new': False}
    return SocialAuthRegistrationView.as_view(associated_email=details['email'])(request=backend.strategy.request)


class SocialAuthExceptionMiddleware(OldSocialAuthExceptionMiddleware):
    def process_exception(self, request, exception):
        if isinstance(exception, SocialAuthBaseException):
            return HttpResponseRedirect('%s?message=%s' % (reverse('social_auth_error'),
                                                           quote(self.get_message(request, exception))))
