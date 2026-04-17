"""
Modèles Académiques
Gère : Départements, Filières, Niveaux, Matières
"""

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class Departement(models.Model):
    """
    Représente un département académique.
    Exemple : Département Informatique, Département Droit...
    """

    nom = models.CharField(
        max_length=200,
        verbose_name="Nom du département"
    )

    code = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Code du département"
    )

    description = models.TextField(
        null=True,
        blank=True,
        verbose_name="Description"
    )

    responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='departements_diriges',
        verbose_name="Responsable du département"
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="Actif"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Département"
        verbose_name_plural = "Départements"
        ordering = ['nom']

    def __str__(self):
        return f"{self.code} - {self.nom}"


# ─────────────────────────────────────────────────────────────────


class Filiere(models.Model):
    """
    Représente une filière d'études.
    Exemple : Licence Informatique, Master Finance...
    """

    departement = models.ForeignKey(
        Departement,
        on_delete=models.CASCADE,
        related_name='filieres',
        verbose_name="Département"
    )

    nom = models.CharField(
        max_length=200,
        verbose_name="Nom de la filière"
    )

    code = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Code de la filière"
    )

    description = models.TextField(
        null=True,
        blank=True,
        verbose_name="Description"
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="Active"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Filière"
        verbose_name_plural = "Filières"
        ordering = ['departement', 'nom']

    def __str__(self):
        return f"{self.code} - {self.nom}"


# ─────────────────────────────────────────────────────────────────


class Niveau(models.Model):
    """
    Représente un niveau d'études dans une filière.
    Exemple : L1, L2, L3, M1, M2...
    """

    class NiveauChoix(models.TextChoices):
        L1 = 'L1', 'Licence 1'
        L2 = 'L2', 'Licence 2'
        L3 = 'L3', 'Licence 3'
        M1 = 'M1', 'Master 1'
        M2 = 'M2', 'Master 2'
        D1 = 'D1', 'Doctorat 1'
        D2 = 'D2', 'Doctorat 2'
        D3 = 'D3', 'Doctorat 3'
        AUTRE = 'AUTRE', 'Autre'

    filiere = models.ForeignKey(
        Filiere,
        on_delete=models.CASCADE,
        related_name='niveaux',
        verbose_name="Filière"
    )

    nom = models.CharField(
        max_length=10,
        choices=NiveauChoix.choices,
        verbose_name="Niveau"
    )

    annee_academique = models.CharField(
        max_length=9,
        verbose_name="Année académique",
        help_text="Format : 2024-2025"
    )

    etudiants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='InscriptionNiveau',
        related_name='niveaux_inscrits',
        verbose_name="Étudiants inscrits"
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="Actif"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Niveau"
        verbose_name_plural = "Niveaux"
        ordering = ['filiere', 'nom']
        unique_together = ['filiere', 'nom', 'annee_academique']

    def __str__(self):
        return f"{self.filiere.code} - {self.nom} ({self.annee_academique})"

    @property
    def nombre_etudiants(self):
        return self.etudiants.filter(role='ETUDIANT').count()


# ─────────────────────────────────────────────────────────────────


class InscriptionNiveau(models.Model):
    """
    Table de liaison entre Étudiant et Niveau.
    Permet de garder l'historique des inscriptions.
    """

    etudiant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='inscriptions',
        verbose_name="Étudiant"
    )

    niveau = models.ForeignKey(
        Niveau,
        on_delete=models.CASCADE,
        related_name='inscriptions',
        verbose_name="Niveau"
    )

    date_inscription = models.DateField(
        auto_now_add=True,
        verbose_name="Date d'inscription"
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="Inscription active"
    )

    class Meta:
        verbose_name = "Inscription"
        verbose_name_plural = "Inscriptions"
        unique_together = ['etudiant', 'niveau']

    def __str__(self):
        return f"{self.etudiant.nom_complet} → {self.niveau}"


# ─────────────────────────────────────────────────────────────────


class Matiere(models.Model):
    """
    Représente une matière / un cours.
    Exemple : Algorithmique, Base de données...
    """

    niveau = models.ForeignKey(
        Niveau,
        on_delete=models.CASCADE,
        related_name='matieres',
        verbose_name="Niveau"
    )

    professeur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='matieres_enseignees',
        verbose_name="Professeur"
    )

    nom = models.CharField(
        max_length=200,
        verbose_name="Nom de la matière"
    )

    code = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Code de la matière"
    )

    description = models.TextField(
        null=True,
        blank=True,
        verbose_name="Description"
    )

    volume_horaire = models.PositiveIntegerField(
        default=30,
        verbose_name="Volume horaire (heures)"
    )

    coefficient = models.PositiveIntegerField(
        default=1,
        verbose_name="Coefficient"
    )

    seuil_absences = models.PositiveIntegerField(
        default=3,
        verbose_name="Seuil d'absences (zone rouge)",
        help_text="Nombre d'absences max avant convocation"
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="Active"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Matière"
        verbose_name_plural = "Matières"
        ordering = ['niveau', 'nom']

    def __str__(self):
        return f"{self.code} - {self.nom} ({self.niveau})"