from django import forms
import models
from django.core.validators import FileExtensionValidator

valid_file_types = ['shp', 'dbf', 'shx', 'xml', 'prj',
                    'shx.xml', 'jpg', 'aux', 'aux.xml', 'jpg.ovr', 'jgwx', 'jpg.aux.xml']


class ImageUploadForm(forms.Form):
    bilde = forms.ImageField(required=True, help_text='Hjelpetekst', label='Bildelabel:')

    class Meta:
        model = models.Image


class MultiUploadForm(forms.Form):
    jpg_background = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}),
                                     required=True,
                                     label='Last opp georeferert JPG fil',
                                     validators=[FileExtensionValidator(
                                         allowed_extensions=valid_file_types)]
                                     )
    files = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}),
                            required=True,
                            label='Last opp alle SHAPE-filer til bruk (areal, linje, punkt)',
                            validators=[FileExtensionValidator(
                                allowed_extensions=valid_file_types)]
                            )

    # what to show:
    class Meta:
        model = models.UploadedFile
        fields = 'jpg_background', 'files',

"""
class ShapeFilesUploadForm(forms.Form):
    # form contents and metadata
    area_files = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}),
                                 required=True,
                                 label='Last opp shape-filer (areal)',
                                 validators=[FileExtensionValidator(
                                    allowed_extensions=valid_file_types)]
                                 )
    line_files = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}),
                                 required=True,
                                 label='Last opp shape-filer (linje)',
                                 validators=[FileExtensionValidator(
                                     allowed_extensions=valid_file_types)]
                                 )
    point_files = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}),
                                  required=True,
                                  label='Last opp shape-filer (punkt)',
                                  validators=[FileExtensionValidator(
                                      allowed_extensions=valid_file_types)]
                                  )

    # what to show:
    class Meta:
        model = models.UploadedFile
        fields = 'area_files', 'line_files', 'point_files'
"""
