from django.conf.urls import url
from . import views

app_name = 'art'

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^user_art/$', views.user_art, name='user_art'),
    url(r'^register/$', views.register, name='register'),
    url(r'^login_user/$', views.login_user, name='login_user'),
    url(r'^logout_user$', views.logout_user, name='logout_user'),
    url(r'^add_art$', views.add_art, name='add_art'),
    url(r'^(?P<art_id>[0-9]+)/$', views.detail, name='detail'),
    url(r'^(?P<art_id>[0-9]+)/delete_art$', views.delete_art, name='delete_art')
]