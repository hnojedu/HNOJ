# Generated by Django 2.2.28 on 2022-10-05 09:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('judge', '0180_add_problem_data_hints'),
    ]

    operations = [
        migrations.AddField(
            model_name='judge',
            name='is_disabled',
            field=models.BooleanField(default=False, help_text='Whether this judge should be removed from judging queue.', verbose_name='disable judge'),
        ),
    ]
