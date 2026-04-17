"""
URLs du module Academic
"""

from django.urls import path
from . import views

urlpatterns = [

    # ── Départements ──
    path('departements/',
         views.departements_list, name='admin_departements'),
    path('departements/creer/',
         views.departement_create, name='departement_create'),
    path('departements/<int:pk>/modifier/',
         views.departement_edit, name='departement_edit'),
    path('departements/<int:pk>/supprimer/',
         views.departement_delete, name='departement_delete'),

    # ── Filières ──
    path('filieres/',
         views.filieres_list, name='admin_filieres'),
    path('filieres/creer/',
         views.filiere_create, name='filiere_create'),
    path('filieres/<int:pk>/modifier/',
         views.filiere_edit, name='filiere_edit'),
    path('filieres/<int:pk>/supprimer/',
         views.filiere_delete, name='filiere_delete'),

    # ── Niveaux ──
    path('niveaux/',
         views.niveaux_list, name='admin_niveaux'),
    path('niveaux/creer/',
         views.niveau_create, name='niveau_create'),
    path('niveaux/<int:pk>/modifier/',
         views.niveau_edit, name='niveau_edit'),
    path('niveaux/<int:pk>/supprimer/',
         views.niveau_delete, name='niveau_delete'),

    # ── Matières ──
    path('matieres/',
         views.matieres_list, name='admin_matieres'),
    path('matieres/creer/',
         views.matiere_create, name='matiere_create'),
    path('matieres/<int:pk>/modifier/',
         views.matiere_edit, name='matiere_edit'),
    path('matieres/<int:pk>/supprimer/',
         views.matiere_delete, name='matiere_delete'),
]