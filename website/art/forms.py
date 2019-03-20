from django import forms

class ArtForm(forms.Form):
    title = forms.CharField(max_length=128)
    style = forms.CharField(max_length=64)
    foo = forms.ImageField()

class UserForm(forms.Form):
    username = forms.CharField(max_length=20)
    password = forms.CharField(widget=forms.PasswordInput)
