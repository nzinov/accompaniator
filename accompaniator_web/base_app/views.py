import os

from django.conf import settings
from django.http import HttpResponseRedirect
from django.shortcuts import render

from .forms import FeedbackForm


def index(request):
    context_dict = {}
    return render(request, 'base_app/landing.html', context_dict)


def home(request):
    context_dict = {'after_landing': False}

    return render(request, 'base_app/home.html', context_dict)


def recordings(request):
    context_dict = {}

    session_key = request.session.session_key

    context_dict['filenames'] = os.listdir(os.path.join(settings.MEDIA_ROOT, session_key))

    return render(request, 'base_app/recordings.html', context_dict)


def preferences(request):
    context_dict = {}
    return render(request, 'base_app/settings.html', context_dict)


def home_after_landing(request):
    context_dict = {'after_landing': True}
    return render(request, 'base_app/home.html', context_dict)


def results(request):
    context_dict = {}
    session_key = request.session.session_key

    if request.method == 'POST':
        form = FeedbackForm(request.POST, request.FILES)
        if form.is_valid():
            instance = form.save(commit=False)
            instance.session_key = session_key
            instance.save()
            return HttpResponseRedirect('/results')

        else:
            print(form.errors)
    else:
        form = FeedbackForm()

    context_dict['feedback_form'] = form

    context_dict['stars_range'] = range(1, 6)
    return render(request, 'base_app/results.html', context_dict)
