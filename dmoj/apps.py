from django.contrib.admin.apps import AdminConfig


class JudgeAdminConfig(AdminConfig):
    default_site = 'dmoj.admin.JudgeAdminSite'
