# Generated by Django 2.2.20 on 2021-04-20 09:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('judge', '0124_32char_and_underscore_problem_and_contest_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='problem',
            name='pdf_url',
            field=models.CharField(blank=True, help_text='URL to PDF statement. The PDF file must be embeddable (Mobile web browsersmay not support embedding). Fallback included.', max_length=100, verbose_name='PDF statement URL'),
        ),
    ]