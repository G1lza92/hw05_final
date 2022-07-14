from django.urls import path

from . import views

app_name = 'about'
# Для Андрея: да эту переменную мы используем в yatube/urls.py

urlpatterns = [
    path('author/', views.AboutAuthorView.as_view(), name='author'),
    path('tech/', views.AboutTechView.as_view(), name='tech'),
]
