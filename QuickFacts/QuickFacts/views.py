from django.shortcuts import render

def aboutme(request):
    return render(request, 'aboutme.html')