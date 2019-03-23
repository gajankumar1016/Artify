import sys
sys.path.insert(0, '../')
sys.path.insert(0, '../../')
sys.path.insert(0, '../../database')
from database.dbutils import DbApiInstance
from django.shortcuts import render, redirect
from .forms import UserForm, ArtForm
from django.contrib.auth import authenticate, login, logout
from django.core.files.storage import FileSystemStorage
import uuid

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


def detail(request, art_id):
    if not request.user.is_authenticated:
        return redirect('/art/login_user')
    else:
        user = request.user
        with DbApiInstance() as dbapi:
            art_info = dbapi.get_art_by_id(art_id)
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
        print(username, password)
        user.set_password(password)
        user.save()
        # Also need to add user to our user table; could add extra fields that may not be in auth_user table
        with DbApiInstance() as ArtifyDbAPI:
            ArtifyDbAPI.insert_user(username=username, password_hash=password)

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

def add_art(request):
    if not request.user.is_authenticated:
        return redirect('/art/login_user')

    form = ArtForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        title = form.cleaned_data['title']
        style = form.cleaned_data['style']
        year = form.cleaned_data['year']
        user_id = request.user.id
        file = request.FILES['art_image']
        fs = FileSystemStorage()
        file_ext = file.name.split('.')[-1]
        print(file_ext)
        unique_fname = str(uuid.uuid4()) + '.' + file_ext
        fname = fs.save(unique_fname, file)
        print(fname)

        with DbApiInstance() as artifyDbAPI:
            artifyDbAPI.insert_art(IMAGES_DIR="./media", title=title, file_name=fname, year=year, style=style,
                                   owner_id=user_id)

        return redirect('/art/user_art')

    context = {
        "form": form,
    }

    return render(request, 'art/add_art.html', context)