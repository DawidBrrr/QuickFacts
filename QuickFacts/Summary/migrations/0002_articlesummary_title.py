# Generated by Django 5.1.2 on 2024-11-08 16:29

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Summary', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='articlesummary',
            name='title',
            field=models.CharField(default=django.utils.timezone.now, max_length=255),
            preserve_default=False,
        ),
    ]