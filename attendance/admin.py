"""
Configuration Admin pour les présences et séances
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import Seance, Presence, Notification


class PresenceInline(admin.TabularInline):
    model = Presence
    extra = 0
    fields = ['etudiant', 'statut', 'heure_pointage', 'distance_calculee', 'methode_pointage']
    readonly_fields = ['heure_pointage', 'distance_calculee', 'methode_pointage']
    can_delete = False


@admin.register(Seance)
class SeanceAdmin(admin.ModelAdmin):
    list_display = [
        'matiere', 'professeur', 'date_seance',
        'heure_debut', 'code_unique', 'statut_badge',
        'presents_absents'
    ]
    list_filter = ['statut', 'date_seance', 'matiere__niveau']
    search_fields = ['matiere__nom', 'professeur__last_name', 'code_unique']
    readonly_fields = [
        'code_unique', 'heure_demarrage_reel',
        'heure_cloture_reel', 'code_expire_a'
    ]
    inlines = [PresenceInline]

    def statut_badge(self, obj):
        colors = {
            'EN_ATTENTE': '#ffc107',
            'ACTIVE': '#198754',
            'CLOTUREE': '#6c757d',
            'ANNULEE': '#dc3545',
        }
        color = colors.get(obj.statut, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; '
            'padding: 3px 8px; border-radius: 4px; font-size: 12px;">{}</span>',
            color, obj.get_statut_display()
        )
    statut_badge.short_description = 'Statut'

    def presents_absents(self, obj):
        return format_html(
            '<span style="color: #198754;">✓ {}</span> / '
            '<span style="color: #dc3545;">✗ {}</span>',
            obj.nombre_presents, obj.nombre_absents
        )
    presents_absents.short_description = 'Présents / Absents'


@admin.register(Presence)
class PresenceAdmin(admin.ModelAdmin):
    list_display = [
        'etudiant', 'seance', 'statut_badge',
        'heure_pointage', 'distance_calculee', 'methode_pointage'
    ]
    list_filter = ['statut', 'methode_pointage', 'seance__date_seance']
    search_fields = [
        'etudiant__last_name', 'etudiant__first_name',
        'seance__matiere__nom'
    ]
    readonly_fields = [
        'heure_pointage', 'latitude_etudiant', 'longitude_etudiant',
        'distance_calculee', 'ip_address', 'methode_pointage', 'created_at'
    ]

    def statut_badge(self, obj):
        colors = {
            'PRESENT': '#198754',
            'ABSENT': '#dc3545',
            'RETARD': '#ffc107',
            'EXCUSE': '#0dcaf0',
        }
        color = colors.get(obj.statut, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; '
            'padding: 3px 8px; border-radius: 4px; font-size: 12px;">{}</span>',
            color, obj.get_statut_display()
        )
    statut_badge.short_description = 'Statut'


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['destinataire', 'titre', 'type_notification', 'lu', 'created_at']
    list_filter = ['type_notification', 'lu', 'created_at']
    search_fields = ['destinataire__last_name', 'titre']