"""
Configuration Admin pour les entités académiques
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import Departement, Filiere, Niveau, InscriptionNiveau, Matiere


@admin.register(Departement)
class DepartementAdmin(admin.ModelAdmin):
    list_display = ['code', 'nom', 'responsable', 'nombre_filieres', 'is_active']
    list_filter = ['is_active']
    search_fields = ['nom', 'code']

    def nombre_filieres(self, obj):
        return obj.filieres.count()
    nombre_filieres.short_description = 'Filières'


@admin.register(Filiere)
class FiliereAdmin(admin.ModelAdmin):
    list_display = ['code', 'nom', 'departement', 'nombre_niveaux', 'is_active']
    list_filter = ['departement', 'is_active']
    search_fields = ['nom', 'code']

    def nombre_niveaux(self, obj):
        return obj.niveaux.count()
    nombre_niveaux.short_description = 'Niveaux'


class InscriptionNiveauInline(admin.TabularInline):
    model = InscriptionNiveau
    extra = 0
    fields = ['etudiant', 'date_inscription', 'is_active']
    readonly_fields = ['date_inscription']


@admin.register(Niveau)
class NiveauAdmin(admin.ModelAdmin):
    list_display = [
        'filiere', 'nom', 'annee_academique',
        'nombre_etudiants', 'nombre_matieres', 'is_active'
    ]
    list_filter = ['nom', 'annee_academique', 'filiere__departement', 'is_active']
    search_fields = ['filiere__nom', 'nom']
    inlines = [InscriptionNiveauInline]

    def nombre_matieres(self, obj):
        return obj.matieres.count()
    nombre_matieres.short_description = 'Matières'


@admin.register(Matiere)
class MatiereAdmin(admin.ModelAdmin):
    list_display = [
        'code', 'nom', 'niveau', 'professeur',
        'volume_horaire', 'seuil_absences', 'is_active'
    ]
    list_filter = ['niveau__filiere__departement', 'niveau', 'is_active']
    search_fields = ['nom', 'code', 'professeur__last_name']
    raw_id_fields = ['professeur']