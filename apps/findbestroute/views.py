# Create your views here.

from django.shortcuts import render, HttpResponse, HttpResponseRedirect
from apps.findbestroute.models import *
from apps.findbestroute.forms import ImageUploadForm
import forms
import os
from django.conf import settings
import os.path
from django.conf import settings
from django import forms as fo
import tasks


def clean_my_file(some_file):
    my_file = some_file
    destination = settings.MEDIA_ROOT + 'data_files/'
    return False if os.path.isfile(destination + my_file.name) else my_file
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
        print('Correct request method...')
        form = forms.MultiUploadForm(request.POST, request.FILES)
        if form.is_valid():
            print('Form is valid...')
            files = request.FILES.getlist('files')
            for f in files:
                clean_my_file(f)
                m = UploadedFile()
                m.uploader = request.user
                m.file = f
                m.save()
                # One entry in the DB per file
            # valid files received; do analysis maybe?
            return analyse(request, files)
    form = forms.MultiUploadForm()
    return render(request, 'last_opp_filer.html', {'form': form})


def lastOppBilder(request):
    if request.method == 'POST':
        form = ImageUploadForm(request.POST, request.FILES)
        if form.is_valid():
            m = Image()
            m.uploader = request.user
            m.bilde = form.cleaned_data['bilde']
            m.save()
            return HttpResponseRedirect(m.get_absolute_url())

    form = ImageUploadForm()
    return render(request, 'bildeopplasting.html', {'form': form})


def analyse(request, files):
    # TODO: analysen, hvordan det enn skal gjores...

    # trigger async. process
    tasks.find_best_route.delay(request.user, files)

    # Etter at analysen er gjort:
#    UploadedFile.objects.filter(uploader=request.user).delete()
#    print('Filer har blitt slettet.')

    # redirect
    return render(request, template_name='analyse.html')



def listOppBilder(request):
    imageModels = Image.objects.filter(uploader=request.user)
    if imageModels.__len__()>0:
        text = "There exists "+str(imageModels.__len__())+" images in database"
    else:
        text = "There are no images in the database"

    return render(request, 'list_opp_bilder.html', {'text': text, 'images': imageModels})


def visBilde(request, image_id):
    image = Image.objects.get(pk=image_id)
    return render(request, 'vis_bilde.html', {'Image': image})


