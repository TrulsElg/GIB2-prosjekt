from django.conf.urls import url

from findbestroute.views import *


urlpatterns = [
    url(r'^$', test, name='test')
]