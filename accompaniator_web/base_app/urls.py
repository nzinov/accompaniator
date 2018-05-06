from django.conf import settings
from django.urls import path, include

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('results', views.results, name='results'),
    path('recordings', views.recordings, name='recordings'),
    path('settings', views.settings, name='settings'),
    path('home', views.home, name='home'),
    path('home_after_landing', views.home_after_landing, name='home_after_landing'),
    path('procces', views.procces, name='procces'),

]
