from __future__ import unicode_literals
from django.urls import reverse
from apps.userregistration.models import *
from django.core.validators import FileExtensionValidator
from django.dispatch import receiver
import os
from django.conf import settings

# Create your models here.

# LEGG INN SHAPE-FILTYPER HER
valid_file_types = ['shp', 'dbf', 'shx', 'xml', 'prj',
                    'shx.xml', 'jpg', 'aux', 'aux.xml', 'jpg.ovr', 'jgwx', 'jpg.aux.xml', 'jpg.xml', 'ovr', 'jgw']


# kopiert fra interwebz, gudene veit om det er nyttig
def user_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/user_<id>/<filename>
    return 'user_{0}/{1}'.format(instance.uploader.id, filename)


class UploadedFile(models.Model):
    """"
    Hver enkelt fil blir knyttet til modellen
    Burde ha:
        0. Egen mappe for hver bruker
        1. Liste over tillate filformat
    """
    uploader = models.ForeignKey(to=PathUser, on_delete=models.CASCADE)
    file = models.FileField(
        # upload_to='test_files/',       # should be acceptable...
        upload_to=user_directory_path,  # alternativt
        validators=[FileExtensionValidator(
            allowed_extensions=valid_file_types)]
        )

    def __str__(self):
        return '"' + self.uploader.username + '"' + ' uploaded: ' + self.file.name

    @staticmethod
    def get_user_upload_collection(owner):
        return UploadedFile.objects.filter(uploader=owner)


class Image(models.Model):
    uploader = models.ForeignKey(PathUser, blank=True, null=True, on_delete=models.SET_NULL)
    bilde = models.ImageField()

    def __str__(self):
        return '' + self.uploader.username + ' analyzed: ' + self.bilde.name

    def get_absolute_url(self):
        return reverse('bilde', args=(self.pk,))


# sletter filer etter at tilknyttet objekt i DB er slettet
@receiver(models.signals.post_delete, sender=UploadedFile)
@receiver(models.signals.post_delete, sender=Image)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    """
    Deletes file from filesystem
    when corresponding db-object is deleted.
    """
    if instance.file:
        if os.path.isfile(instance.file.path):
            os.remove(instance.file.path)
