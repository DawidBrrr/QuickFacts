from django.shortcuts import render
from django.http import JsonResponse
from Summary.models import ArticleSummary


def search_page(request):
    return render(request,'search.html')


def search_articles(request):
    query = request.GET.get('q', '')  
    results = []

    if query:
        results = ArticleSummary.objects.filter(title__icontains=query).values('id', 'title', 'link')

    return JsonResponse(list(results), safe=False)