from django import forms
from django.contrib.auth.models import User


class ArtForm(forms.Form):
    title = forms.CharField(max_length=128)
    style = forms.CharField(max_length=64)
    foo = forms.ImageField()

class UserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'password']
