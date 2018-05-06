import os

from django.conf import settings
from django.http import HttpResponseRedirect
from django.shortcuts import render

from .forms import FeedbackForm


def index(request):
    context_dict = {}
    return render(request, 'base_app/landing.html', context_dict)


def home(request):
    context_dict = {}
    return render(request, 'base_app/home.html', context_dict)


def recordings(request):
    context_dict = {}
    return render(request, 'base_app/recordings.html', context_dict)


def settings(request):
    context_dict = {}
    return render(request, 'base_app/settings.html', context_dict)


def procces(request):
    context_dict = {}
    return render(request, 'base_app/procces.html', context_dict)


def home_after_landing(request):
    context_dict = {}
    return render(request, 'base_app/home_after_landing.html', context_dict)


def results(request):
    context_dict = {}
    return render(request, 'base_app/results.html', context_dict)
