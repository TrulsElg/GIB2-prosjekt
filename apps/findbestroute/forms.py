from django import forms
from django.contrib.auth.models import User
from django.db import models as m
import models
from django.core.validators import FileExtensionValidator

valid_file_types = ['ocd', 'shp', 'dbf', 'shx', 'xml', 'prj',
                    'shx.xml', ]


class ImageUploadForm(forms.Form):
    bilde = forms.ImageField(required=True, help_text='Hjelpetekst', label='Bildelabel:')

    class Meta:
        model = models.Image


class MultiUploadForm(forms.Form):
    # form contents and metadata
    files = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}),
                           required=True,
                           label='Last opp filer',
                           validators=[FileExtensionValidator(
                                    allowed_extensions=valid_file_types)]
                           )

    # what to show:
    class Meta:
        model = models.UploadedFile
        fields = 'files'

