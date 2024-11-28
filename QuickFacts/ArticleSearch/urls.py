from django.urls import path
from . import views

urlpatterns = [
    path('',views.search_page,name='search_page'),
    path('search_articles/',views.search_articles,name='search_articles'),
]
