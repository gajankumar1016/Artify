import sys
sys.path.insert(0, '../')
sys.path.insert(0, '../../')
sys.path.insert(0, '../../database')
from database.dbutils import DbApiInstance
from django.shortcuts import render, redirect
from .forms import UserForm, ArtForm
from django.contrib.auth import authenticate, login, logout
# Create your views here.

def index(request):
    print("In index")
    if not request.user.is_authenticated:
        return render(request, 'art/login.html')
    user_id = request.user.id
    print(user_id)

    with DbApiInstance() as ArtifyDbAPI:
        artworks = ArtifyDbAPI.get_recommended_art(user_id)

    return render(request, 'art/index.html', {'artworks':artworks})

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
        with DbApiInstance() as ArtifyDbAPI:
            ArtifyDbAPI.insert_user(username=username, password_hash=password)

        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                print("User has been logged in")
                return redirect('/art')

        # with DbApiInstance() as ArtifyDbAPI:
        #     if ArtifyDbAPI.user_exists(username):
        #         # User already exists! Probably should display error
        #         print("Username already taken")
        #         return render(request, 'art/register.html', context)
        #
        #     ArtifyDbAPI.insert_user(username=username, password_hash=password)
        #     return render(request, 'art/login.html')

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
    # TODO: authentication
    authenticated = True
    if not authenticated:
        #Redirect to login page
        pass
    else:
        return render(request, 'art/add_art.html')