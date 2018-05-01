from django.shortcuts import render, HttpResponse, HttpResponseRedirect
from apps.findbestroute.models import *

from apps.findbestroute.forms import ImageUploadForm
import forms
import os
from django.conf import settings

# Create your views here.


def index(request):
    return render(request, 'frontpage.html')


"""
def file_upload(request):
    save_path = os.path.join(settings.MEDIA_ROOT, 'uploads', request.FILES['file'])
    path = default_storage.save(save_path, request.FILES['file'])
    return default_storage.path(path)
"""


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
                m = UploadedFile()
                m.uploader = request.user
                m.file = f
                if UploadedFile.objects.filter(
                        uploader=request.user,
                        file=f):
                    print('skipped file')
                    continue    # file already exists.
                m.save()
                # One entry in the DB per file
            # valid files received; do analysis maybe?
            return analyse(request)
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


def analyse(request):
    # FIXME kjoyr analysen, hvordan det enn skal gjores.
    # Kanskje sende resultat til brukerens email pga async?
    template_name = 'analyse.html'  # Replace with your template.
    success_url = 'analyse'  # Replace with your URL or reverse().
    return render(request, template_name=template_name)


def handle_uploaded_file(f, file_owner):
    with open('uploads/'+file_owner + '/', 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)


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


