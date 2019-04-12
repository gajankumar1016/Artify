import sys
sys.path.insert(0, '../')
sys.path.insert(0, '../../')
sys.path.insert(0, '../../database')
from database.dbutils import DbApiInstance
from django.shortcuts import render, redirect
from django.http import JsonResponse
from .forms import UserForm, ArtForm, EditForm, SearchForm
from django.contrib.auth import authenticate, login, logout
from django.core.files.storage import FileSystemStorage
import uuid
import nltk
from nltk.stem import PorterStemmer
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import wordnet
from nltk.metrics.distance import edit_distance
import re
import copy

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

#For debugging
#file = open("logfile.txt", "w")
#American Soundex for a given term
#Citation: Algo from https://en.wikipedia.org/wiki/Soundex#American_Soundex
def getSoundex(term):
    #file.write(term)
    first = term[0]
    term = re.sub("a|e|i|o|u|y|h|w", '', term)
    term = re.sub("b|f|p|v", '1', term)
    term = re.sub("c|g|j|k|q|s|x|z", '2', term)
    term = re.sub("d|t", '3', term)
    term = re.sub("l", '4', term)
    term = re.sub("m|n", '5', term)
    term = re.sub("r", '6', term)

    adjrem = ''
    for i in range(len(term) - 1):
        if not term[i] == term[i+1]:
            adjrem += term[i]
    firstcopy = copy.copy(first)
    firstcopy = re.sub("a|e|i|o|u|y|h|w", '', firstcopy)
    firstcopy = re.sub("b|f|p|v", '1', firstcopy)
    firstcopy = re.sub("c|g|j|k|q|s|x|z", '2', firstcopy)
    firstcopy = re.sub("d|t", '3', firstcopy)
    firstcopy = re.sub("l", '4', firstcopy)
    firstcopy = re.sub("m|n", '5', firstcopy)
    firstcopy = re.sub("r", '6', firstcopy)

    if len(adjrem) > 0 and firstcopy == adjrem[0]:
        adjrem = adjrem[1:]

    if len(adjrem) < 3:
        for i in range(3 - len(adjrem)):
            adjrem += '0'

    if len(adjrem) > 3:
        adjrem = adjrem[:3]

    encoding = first + adjrem
    #file.write(encoding)
    return encoding
    
#Big Idea is that we do something intelligent with the query string,
#the other parameters dynamically appended to where conditions
#Note: All search params optional
#Note: We should apply all the non-query paramaters first so that we dont waste effort
#      calculating NLP metrics on the whole art relation
def search(request):
    form = SearchForm(request.POST or None)
    context = {
        "form": form,
    }
    if form.is_valid():
        #Read the search parameters and form the condition strings
        conditions = []
        query = form.cleaned_data['query']
        
        min_price = form.cleaned_data['min_price']
        if min_price != None: 
            conditions.append("price >= " + str(min_price))
        
        max_price = form.cleaned_data['max_price']
        if max_price != None:
            conditions.append("price <= " + str(max_price))

        min_year = form.cleaned_data['min_year']
        if min_year != None: 
            conditions.append("year >= " + str(min_year))
        
        max_year = form.cleaned_data['max_year']
        if max_year != None:
            conditions.append("year <= " + str(max_year))
            
        subject_list = ''
        style_list = ''
        artist_list = ''
        #To do: Somthing with subject

        styles = form.cleaned_data['style']
        if len(styles) > 0:
            for i in range(len(styles)):
                style_list += 'style LIKE ' + '"'+styles[i]+'"'
                if i < len(styles) - 1:
                     style_list += ' OR '

            conditions.append(style_list)

        artists = form.cleaned_data['artist']
        if len(artists) > 0:
            for i in range(len(artists)):
                artist_list += 'name LIKE ' + '"'+artists[i]+'"'
                if i < len(artists) - 1:
                     artist_list += ' OR '

            conditions.append(artist_list)

        #Apply the where conditions to reduce size of intermediate relation
        #artworks is a list of ArtDetail objs
        artworks = []
        filtered_artworks = []
        with DbApiInstance() as ArtifyDbAPI:
            artworks = ArtifyDbAPI.get_art_by_cond(conditions)
        
        #For the search query
        #1.Tokenization, Porter Stemming, Levenshtein distance for word similarity(Spellcheck).
        #2.WordNet for synonymity/semantic similarity
        #3.American Soundex Algo (Fuzzy Search) for phonetic similarity
        #4.Substring/Exact match
        #5.Take best of all 4

        if query != '' and query is not None:
            #Step 1
            query = query.lower()
            porter = PorterStemmer()
            tokens = word_tokenize(query) #tokens - list of tokens

            lev_dist = []
            synonyms_sets = [] #List of unioned sets of synonyms for each term in each art title
            query_syn_set = set() #Synonym set for query terms
            query_encodings = set() #Soundex encodings for query terms
            #Step 2
            #Generating synonym set for query terms
            for term in tokens:
                syn_list = []
                for syn in wordnet.synsets(term):
                    for l in syn.lemmas():
                        syn_list.append(l.name())
                query_syn_set = query_syn_set.union(set(syn_list))

            #Generating soundex set for query terms
            for term in tokens:
                query_encodings.add(getSoundex(term))
            
            #Generating synonym set for art title terms for all the art titles
            #Note: This can possibly be cached
            for art in artworks:
                
                #Step 1
                lev_dist.append(edit_distance(porter.stem(query), porter.stem(art.title.lower())))

                #Step 2
                title_terms = word_tokenize(art.title.lower())
                syn_set = set()
                for term in title_terms:
                    syn_list = []
                    for syn in wordnet.synsets(term):
                        for l in syn.lemmas():
                            syn_list.append(l.name())
                    syn_set = syn_set.union(set(syn_list))
                synonyms_sets.append(syn_set)
                
                #Step 3
                encodings = set()
                for term in title_terms:
                    encodings.add(getSoundex(term))

                #Step 4
                exact_match = False
                substring = False
                query = query.lower()
                art_title = art.title.lower()
                if query == art_title:
                    exact_match = True
                if art_title.find(query) >= 0:
                    substring = True
                if query.find(art_title) >= 0:
                    substring = True

                #Step 5
                include_this_piece = False
                if exact_match == True or substring == True:
                    include_this_piece = True
                    
                elif lev_dist[len(lev_dist) - 1] <= 3:
                    include_this_piece = True

                elif len(query_syn_set.intersection(syn_set)) > 0:
                    include_this_piece = True

                elif len(query_encodings.intersection(encodings)) > 0:
                    include_this_piece = True

                if include_this_piece == True:
                    filtered_artworks.append(art)
                    
        else:
            filtered_artworks = artworks
        return render(request, 'art/searchResult.html', {'artworks':filtered_artworks})
    
    return render(request, 'art/search.html', context)

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

    form = ArtForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        title = form.cleaned_data['title']
        style = form.cleaned_data['style']
        year = form.cleaned_data['year']
        artist = form.cleaned_data['artist']
        user_id = request.user.id

        # TODO: make sure file has valid file extension
        file = request.FILES['art_image']
        fs = FileSystemStorage()
        file_ext = file.name.split('.')[-1]
        print(file_ext)
        unique_fname = str(uuid.uuid4()) + '.' + file_ext
        fname = fs.save(unique_fname, file)
        print(fname)

        with DbApiInstance() as artifyDbAPI:
            artist_obj = artifyDbAPI.get_artist_by_name(name=artist)
            if not artist_obj:
                artist_obj = artifyDbAPI.insert_artist(name=artist)

            artifyDbAPI.insert_art(IMAGES_DIR="./media", title=title, file_name=fname, year=year, style=style,
                                   owner_id=user_id, artist_id=artist_obj.id)

        return redirect('/art/user_art')

    context = {
        "form": form,
    }

    return render(request, 'art/add_art.html', context)


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
