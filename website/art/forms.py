from django import forms
from django.contrib.auth.models import User
import sys
sys.path.insert(0, '../')
sys.path.insert(0, '../../')
sys.path.insert(0, '../../database')
from database.dbutils import DbApiInstance
from django.http import JsonResponse
from django.core.files.storage import FileSystemStorage
import uuid

artistobjs = []
with DbApiInstance() as ArtifyDbAPI:
    artistobjs = ArtifyDbAPI.get_all_artists()
    style_tuples = ArtifyDbAPI.get_unique_styles()
# TODO: align max lengths with database constraints

class ArtForm(forms.Form):
    title = forms.CharField(max_length=128)
    style = forms.CharField(max_length=64)
    year = forms.IntegerField()
    artist = forms.CharField(max_length=64)
    art_image = forms.ImageField()


class EditForm(forms.ModelForm):
    age = forms.CharField()
    gender = forms.ChoiceField(choices = [('1', 'Male'), ('2', 'Female')], widget=forms.RadioSelect)
    location = forms.CharField(label="City")

    class Meta:
        model = User
        fields = ['age', 'gender','location']

#Form for user registration info
class UserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    age = forms.CharField()
    gender = forms.ChoiceField(choices = [('1', 'Male'), ('2', 'Female')], widget=forms.RadioSelect)
    location = forms.CharField(label="City")
    #Choices from https://makingamark.blogspot.com/2016/02/what-kind-of-art-do-people-like-to-buy-online.html
    subject = forms.MultipleChoiceField(label = "Favorite Art Subjects", choices = [('1', 'Portraits'), ('2', 'Landscapes'), ('3', 'Wildlife'), ('4', 'Botanical Art'), ('5', 'Still Life'), ('6','Symbolic'), ('7', 'Show me a variety of Subjects')], widget=forms.CheckboxSelectMultiple)
    style = forms.MultipleChoiceField(label = "Preferred Art Styles", choices = [('1', 'Impressionistic'), ('2', 'Abstract'), ('3', 'Realistic'), ('4', 'Expressive'), ('5', 'Illustrative'), ('6', 'Urban and Pop Art'), ('7', 'Show me a variety of Styles')], widget=forms.CheckboxSelectMultiple)

    class Meta:
        model = User
        fields = ['username', 'password', 'age', 'gender','location', 'subject', 'style']

#Form for search parameters
class SearchForm(forms.Form):
    query = forms.CharField(label="Artwork Name", required=False)
    min_price = forms.IntegerField(required=False, label="Minimum Price")
    max_price = forms.IntegerField(required=False, label="Maximum Price")
    min_year = forms.IntegerField(required=False, label="Earliest Year")
    max_year = forms.IntegerField(required=False, label="Latest Year")
    artist = forms.MultipleChoiceField(choices = [(artistobjs[i].name,artistobjs[i].name) for i in range(len(artistobjs))],required=False, label="Artist", widget=forms.CheckboxSelectMultiple)
    style = forms.MultipleChoiceField(required=False, label = "Art Style", choices = [(style_tuples[i][0], style_tuples[i][0]) for i in range(len(style_tuples))], widget=forms.CheckboxSelectMultiple)
    
    #subject = forms.MultipleChoiceField(required=False, label = "Art Subject", choices = [('Portraits', 'Portraits'), ('Landscapes', 'Landscapes'), ('Wildlife', 'Wildlife'), ('Botanical Art', 'Botanical Art'), ('Still Life', 'Still Life'), ('Symbolic','Symbolic')], widget=forms.CheckboxSelectMultiple)
   
    
