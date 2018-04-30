from __future__ import unicode_literals
from django.contrib.auth import login, authenticate
from django.contrib.auth.models import User

from django.db import models
from django.urls import reverse
from apps.userregistration.models import *

# Create your models here.


# one folder per user or something...
class MultipleFileUploadModel(models.Model):
    owner = models.ForeignKey(User, default=0)
    files = models.FileField()

    def find_best_route(self, files):
        # TODO: gjør analysen
        pass

    def get_user_upload_collection(self, owner):
        return MultipleFileUploadModel.objects.filter(owner=owner)


def user_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/user_<id>/<filename>
    return 'user_{0}/{1}'.format(instance.user.id, filename)


class Image(models.Model):
    uploader = models.ForeignKey(PathUser, blank=True, null=True, on_delete=models.SET_NULL)
    bilde = models.ImageField(upload_to='bilder/')

    def get_absolute_url(self):
        return reverse('bilde', args=(self.pk,))