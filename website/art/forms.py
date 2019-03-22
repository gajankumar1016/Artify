from django import forms
from django.contrib.auth.models import User

# TODO: align max lengths with database constraints

class ArtForm(forms.Form):
    title = forms.CharField(max_length=128)
    style = forms.CharField(max_length=64)
    year = forms.IntegerField()
    art_image = forms.ImageField()

class UserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'password']
