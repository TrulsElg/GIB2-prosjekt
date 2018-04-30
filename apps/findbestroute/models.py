from __future__ import unicode_literals
from django.contrib.auth import login, authenticate
import django.contrib.auth.models
from django.db import models
from django.urls import reverse
from apps.userregistration.models import *
from django.core.validators import FileExtensionValidator

# Create your models here.


class MultiUpload(models.Model):
    """"
    Burde ha folgende:
        0. Egen mappe for hver bruker
        1. Liste over tillate filformat
    """
    owner = models.ForeignKey(to=PathUser, on_delete=models.CASCADE)
    files = models.FileField(
        upload_to='data_files/' + PathUser.__name__ + '/',
        validators=[FileExtensionValidator(
            allowed_extensions=['OCD', ])])
    timestamp = models.TimeField(auto_now=True)

    def find_best_route(self, files):
        # TODO: do analysis
        pass

    @staticmethod
    def get_user_upload_collection(owner):
        return MultiUpload.objects.filter(owner=owner)


def user_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/user_<id>/<filename>
    return 'user_{0}/{1}'.format(instance.user.id, filename)


class Image(models.Model):
    uploader = models.ForeignKey(PathUser, blank=True, null=True, on_delete=models.SET_NULL)
    bilde = models.ImageField(upload_to='bilder/' + PathUser.__name__ + '/')

    def get_absolute_url(self):
        return reverse('bilde', args=(self.pk,))