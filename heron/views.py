from django.shortcuts import render


def home(request):
    return render(request, "heron/base_semantic.html")
