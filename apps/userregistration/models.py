from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.

class PathUser(AbstractUser):
    middle_name = models.CharField(max_length=50, blank=True, null=True)

    def get_full_name(self):
        if self.middle_name:
            first_name = self.first_name + ' ' + self.middle_name
        else:
            first_name = self.first_name
        if first_name == "" and self.last_name == "":
            return self.username
        return first_name + ' ' + self.last_name

    full_name = property(get_full_name)