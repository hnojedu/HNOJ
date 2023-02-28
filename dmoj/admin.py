from django.contrib.admin import AdminSite
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.urls import path
from django.views.decorators.cache import never_cache

from judge.tasks.user_import import UserImportView, SampleUserCsvView


class JudgeAdminSite(AdminSite):

    def get_urls(self):
        return [
                   path('user/import/', self.admin_view(self.user_import), name='user_import'),
                   path('user/import/sample', self.admin_view(self.user_csv_sample), name='user_import_sample')
               ] + super().get_urls()

    @never_cache
    def user_import(self, request, extra_context=None):
        if not request.user.is_superuser:
            raise PermissionDenied
        opts = User._meta
        return UserImportView.as_view(extra_context={
            **self.each_context(request),
            'title': 'Import users from CSV',
            'subtitle': None,
            'opts': opts,
            **(extra_context or {}),
        })(request)

    def user_csv_sample(self, request, extra_context=None):
        if not request.user.is_superuser:
            raise PermissionDenied
        return SampleUserCsvView.as_view()(request)
