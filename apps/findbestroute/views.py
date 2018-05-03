# Create your views here.

import os.path
import tasks
import time
from models import Image
from django.conf import settings
from django.shortcuts import render, HttpResponseRedirect
from apps.findbestroute.forms import ImageUploadForm
from apps.findbestroute.models import *
from django.shortcuts import render, HttpResponse, HttpResponseRedirect
from apps.findbestroute.models import *
from apps.findbestroute.forms import ImageUploadForm
import forms
from tasks import runScript
import os
from django.conf import settings

# Create your views here.


def file_exists(some_file):
    my_file = some_file
    destination = settings.MEDIA_ROOT + 'test_files/'
    return True if os.path.isfile(destination + my_file.name) else False
    # returns true if file exists; otherwise false
#        raise fo.ValidationError(
#            'A file with the name "' + my_file.name + '" already exists. Please, rename your file and try again.'
#            )


def index(request):
    return render(request, 'frontpage.html')


def vis_filer(request):
    file_objects = UploadedFile.objects.filter(uploader=request.user)
    files = list()
    for fo in file_objects:
        files.append(fo.file)
    if files is not None:
        return render(request, 'vis_filer.html', {'files': files})
    return render(request, 'vis_filer.html', {'files': None})


def last_opp_filer(request):
    if request.method == 'POST':
        #print('Correct request method...')
        form = forms.MultiUploadForm(request.POST, request.FILES)
        if form.is_valid():
            #print('Form is valid...')
            files = request.FILES.getlist('files')
            jpg_background = request.FILES.getlist('jpg_background')

            for j in jpg_background:
                if file_exists(j):
                    continue
                k = UploadedFile()
                k.uploader = request.user
                k.file = j
                k.save()
                print('jpg-file saved')

            for f in files:
                if file_exists(f):
                    continue
                m = UploadedFile()
                m.uploader = request.user
                m.file = f
                m.save()
                print('shape-file saved')
                # One entry in the DB per file

            # Begin Celery processes
            print('Trying to make best route')

            # KJOYR GUTAR WOOOOHOOOOOOOO
            tasks.runScript.delay(request.user.pk)
            tasks.delete_user_uploads.delay(request.user.pk)
            return HttpResponseRedirect('analyse.html')

    form = forms.MultiUploadForm()
    return render(request, 'last_opp_filer.html', {'form': form} )

def analyse(request):
    return render(request=request, template_name='analyse.html', context=None)


def lastOppBilder(request):
    if request.method == 'POST':
        form = ImageUploadForm(request.POST, request.FILES)
        if form.is_valid():
            m = Image()
            m.uploader = request.user
            m.bilde = form.cleaned_data['bilde']
            m.save()
            # tror ikke dette skal vere her
            # runScript.delay(request.user.pk)
            return HttpResponseRedirect(m.get_absolute_url())

    form = ImageUploadForm()
    return render(request, 'bildeopplasting.html', {'form': form})

# data = httpRequest object; data.FILES.getlist('files') --> .shp filer, etc.


def listOppBilder(request):
#    imageModels = Image.objects.all()
    imageModels = Image.objects.filter(uploader=request.user)
    if imageModels.__len__()>0:
        text = "There exists "+str(imageModels.__len__())+" images in database"
    else:
        text = "There are no images in the database"

    return render(request, 'list_opp_bilder.html', {'text': text, 'images': imageModels})


def visBilde(request, image_id):
    image = Image.objects.get(pk=image_id)
    return render(request, 'vis_bilde.html', {'Image': image})


