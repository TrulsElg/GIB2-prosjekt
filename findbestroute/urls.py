from django.conf.urls import url

from findbestroute.views import *


urlpatterns = [
    url(r'^$', lastOppFiler, name='last_opp_filer')
]