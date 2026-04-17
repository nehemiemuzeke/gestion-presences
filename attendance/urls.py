"""
URLs du module Attendance - Version complète
"""

from django.urls import path
from . import views

urlpatterns = [

    # ── PROFESSEUR : Gestion des séances ──
    path(
        'seances/',
        views.prof_seances_list,
        name='prof_seances_list'
    ),
    path(
        'seances/creer/',
        views.prof_seance_creer,
        name='prof_seance_creer'
    ),
    path(
        'seances/<int:pk>/demarrer/',
        views.prof_seance_demarrer,
        name='prof_seance_demarrer'
    ),
    path(
        'seances/<int:pk>/active/',
        views.prof_seance_active,
        name='prof_seance_active'
    ),
    path(
        'seances/<int:pk>/cloturer/',
        views.prof_seance_cloturer,
        name='prof_seance_cloturer'
    ),
    path(
        'seances/<int:pk>/detail/',
        views.prof_seance_detail,
        name='prof_seance_detail'
    ),
    path(
        'seances/<int:pk>/regenerer-code/',
        views.prof_regenerer_code,
        name='prof_regenerer_code'
    ),
    path(
        'presences/<int:presence_pk>/modifier/',
        views.prof_modifier_presence,
        name='prof_modifier_presence'
    ),

    # ── API JSON ──
    path(
        'api/pointer/',
        views.api_pointer_presence,
        name='api_pointer_presence'
    ),
    path(
        'api/seance/<int:pk>/status/',
        views.api_seance_status,
        name='api_seance_status'
    ),
    path(
        'api/notifications/',
        views.api_notifications,
        name='api_notifications'
    ),
    path(
        'api/notifications/<int:pk>/lue/',
        views.api_marquer_notification_lue,
        name='api_marquer_notification_lue'
    ),
    path(
        'api/notifications/toutes-lues/',
        views.api_marquer_toutes_lues,
        name='api_marquer_toutes_lues'
    ),

    # ── ÉTUDIANT ──
    path(
        'pointer/',
        views.etudiant_pointer,
        name='etudiant_pointer'
    ),
    path(
        'historique/',
        views.etudiant_historique,
        name='etudiant_historique'
    ),

    # ── NOTIFICATIONS ──
    path(
        'notifications/',
        views.notifications_list,
        name='notifications_list'
    ),
]