from django.shortcuts import render, HttpResponse

# Create your views here.

def index(request):
    return render(request, 'frontpage.html')

def lastOppFiler(request):
    #if request.method == 'POST':



    return render(request, 'finn_beste_rute.html')