from django.shortcuts import render, HttpResponse, HttpResponseRedirect
from apps.findbestroute.models import *

from apps.findbestroute.forms import ImageUploadForm


# Create your views here.

def index(request):
    return render(request, 'frontpage.html')

def lastOppFiler(request):
    #if request.method == 'POST':



    return render(request, 'finn_beste_rute.html')



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


def listOppBilder(request):
    imageModels = Image.objects.all()
    if imageModels.__len__()>0:
        text = "There exists "+str(imageModels.__len__())+" images in database"
    else:
        text = "There are no images in the database"


    return render(request, 'list_opp_bilder.html', {'text': text, 'images': imageModels})


def visBilde(request, image_id):
    image=Image.objects.get(pk=image_id)

    return render(request, 'vis_bilde.html', {'Image': image})