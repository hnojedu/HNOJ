# Generated by Django 3.2.23 on 2024-01-24 20:39

from django.db import migrations, models


# Functions from the following migrations need manual copying.
# Move them and any dependencies into this file, then update the
# RunPython operations to refer to the local versions:
# judge.migrations.0192_add_contest_tag_title

def populate_tag_title(apps, schema_editor):
    ContestTag = apps.get_model('judge', 'ContestTag')
    for tag in ContestTag.objects.all():
        tag.name = tag.slug
        tag.save()


class Migration(migrations.Migration):

    replaces = [('judge', '0192_add_registration_fields'), ('judge', '0192_add_contest_tag_title')]

    dependencies = [
        ('judge', '0191_submission_index_cleanup'),
    ]

    operations = [
        migrations.AddField(
            model_name='contest',
            name='registration_end',
            field=models.DateTimeField(blank=True, default=None, null=True, verbose_name='registration end time'),
        ),
        migrations.AddField(
            model_name='contest',
            name='registration_start',
            field=models.DateTimeField(blank=True, default=None, null=True, verbose_name='registration start time'),
        ),
        migrations.RenameField(
            model_name='contesttag',
            old_name='name',
            new_name='slug',
        ),
        migrations.AlterField(
            model_name='contesttag',
            name='slug',
            field=models.SlugField(help_text='Tag name shown in URLs.', max_length=20, unique=True, verbose_name='tag slug'),
        ),
        migrations.AddField(
            model_name='contesttag',
            name='name',
            field=models.CharField(max_length=128, null=True, verbose_name='tag title'),
        ),
        migrations.RunPython(populate_tag_title, reverse_code=migrations.RunPython.noop, atomic=True),
        migrations.AlterField(
            model_name='contesttag',
            name='name',
            field=models.CharField(max_length=128, verbose_name='tag title'),
        ),
    ]
