from django.conf.urls import url
from django.contrib.auth import views as auth_views

from apps.userregistration.views import *


urlpatterns = [
    url(r'^signup$', signup, name='sign_up'),
    url(r'^login', auth_views.login, {'template_name': 'userregistration/login.html'}, name='login'),
    url(r'^logout', auth_views.logout, {'next_page': '/'}, name='logout')
]