from django.contrib import admin
from apps.findbestroute.models import *

# Register your models here.
admin.site.register(Image)
admin.site.register(UploadedFile)

"""
class uploadAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, )
    ]
"""
