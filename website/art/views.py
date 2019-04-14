import sys
sys.path.insert(0, '../')
sys.path.insert(0, '../../')
sys.path.insert(0, '../../database')
from database.dbutils import DbApiInstance
from django.shortcuts import render, redirect
from django.http import JsonResponse
from .forms import UserForm, EditForm, ArtUploadForm, ArtDetailForm
from django.contrib.auth import authenticate, login, logout
from django.core.files.storage import FileSystemStorage
from django.conf import settings
import uuid
import requests
import os

# Create your views here.

def index(request):
    if not request.user.is_authenticated:
        return redirect('/art/login_user')

    user_id = request.user.id

    with DbApiInstance() as ArtifyDbAPI:
        artworks = ArtifyDbAPI.get_recommended_art(user_id)

    return render(request, 'art/index.html', {'artworks':artworks})

def user_art(request):
    if not request.user.is_authenticated:
        return redirect('/art/login_user')

    user_id = request.user.id
    with DbApiInstance() as ArtifyDbAPI:
        artworks = ArtifyDbAPI.get_user_art(user_id)

    return render(request, 'art/user_art.html', {'artworks': artworks})


def user_profile(request):
    if not request.user.is_authenticated:
        return redirect('/art/login_user')

    user_id = request.user.id
    with DbApiInstance() as ArtifyDbAPI:
        user_prof = ArtifyDbAPI.get_user_by_user_id(user_id)

    return render(request, 'art/user_profile.html', {'user_prof':user_prof})


def detail(request, art_id):
    if not request.user.is_authenticated:
        return redirect('/art/login_user')
    else:
        user = request.user
        with DbApiInstance() as dbapi:
            art_info = dbapi.get_art_by_id(art_id)
        # return render(request, 'art/detail.html', {'art_info':art_info})
        return render(request, 'art/detail.html', {'art_info':art_info, 'user':user})


def register(request):
    form = UserForm(request.POST or None)
    context = {
        "form": form,
    }
    if form.is_valid():
        user = form.save(commit=False)
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']
        age = form.cleaned_data['age']
        gender = form.cleaned_data['gender']
        location = form.cleaned_data['location']
        subject_str = ""
        style_str = ""
        for item in form.cleaned_data['subject']:
            subject_str += item
        for item in form.cleaned_data['style']:
            style_str += item
        print(username, password)
        user.set_password(password)
        user.save()
        # Also need to add user to our user table; could add extra fields that may not be in auth_user table
        with DbApiInstance() as ArtifyDbAPI:
            ArtifyDbAPI.insert_user(username=username, password_hash=password, age=age, gender=gender, location=location, subject=subject_str, style=style_str)

        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                print("User has been logged in")
                return redirect('/art')

    return render(request, 'art/register.html', context)

def login_user(request):
    print("In login function")
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user:
            if user.is_active:
                login(request, user)
                return redirect('/art')
            else:
                return render(request, 'art/login.html', {'error_message': 'Your account has been disabled'})
        else:
            print("User not found")
            return render(request, 'art/login.html', {'error_message':'Invalid login'})

    return render(request, 'art/login.html')

def logout_user(request):
    logout(request)
    return redirect('/art/login_user')


def edit_user(request):
    user_id = request.user.id

    with DbApiInstance() as ArtifyDbAPI:
        user_prof = ArtifyDbAPI.get_user_by_user_id(user_id)


    form = EditForm(request.POST or None, initial={'age':user_prof.age,'gender': '1' if user_prof.gender == "M" else '2','location':user_prof.location})
    context = {
        "form": form,
    }
    if form.is_valid():
        user = form.save(commit=False)

        age = form.cleaned_data['age']
        gender = form.cleaned_data['gender']
        location = form.cleaned_data['location']

        with DbApiInstance() as ArtifyDbAPI:
            ArtifyDbAPI.edit_user(id=user_id, age=age, gender=gender, location=location)

        return redirect('/art/user_profile')

    return render(request, 'art/user_edit.html', context)


def add_art(request):
    if not request.user.is_authenticated:
        return redirect('/art/login_user')

    form = ArtUploadForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        # TODO: make sure file has valid file extension
        file = request.FILES['art_image']
        fs = FileSystemStorage()
        file_ext = file.name.split('.')[-1]
        print(file_ext)
        unique_fname_no_ext = str(uuid.uuid4())
        unique_fname = unique_fname_no_ext + '.' + file_ext
        fname = fs.save(unique_fname, file)
        print(fname)

        return redirect('/art/add_art_detail/' + unique_fname_no_ext + '/ext/' + file_ext)

    context = {
        "form": form,
    }

    return render(request, 'art/add_art.html', context)


def add_art_detail(request, fname, ext):
    if not request.user.is_authenticated:
        return redirect('/art/login_user')

    def get_most_likely_style(img_path):
        URL = "http://localhost:5000/predict"

        image = open(img_path, "rb").read()
        payload = {"image": image}

        # make request to the API
        request = requests.post(URL, files=payload).json()

        max_prob = 0
        most_likely_style = None
        if request["success"]:
            # Print formatted Result
            print("% s % 15s % s" % ("Rank", "Label", "Probability"))
            for (i, result) in enumerate(request["predictions"]):
                label = result["label"]
                prob = result["probability"]
                print("% d. % 17s %.4f" % (i + 1, label, prob))

                if prob > max_prob:
                    max_prob = prob
                    most_likely_style = label
        return most_likely_style


    fname = fname + "." + ext
    form = ArtDetailForm(request.POST or None)
    if form.is_valid():
        title = form.cleaned_data['title']
        style = form.cleaned_data['style']
        other_style = form.cleaned_data['other_style']
        year = form.cleaned_data['year']
        artist = form.cleaned_data['artist']
        user_id = request.user.id

        if other_style:
            style = other_style

        with DbApiInstance() as artifyDbAPI:
            artist_obj = artifyDbAPI.get_artist_by_name(name=artist)
            if not artist_obj:
                artist_obj = artifyDbAPI.insert_artist(name=artist)

            artifyDbAPI.insert_art(IMAGES_DIR="./media", title=title, file_name=fname, year=year, style=style,
                                   owner_id=user_id, artist_id=artist_obj.id)

        return redirect('/art/user_art')


    print("Initial style", form.fields["style"].initial)
    try:
        most_likely_style = get_most_likely_style(os.path.join(settings.MEDIA_ROOT, fname))
        print("Most likely style: ", most_likely_style)
        form.fields["style"].initial = most_likely_style
    except Exception as e:
        print(e)
        print("Could not get most likely style. Make sure server is up")

    context = {
        "form": form,
        "file_name": fname
    }

    return render(request, 'art/add_art_detail.html', context)


def delete_art(request, art_id):
    # TODO: Prevent user from deleting another user's art
    if not request.user.is_authenticated:
        return redirect('/art/login_user')

    with DbApiInstance() as dbapi:
        art = dbapi.get_art_by_id(art_id)
        fs = FileSystemStorage()
        fs.delete(art.file_name)
        dbapi.delete_art(art_id)
    return redirect('/art/user_art')


def like_art(request, art_id):
    if not request.user.is_authenticated:
        return redirect('/art/login_user')

    user_id = request.user.id
    with DbApiInstance() as dbapi:
        like_exists = dbapi.does_like_exist(user_id, art_id)
        if like_exists:
            dbapi.delete_like(user_id, art_id)
        else:
            dbapi.insert_like(user_id, art_id)

    # TODO: return JsonResponse instead and implement javascript so whole page doesn't scroll
    # return JsonResponse({'success': True})
    return redirect('/art/')
