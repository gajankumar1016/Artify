from django import forms
from django.contrib.auth.models import User
from django.core.validators import  MaxValueValidator
from datetime import datetime


# TODO: align max lengths with database constraints
style_to_idx = {'Impressionism': 12, 'Romanticism': 23, 'Baroque': 4, 'Rococo': 22, 'Pop_Art': 19,
                'Early_Renaissance': 8, 'Color_Field_Painting': 5, 'Contemporary_Realism': 6, 'Pointillism': 18,
                'Abstract_Expressionism': 0, 'Minimalism': 14, 'Art_Nouveau_Modern': 3, 'Symbolism': 24,
                'Mannerism_Late_Renaissance': 13, 'Analytical_Cubism': 2, 'Expressionism': 9, 'Fauvism': 10,
                'Synthetic_Cubism': 25, 'Ukiyo_e': 26, 'New_Realism': 16, 'Northern_Renaissance': 17, 'Realism': 21,
                'Cubism': 7, 'Action_painting': 1, 'High_Renaissance': 11, 'Post_Impressionism': 20,
                'Naive_Art_Primitivism': 15}

style_choices = [(style, style) for i, style in enumerate(style_to_idx.keys())]

class ArtUploadForm(forms.Form):
    art_image = forms.ImageField()


class ArtDetailForm(forms.Form):
    title = forms.CharField(max_length=128)
    style = forms.ChoiceField(choices=style_choices, required=False)
    other_style = forms.CharField(max_length=64, required=False)
    year = forms.IntegerField(validators=[MaxValueValidator(datetime.today().year)])
    artist = forms.CharField(max_length=64)


class EditForm(forms.ModelForm):
    age = forms.CharField()
    gender = forms.ChoiceField(choices = [('1', 'Male'), ('2', 'Female')], widget=forms.RadioSelect)
    location = forms.CharField(label="City")

    class Meta:
        model = User
        fields = ['age', 'gender','location']


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
