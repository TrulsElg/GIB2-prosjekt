from django import forms
from django.contrib.auth.models import User
from django.db import models as m
import models


class ImageUploadForm(forms.Form):
    bilde = forms.ImageField(required=True, help_text='Hjelpetekst', label='Bildelabel:')

    class Meta:
        model = models.Image


class MultiUploadForm(forms.Form):
    # form contents and metadata
    file_field = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}),
                                 required=True, help_text='Last opp OCAD filer',
                                 label='Last opp noe')

    # what to show:
    class Meta:
        model = models.MultiUpload
        fields = 'file_field'

