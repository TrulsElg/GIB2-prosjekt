from __future__ import unicode_literals
from django.contrib.auth import login, authenticate

from django.db import models
from django.urls import reverse
from apps.userregistration.models import *

# Create your models here.

class Image(models.Model):
    uploader = models.ForeignKey(PathUser, blank=True, null=True, on_delete=models.SET_NULL)
    bilde = models.ImageField(upload_to='bilder/')

    def get_absolute_url(self):
        return reverse('bilde', args=(self.pk,))