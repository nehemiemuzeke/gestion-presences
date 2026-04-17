"""
Configuration de l'interface Admin pour les Utilisateurs
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import User


@admin.register(User)
class UserAdmin(UserAdmin):
    """Interface admin personnalisée pour les utilisateurs."""

    list_display = [
        'matricule',
        'nom_complet',
        'email',
        'role_badge',
        'statut_badge',
        'date_joined'
    ]

    list_filter = ['role', 'statut', 'is_active', 'date_joined']

    search_fields = ['username', 'first_name', 'last_name', 'email', 'matricule']

    ordering = ['last_name', 'first_name']

    fieldsets = (
        ('Informations de connexion', {
            'fields': ('username', 'password')
        }),
        ('Informations personnelles', {
            'fields': (
                'first_name', 'last_name', 'email',
                'telephone', 'date_naissance', 'adresse', 'photo'
            )
        }),
        ('Informations académiques', {
            'fields': ('role', 'matricule', 'statut')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser'),
            'classes': ('collapse',)
        }),
        ('Dates importantes', {
            'fields': ('last_login', 'date_joined'),
            'classes': ('collapse',)
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username', 'first_name', 'last_name',
                'email', 'role', 'matricule',
                'password1', 'password2'
            ),
        }),
    )

    def role_badge(self, obj):
        """Affiche le rôle avec une couleur."""
        colors = {
            'ADMIN': '#dc3545',
            'PROFESSEUR': '#0d6efd',
            'ETUDIANT': '#198754',
        }
        color = colors.get(obj.role, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; '
            'padding: 3px 8px; border-radius: 4px; font-size: 12px;">{}</span>',
            color,
            obj.get_role_display()
        )
    role_badge.short_description = 'Rôle'

    def statut_badge(self, obj):
        """Affiche le statut avec une couleur."""
        colors = {
            'ACTIF': '#198754',
            'INACTIF': '#6c757d',
            'SUSPENDU': '#dc3545',
        }
        color = colors.get(obj.statut, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; '
            'padding: 3px 8px; border-radius: 4px; font-size: 12px;">{}</span>',
            color,
            obj.get_statut_display()
        )
    statut_badge.short_description = 'Statut'