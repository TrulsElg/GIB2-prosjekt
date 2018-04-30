from django.conf.urls import url

from apps.findbestroute.views import *

urlpatterns = [
    url(r'^$', upload_files, name='uploadFiles'),
    url(r'^lastoppbilde$', lastOppBilder, name='last_opp_bilde'),
    url(r'^visbilder$', listOppBilder, name='vis_bilder'),
#    url(r'^uploadFiles', uploadFiles, name='uploadFiles'),
    url('bilde/(\d+)', visBilde, name='bilde')
]