import csv

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.forms import formset_factory
from django.http import HttpResponse, Http404, JsonResponse
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView, TemplateView
from django.views.generic.base import TemplateResponseMixin, ContextMixin, View
from django.views.generic.edit import ProcessFormView

from judge.models import Organization, Profile, Language

fields = ['username', 'password', 'name', 'school', 'email', 'organizations']
descriptions = ['my_username(edit old one if exist)',
                '123456 (must have)',
                'Le Van A (can be empty)',
                'Le Quy Don (can be empty)',
                'email@email.com (can be empty)',
                'org1&org2&org3&... (can be empty - org slug in URL)']


class CsvForm(forms.Form):
    file = forms.FileField(label=_('User file'))

    def __init__(self, data_field='', **kwargs):
        super().__init__(**kwargs)
        self.data_field = data_field

    def clean(self):
        cleaned_data = super().clean()
        if 'file' not in cleaned_data:
            return cleaned_data
        try:
            # with open(cleaned_data['file'], newline='') as csvfile:
            reader = csv.DictReader([line.decode() for line in cleaned_data['file']], delimiter=',')
            data = []
            for index, row in enumerate(reader):
                for header in fields:
                    if header not in row:
                        raise ValidationError('Unable to find "%s" on row %d' % (header, index))
                data.append(row)
            cleaned_data[self.data_field] = data

        except ValidationError as e:
            self.add_error('file', e)
        except IOError:
            self.add_error('file', 'Unexpected error')
        return cleaned_data


class ImportForm(forms.Form):
    username = forms.CharField(label=_('Username'))
    password = forms.CharField(label=_('Password'))
    name = forms.CharField(label=_('Name'), required=False)
    school = forms.CharField(label=_('School'), required=False)
    email = forms.CharField(label=_('Email'), required=False)
    organizations = forms.CharField(label=_('Organizations'), required=False)

    def commit(self):
        """
        Adds (or changes) a user using supplied form fields.
        Commits directly into DB without any validation.
        """

        # based from https://github.com/LQDJudge/online-judge/blob/d01f536935a037894790c2ac1c55a91e1af61075/judge/tasks/import_users.py

        log = ''
        row = self.cleaned_data

        username = row['username']
        log += username + ': '

        pwd = row['password']

        user, created = User.objects.get_or_create(username=username, defaults={
            'is_active': True,
        })

        profile, _ = Profile.objects.get_or_create(user=user)

        if created:
            log += 'Create new - '
        else:
            log += 'Edit - '

        if pwd:
            user.set_password(pwd)
        elif created:
            user.set_password('lqdoj')
            log += 'Missing password, set password = lqdoj - '

        if 'name' in row and row['name']:
            user.first_name = row['name']

        if 'school' in row.keys() and row['school']:
            user.last_name = row['school']

        if row['organizations']:
            orgs = row['organizations'].split('&')
            added_orgs = []
            for o in orgs:
                try:
                    org = Organization.objects.get(slug=o)
                    profile.organizations.add(org)
                    added_orgs.append(org.name)
                except Organization.DoesNotExist:
                    continue
            if added_orgs:
                log += 'Added to ' + ', '.join(added_orgs) + ' - '

        if row['email']:
            user.email = row['email']

        user.save()
        profile.save()
        log += 'Saved\n'
        return log

    # def clean(self):
    #     cleaned_data = super().clean()
    #     user = User(
    #         username=cleaned_data.get('username'),
    #         first_name=cleaned_data.get('full_name'),
    #         last_name=cleaned_data.get('school'),
    #         email=cleaned_data.get('email')
    #     )
    #     try:
    #         validate_password(cleaned_data.get('password'))
    #     except ValidationError as e:
    #         raise ValidationError({'password': e.message})
    #     user.set_password(cleaned_data.get('password'))
    #     try:
    #         user.full_clean()
    #     except ValidationError as e:
    #         message_dict = e.message_dict
    #         if 'first_name' in message_dict:
    #             message_dict['full_name'] = message_dict.pop('first_name')
    #         if 'last_name' in message_dict:
    #             message_dict['school'] = message_dict.pop('last_name')
    #         raise ValidationError(message_dict)


class SampleUserCsvView(View):
    def get(self, request):
        filename = 'import_sample.csv'
        content = ','.join(fields) + '\n' + ','.join(descriptions)
        response = HttpResponse(content, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename={0}'.format(filename)
        return response


class UserImportView(ContextMixin, TemplateResponseMixin, ProcessFormView):
    csv_form_class = CsvForm
    import_form_class = ImportForm
    import_formset_class = formset_factory(import_form_class, extra=0)
    template_name = 'admin/auth/user/import_form.html'
    action_keyword = 'action'
    csv_form_action = 'csv-form'
    import_form_action = 'import-form'
    csv_form_data_field = 'data'
    import_form_initial = None

    def post(self, request, *args, **kwargs):
        action = request.POST[self.action_keyword]
        if action == self.csv_form_action:
            csv_form = self.get_csv_form()
            if csv_form.is_valid():
                self.import_form_initial = csv_form.cleaned_data[self.csv_form_data_field]

            return self.render_to_response(self.get_context_data(
                csv_form=csv_form,
                import_form=self.import_formset_class(initial=self.import_form_initial)
            ))
        elif action == self.import_form_action:
            import_form = self.get_import_form()
            if import_form.is_valid():
                log = ''
                for index, form in enumerate(import_form):
                    log += ('%d. ' % index) + form.commit()
                return JsonResponse({'msg': log})
            else:
                return self.render_to_response(self.get_context_data(
                    csv_form=self.csv_form_class(data_field=self.csv_form_data_field),
                    import_form=import_form
                ))

        return self.render_to_response(self.get_context_data())

    def get_csv_form_kwargs(self):
        kwargs = {
            # 'prefix': 'csv-form',
            'data_field': self.csv_form_data_field,
        }
        if self.request.method in ('POST', 'PUT'):
            kwargs.update(
                {
                    'data': self.request.POST,
                    'files': self.request.FILES,
                }
            )
        return kwargs

    def get_import_form_kwargs(self):
        kwargs = {
            'initial': self.import_form_initial,
            # 'prefix': 'import-form',
        }
        if self.request.method in ('POST', 'PUT'):
            kwargs.update(
                {
                    'data': self.request.POST,
                    'files': self.request.FILES,
                }
            )
        return kwargs

    def get_csv_form(self):
        return self.csv_form_class(**self.get_csv_form_kwargs())

    def get_import_form(self):
        return self.import_formset_class(**self.get_import_form_kwargs())

    def get_context_data(self, **kwargs):
        if 'csv_form' not in kwargs:
            kwargs['csv_form'] = self.get_csv_form()
        if 'import_form' not in kwargs:
            kwargs['import_form'] = self.get_import_form()
        return super().get_context_data(**kwargs)

    # def form_valid(self, formset):
    #     for form in formset:
    #         cleaned_data = form.cleaned_data
    #         user = User(
    #             username=cleaned_data.get('username'),
    #             first_name=cleaned_data.get('full_name'),
    #             last_name=cleaned_data.get('school'),
    #             email=cleaned_data.get('email')
    #         )
    #         user.set_password(cleaned_data.get('password'))
    #         profile = Profile(user=user)
    #         profile.organizations.add(*cleaned_data.get['organizations'])
    #         user.save()
    #         profile.save()
    #     return self.render_to_response(self.get_context_data(form=formset))
    # return super().form_valid(formset)

# class UserImportAdmin(UserAdmin):
#     import_form_template = 'admin/auth/user/import_form.html'
#
#     def get_urls(self):
#         return [
#             path(
#                 'import/',
#                 self.admin_site.admin_view()
#             ),
#         ] + super().get_urls()
#
#     def import_view(self, request, extra_context=None):
