# Generated by Django 2.2.17 on 2021-02-07 15:30

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('judge', '0117_change_default_timezone'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='problem',
            name='is_polygon_problem',
        ),
    ]