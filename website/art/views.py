import sys
sys.path.insert(0, '../')
sys.path.insert(0, '../../')
sys.path.insert(0, '../../database')
from database.dbutils import DbApiInstance
from django.shortcuts import render
from .forms import UserForm, ArtForm

# Create your views here.

def index(request):
    return render(request, 'art/index.html', {'sample_img': "3.jpg"})

def register(request):
    form = UserForm(request.POST or None)
    if form.is_valid():
        pass

    context = {
        "form":form,
    }
    return render(request, 'art/register.html', context)

def login_user(request):
    print("Log in!")
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        # TODO: authenticate user

    return render(request, 'art/login.html')

def logout_user(request):
    # TODO: logout logic
    return render(request, 'art/login.html')

def add_art(request):
    # TODO: authentication
    authenticated = True
    if not authenticated:
        #Redirect to login page
        pass
    else:
        return render(request, 'art/add_art.html')