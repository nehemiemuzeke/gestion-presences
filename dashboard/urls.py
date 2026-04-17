"""
URLs du Dashboard
"""

from django.urls import path
from . import views

urlpatterns = [
    path('', views.accueil_redirect, name='accueil'),
    path('admin/',       views.admin_dashboard,   name='admin_dashboard'),
    path('professeur/',  views.prof_dashboard,     name='prof_dashboard'),
    path('etudiant/',    views.etudiant_dashboard, name='etudiant_dashboard'),
]