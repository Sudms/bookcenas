from django.shortcuts import render, redirect

# Create your views here.

def home(request):
    return render(request, 'index.html', {})

def celebrity(request):
    return render(request, 'celebrity-detail.html', {})

def celebrities(request):
    return render(request, 'celebrities-grid.html', {})

def movie(request):
    return render(request, 'movie-detail.html', {})

def movies(request):
    return render(request, 'movie-grid.html', {})
