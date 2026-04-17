"""
Modèles de Gestion des Présences
Gère : Séances, Présences, Géolocalisation
"""

import random
import string
import math
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


def generer_code_unique():
    """
    Génère un code alphanumérique unique de 6 caractères.
    Exemple : K7M2P9
    Utilise uniquement des majuscules et chiffres (pas O, 0, I, 1 pour éviter confusion)
    """
    caracteres = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
    return ''.join(random.choices(caracteres, k=6))


def calculer_distance_gps(lat1, lon1, lat2, lon2):
    """
    Calcule la distance en mètres entre deux points GPS.
    Utilise la formule de Haversine.

    Args:
        lat1, lon1 : Coordonnées du professeur
        lat2, lon2 : Coordonnées de l'étudiant

    Returns:
        Distance en mètres (float)
    """
    # Rayon de la Terre en mètres
    R = 6_371_000

    # Conversion en radians
    lat1_rad = math.radians(float(lat1))
    lat2_rad = math.radians(float(lat2))
    delta_lat = math.radians(float(lat2) - float(lat1))
    delta_lon = math.radians(float(lon2) - float(lon1))

    # Formule de Haversine
    a = (math.sin(delta_lat / 2) ** 2 +
         math.cos(lat1_rad) * math.cos(lat2_rad) *
         math.sin(delta_lon / 2) ** 2)

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance = R * c

    return round(distance, 2)


# ─────────────────────────────────────────────────────────────────


class Seance(models.Model):
    """
    Représente une séance de cours.
    C'est ici que le code de présence est généré.
    """

    class Statut(models.TextChoices):
        EN_ATTENTE = 'EN_ATTENTE', _('En attente')
        ACTIVE = 'ACTIVE', _('Active')
        CLOTUREE = 'CLOTUREE', _('Clôturée')
        ANNULEE = 'ANNULEE', _('Annulée')

    matiere = models.ForeignKey(
        'academic.Matiere',
        on_delete=models.CASCADE,
        related_name='seances',
        verbose_name="Matière"
    )

    professeur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='seances_enseignees',
        verbose_name="Professeur"
    )

    # ── Informations de la séance ──
    date_seance = models.DateField(
        verbose_name="Date de la séance"
    )

    heure_debut = models.TimeField(
        verbose_name="Heure de début"
    )

    heure_fin = models.TimeField(
        verbose_name="Heure de fin prévue",
        null=True,
        blank=True
    )

    salle = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name="Salle / Lieu"
    )

    # ── Code de présence ──
    code_unique = models.CharField(
        max_length=6,
        unique=True,
        verbose_name="Code de présence"
    )

    code_expire_a = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Le code expire à"
    )

    duree_code_minutes = models.PositiveIntegerField(
        default=10,
        verbose_name="Durée du code (minutes)"
    )

    # ── Géolocalisation du professeur ──
    latitude_prof = models.DecimalField(
        max_digits=10,
        decimal_places=8,
        null=True,
        blank=True,
        verbose_name="Latitude du professeur"
    )

    longitude_prof = models.DecimalField(
        max_digits=11,
        decimal_places=8,
        null=True,
        blank=True,
        verbose_name="Longitude du professeur"
    )

    rayon_metres = models.PositiveIntegerField(
        default=15,
        verbose_name="Rayon autorisé (mètres)"
    )

    # ── Statut de la séance ──
    statut = models.CharField(
        max_length=20,
        choices=Statut.choices,
        default=Statut.EN_ATTENTE,
        verbose_name="Statut"
    )

    # ── Timestamps ──
    heure_demarrage_reel = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Heure de démarrage réel"
    )

    heure_cloture_reel = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Heure de clôture réelle"
    )

    notes = models.TextField(
        null=True,
        blank=True,
        verbose_name="Notes"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # ─────────────────────────────────────────
    # MÉTHODES
    # ─────────────────────────────────────────

    def demarrer(self, latitude, longitude):
        """
        Démarre la séance :
        - Capture la position GPS du professeur
        - Génère un code unique
        - Définit l'heure d'expiration
        - Change le statut en ACTIVE
        """
        self.latitude_prof = latitude
        self.longitude_prof = longitude
        self.code_unique = generer_code_unique()
        self.heure_demarrage_reel = timezone.now()
        self.code_expire_a = timezone.now() + timezone.timedelta(
            minutes=self.duree_code_minutes
        )
        self.statut = self.Statut.ACTIVE
        self.save()

        # Initialiser tous les étudiants du cours comme ABSENT
        self._initialiser_absences()

    def cloturer(self):
        """Clôture la séance."""
        self.statut = self.Statut.CLOTUREE
        self.heure_cloture_reel = timezone.now()
        self.save()

    def regenerer_code(self):
        """Régénère un nouveau code et remet le timer."""
        self.code_unique = generer_code_unique()
        self.code_expire_a = timezone.now() + timezone.timedelta(
            minutes=self.duree_code_minutes
        )
        self.save()

    def _initialiser_absences(self):
        """
        Crée automatiquement un enregistrement ABSENT
        pour chaque étudiant inscrit à la matière.
        """
        from academic.models import InscriptionNiveau

        # Récupère tous les étudiants du niveau
        inscriptions = InscriptionNiveau.objects.filter(
            niveau=self.matiere.niveau,
            is_active=True,
            etudiant__statut='ACTIF'
        )

        # Crée une présence ABSENT pour chaque étudiant
        presences_a_creer = []
        for inscription in inscriptions:
            if not Presence.objects.filter(
                seance=self,
                etudiant=inscription.etudiant
            ).exists():
                presences_a_creer.append(
                    Presence(
                        seance=self,
                        etudiant=inscription.etudiant,
                        statut=Presence.Statut.ABSENT,
                        methode_pointage=Presence.Methode.AUTOMATIQUE
                    )
                )

        Presence.objects.bulk_create(presences_a_creer)

    @property
    def est_active(self):
        """Vérifie si la séance est active ET si le code n'est pas expiré."""
        if self.statut != self.Statut.ACTIVE:
            return False
        if self.code_expire_a and timezone.now() > self.code_expire_a:
            return False
        return True

    @property
    def code_expire_dans_secondes(self):
        """Retourne le nombre de secondes avant expiration du code."""
        if not self.code_expire_a:
            return 0
        delta = self.code_expire_a - timezone.now()
        return max(0, int(delta.total_seconds()))

    @property
    def nombre_presents(self):
        return self.presences.filter(statut=Presence.Statut.PRESENT).count()

    @property
    def nombre_absents(self):
        return self.presences.filter(statut=Presence.Statut.ABSENT).count()

    @property
    def nombre_retards(self):
        return self.presences.filter(statut=Presence.Statut.RETARD).count()

    @property
    def total_etudiants(self):
        return self.presences.count()

    class Meta:
        verbose_name = "Séance"
        verbose_name_plural = "Séances"
        ordering = ['-date_seance', '-heure_debut']

    def __str__(self):
        return f"{self.matiere.nom} - {self.date_seance} {self.heure_debut} [{self.statut}]"


# ─────────────────────────────────────────────────────────────────


class Presence(models.Model):
    """
    Représente la présence (ou l'absence) d'un étudiant à une séance.
    """

    class Statut(models.TextChoices):
        PRESENT = 'PRESENT', _('Présent')
        ABSENT = 'ABSENT', _('Absent')
        RETARD = 'RETARD', _('En retard')
        EXCUSE = 'EXCUSE', _('Excusé')

    class Methode(models.TextChoices):
        CODE_GPS = 'CODE_GPS', _('Code + GPS')
        MANUEL = 'MANUEL', _('Manuel (professeur)')
        AUTOMATIQUE = 'AUTOMATIQUE', _('Automatique (système)')

    seance = models.ForeignKey(
        Seance,
        on_delete=models.CASCADE,
        related_name='presences',
        verbose_name="Séance"
    )

    etudiant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='presences',
        verbose_name="Étudiant"
    )

    # ── Statut de présence ──
    statut = models.CharField(
        max_length=20,
        choices=Statut.choices,
        default=Statut.ABSENT,
        verbose_name="Statut"
    )

    # ── Horodatage ──
    heure_pointage = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Heure du pointage"
    )

    # ── Géolocalisation de l'étudiant ──
    latitude_etudiant = models.DecimalField(
        max_digits=10,
        decimal_places=8,
        null=True,
        blank=True,
        verbose_name="Latitude de l'étudiant"
    )

    longitude_etudiant = models.DecimalField(
        max_digits=11,
        decimal_places=8,
        null=True,
        blank=True,
        verbose_name="Longitude de l'étudiant"
    )

    distance_calculee = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Distance calculée (mètres)"
    )

    # ── Méthode et traçabilité ──
    methode_pointage = models.CharField(
        max_length=20,
        choices=Methode.choices,
        default=Methode.AUTOMATIQUE,
        verbose_name="Méthode de pointage"
    )

    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name="Adresse IP"
    )

    justification = models.TextField(
        null=True,
        blank=True,
        verbose_name="Justification (pour excuse ou modification manuelle)"
    )

    modifie_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='presences_modifiees',
        verbose_name="Modifié par"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Présence"
        verbose_name_plural = "Présences"
        ordering = ['-seance__date_seance', 'etudiant__last_name']
        unique_together = ['seance', 'etudiant']

    def __str__(self):
        return (
            f"{self.etudiant.nom_complet} | "
            f"{self.seance.matiere.nom} | "
            f"{self.seance.date_seance} | "
            f"{self.get_statut_display()}"
        )


# ─────────────────────────────────────────────────────────────────


class Notification(models.Model):
    """
    Système de notifications internes.
    """

    class Type(models.TextChoices):
        ALERTE_ABSENCE = 'ALERTE_ABSENCE', _('Alerte absence')
        CONVOCATION = 'CONVOCATION', _('Convocation')
        INFO = 'INFO', _('Information')
        RAPPEL = 'RAPPEL', _('Rappel')
        SEANCE_ACTIVE = 'SEANCE_ACTIVE', _('Séance active')

    destinataire = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name="Destinataire"
    )

    titre = models.CharField(
        max_length=200,
        verbose_name="Titre"
    )

    message = models.TextField(
        verbose_name="Message"
    )

    type_notification = models.CharField(
        max_length=30,
        choices=Type.choices,
        default=Type.INFO,
        verbose_name="Type"
    )

    lu = models.BooleanField(
        default=False,
        verbose_name="Lu"
    )

    lien = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        verbose_name="Lien de redirection"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.type_notification}] {self.titre} → {self.destinataire.nom_complet}"