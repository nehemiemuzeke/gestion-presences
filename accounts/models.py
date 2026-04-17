"""
Modèle Utilisateur Personnalisé
Gère les rôles : ADMIN, PROFESSEUR, ÉTUDIANT
"""

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """
    Modèle utilisateur personnalisé.
    Étend AbstractUser de Django pour ajouter nos champs spécifiques.
    """

    class Role(models.TextChoices):
        ADMIN = 'ADMIN', _('Administrateur')
        PROFESSEUR = 'PROFESSEUR', _('Professeur')
        ETUDIANT = 'ETUDIANT', _('Étudiant')

    class Statut(models.TextChoices):
        ACTIF = 'ACTIF', _('Actif')
        INACTIF = 'INACTIF', _('Inactif')
        SUSPENDU = 'SUSPENDU', _('Suspendu')

    # Champs de base (hérités de AbstractUser)
    # username, first_name, last_name, email, password, is_active, date_joined

    # Nos champs supplémentaires
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.ETUDIANT,
        verbose_name="Rôle"
    )

    matricule = models.CharField(
        max_length=50,
        unique=True,
        null=True,
        blank=True,
        verbose_name="Matricule"
    )

    telephone = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        verbose_name="Téléphone"
    )

    photo = models.ImageField(
        upload_to='photos/users/',
        null=True,
        blank=True,
        verbose_name="Photo de profil"
    )

    statut = models.CharField(
        max_length=20,
        choices=Statut.choices,
        default=Statut.ACTIF,
        verbose_name="Statut du compte"
    )

    date_naissance = models.DateField(
        null=True,
        blank=True,
        verbose_name="Date de naissance"
    )

    adresse = models.TextField(
        null=True,
        blank=True,
        verbose_name="Adresse"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de création"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Dernière modification"
    )

    # ─────────────────────────────────────────
    # PROPRIÉTÉS UTILES
    # ─────────────────────────────────────────

    @property
    def nom_complet(self):
        """Retourne le nom complet de l'utilisateur."""
        return f"{self.first_name} {self.last_name}".strip() or self.username

    @property
    def is_admin(self):
        """Vérifie si l'utilisateur est un administrateur."""
        return self.role == self.Role.ADMIN

    @property
    def is_professeur(self):
        """Vérifie si l'utilisateur est un professeur."""
        return self.role == self.Role.PROFESSEUR

    @property
    def is_etudiant(self):
        """Vérifie si l'utilisateur est un étudiant."""
        return self.role == self.Role.ETUDIANT

    @property
    def is_actif(self):
        """Vérifie si le compte est actif."""
        return self.statut == self.Statut.ACTIF

    # ─────────────────────────────────────────
    # MÉTADONNÉES
    # ─────────────────────────────────────────

    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f"[{self.role}] {self.nom_complet} ({self.matricule or self.username})"