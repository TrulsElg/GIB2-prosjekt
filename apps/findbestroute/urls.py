from django.conf.urls import url

from apps.findbestroute.views import *

urlpatterns = [
    url(r'^$', lastOppFiler, name='last_opp_filer'),
    url(r'^lastoppbilde$', lastOppBilder, name='last_opp_bilde'),
    url(r'^visbilder$', listOppBilder, name='vis_bilder'),
    url('bilde/(\d+)', visBilde, name='bilde')
]