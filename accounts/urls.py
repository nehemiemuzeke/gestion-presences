"""
URLs du module Accounts
"""

from django.urls import path
from . import views

urlpatterns = [

    # ── Auth ──
    path('login/',  views.login_view,  name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profil/', views.profil_view, name='profil'),

    # ── Professeurs ──
    path('admin/professeurs/',
         views.professeurs_list, name='admin_professeurs'),
    path('admin/professeurs/creer/',
         views.professeur_create, name='professeur_create'),
    path('admin/professeurs/<int:pk>/modifier/',
         views.professeur_edit, name='professeur_edit'),
    path('admin/professeurs/<int:pk>/supprimer/',
         views.professeur_delete, name='professeur_delete'),

    # ── Étudiants ──
    path('admin/etudiants/',
         views.etudiants_list, name='admin_etudiants'),
    path('admin/etudiants/creer/',
         views.etudiant_create, name='etudiant_create'),
    path('admin/etudiants/<int:pk>/modifier/',
         views.etudiant_edit, name='etudiant_edit'),
    path('admin/etudiants/<int:pk>/supprimer/',
         views.etudiant_delete, name='etudiant_delete'),

    # ── Zone Rouge et Paramètres ──
    path('admin/zone-rouge/',
         views.zone_rouge_list, name='admin_zone_rouge'),
    path('admin/parametres/',
         views.parametres_view, name='admin_parametres'),
]