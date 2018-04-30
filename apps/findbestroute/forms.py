from django import forms

from django.contrib.auth.models import User
from django.db import models
import models


class ImageUploadForm(forms.Form):
    bilde = forms.ImageField(required=True, help_text='Hjelpetekst', label='Bildelabel:')


class MultipleFileUploadForm(forms.Form):
    # form contents and metadata
    file_field = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}), required=True,
                                 help_text='Last opp OCAD filer', label='Last opp noe')
    owner = models.ForeignKey(to=User, on_delete='CASCADE')
    timestamp = models.TimeField(auto_now=True)

    # what to show:
    class Meta:
        model = models.MultipleFileUploadModel
        fields = 'file_field'

