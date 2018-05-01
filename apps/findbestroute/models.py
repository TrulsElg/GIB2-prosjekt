from __future__ import unicode_literals
from django.contrib.auth import login, authenticate
import django.contrib.auth.models
from django.db import models
from django.urls import reverse
from apps.userregistration.models import *
from django.core.validators import FileExtensionValidator

# Create your models here.

# LEGG INN SHAPE-FILTYPER HER
valid_file_types = ['ocd', 'shp', 'dbf', 'shx', 'xml', 'prj',
                    'shx.xml', ]


class UploadedFile(models.Model):
    """"
    Burde ha:
        0. Egen mappe for hver bruker
        1. Liste over tillate filformat
    """
    uploader = models.ForeignKey(to=PathUser, on_delete=models.CASCADE)
    file = models.FileField(
        upload_to='data_files/',    # should be acceptable...
        validators=[FileExtensionValidator(
            allowed_extensions=valid_file_types)]
        )

    def __str__(self):
        return '"' + self.uploader.username + '"' + ' uploaded: ' + self.file.name

    def find_best_route(self, files):
        # TODO: do analysis
        pass

    @staticmethod
    def get_user_upload_collection(owner):
        return UploadedFile.objects.filter(owner=owner)


# kopiert fra interwebz, gudene veit om det er nyttig
def user_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/user_<id>/<filename>
    return 'user_{0}/{1}'.format(instance.user.id, filename)


class Image(models.Model):
    uploader = models.ForeignKey(PathUser, blank=True, null=True, on_delete=models.SET_NULL)
    bilde = models.ImageField(upload_to='bilder/')

    def get_absolute_url(self):
        return reverse('bilde', args=(self.pk,))