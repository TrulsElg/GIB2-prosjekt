# -*- coding: utf-8 -*-
# Generated by Django 1.11.12 on 2018-04-30 20:57
from __future__ import unicode_literals

from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('findbestroute', '0002_auto_20180430_2115'),
    ]

    operations = [
        migrations.CreateModel(
            name='MultiUpload',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('files', models.FileField(upload_to='data_files/PathUser/', validators=[django.core.validators.FileExtensionValidator(allowed_extensions=['OCD'])])),
                ('timestamp', models.TimeField(auto_now=True)),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.RemoveField(
            model_name='multiplefileuploadmodel',
            name='owner',
        ),
        migrations.AlterField(
            model_name='image',
            name='bilde',
            field=models.ImageField(upload_to='bilder/PathUser/'),
        ),
        migrations.DeleteModel(
            name='MultipleFileUploadModel',
        ),
    ]
