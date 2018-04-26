from django.shortcuts import render


def index(request):
    context_dict = {}
    return render(request, 'base_app/main.html', context_dict)


def accompaniment(request):
    context_dict = {}
    return render(request, 'base_app/accompaniment.html', context_dict)

def results(request):
    context_dict = {}
    return render(request, 'base_app/results.html', context_dict)
