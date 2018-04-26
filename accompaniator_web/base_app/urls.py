from django.conf import settings
from django.urls import path, include

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('accompaniment', views.accompaniment, name='accompaniment'),
    path('results', views.results, name='results'),
]
