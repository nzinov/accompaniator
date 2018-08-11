import os

from django.conf import settings
from django.http import HttpResponseRedirect
from django.shortcuts import render

from .forms import FeedbackForm


def index(request):
    context_dict = {}
    return render(request, 'base_app/main.html', context_dict)


def accompaniment(request):
    if request.session.session_key is not None:
        request.session.delete()
    request.session.create()
    folder_name = request.session.session_key
    os.mkdir(os.path.join(settings.MEDIA_ROOT, folder_name))

    # ???
    # request.session.save()
    context_dict = {}
    return render(request, 'base_app/accompaniment.html', context_dict)


def results(request):
    context_dict = {}
    session_key = request.session.session_key

    context_dict['filenames'] = os.listdir(os.path.join(settings.MEDIA_ROOT, session_key))

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
    return render(request, 'base_app/results.html', context_dict)
