from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from apps.userregistration.models import PathUser


class SignUpForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=False, help_text='Optional.')
    last_name = forms.CharField(max_length=30, required=False, help_text='Optional.')
    email = forms.EmailField(max_length=254, help_text='Required. Inform a valid email address.')
    #image = forms.ImageField(required=False)

    class Meta:
        model = PathUser
        fields = ('username', 'first_name', 'middle_name', 'last_name', 'email', 'password1', 'password2', )