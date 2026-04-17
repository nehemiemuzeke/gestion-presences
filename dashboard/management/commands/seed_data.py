"""
Commande pour créer des données de test.
Usage : python manage.py seed_data
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from accounts.models import User
from academic.models import (
    Departement, Filiere, Niveau,
    Matiere, InscriptionNiveau
)
from attendance.models import Seance, Presence
import random


class Command(BaseCommand):
    help = 'Crée des données de test pour la démonstration'

    def handle(self, *args, **kwargs):
        self.stdout.write('🌱 Création des données de test...\n')

        # ── 1. Département ──
        dept, _ = Departement.objects.get_or_create(
            code='DEPT-INFO',
            defaults={
                'nom'        : 'Département Informatique',
                'description': 'Département des sciences informatiques',
            }
        )
        self.stdout.write('  ✅ Département créé')

        # ── 2. Filière ──
        filiere, _ = Filiere.objects.get_or_create(
            code='LIC-INFO',
            defaults={
                'nom'        : 'Licence Informatique',
                'departement': dept,
            }
        )
        self.stdout.write('  ✅ Filière créée')

        # ── 3. Professeur ──
        prof, created = User.objects.get_or_create(
            username='prof.faustin',
            defaults={
                'first_name': 'Faustin',
                'last_name' : 'KOUAME',
                'email'     : 'faustin@presences.com',
                'matricule' : 'PROF-2024-001',
                'role'      : 'PROFESSEUR',
                'statut'    : 'ACTIF',
            }
        )
        if created:
            prof.set_password('Prof1234!')
            prof.save()
        self.stdout.write(
            '  ✅ Professeur → username: prof.faustin / password: Prof1234!'
        )

        # ── 4. Niveau ──
        niveau, _ = Niveau.objects.get_or_create(
            filiere          = filiere,
            nom              = 'L2',
            annee_academique = '2024-2025',
        )
        self.stdout.write('  ✅ Niveau L2 créé')

        # ── 5. Matières ──
        matiere1, _ = Matiere.objects.get_or_create(
            code='INF-ALGO-L2',
            defaults={
                'nom'           : 'Algorithmique',
                'niveau'        : niveau,
                'professeur'    : prof,
                'volume_horaire': 45,
                'seuil_absences': 3,
            }
        )
        matiere2, _ = Matiere.objects.get_or_create(
            code='INF-BDD-L2',
            defaults={
                'nom'           : 'Base de données',
                'niveau'        : niveau,
                'professeur'    : prof,
                'volume_horaire': 40,
                'seuil_absences': 3,
            }
        )
        self.stdout.write('  ✅ Matières créées')

        # ── 6. Étudiants ──
        etudiants_data = [
            ('Aya',     'KOUAME',  'ETU-2024-001'),
            ('Jean',    'BAMBA',   'ETU-2024-002'),
            ('Fatou',   'DIALLO',  'ETU-2024-003'),
            ('Ibrahim', 'TRAORE',  'ETU-2024-004'),
            ('Marie',   'DUPONT',  'ETU-2024-005'),
        ]

        etudiants = []
        for prenom, nom, mat in etudiants_data:
            username = mat.lower().replace('-', '.')
            etudiant, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'first_name': prenom,
                    'last_name' : nom,
                    'email'     : f'{username}@etudiant.com',
                    'matricule' : mat,
                    'role'      : 'ETUDIANT',
                    'statut'    : 'ACTIF',
                }
            )
            if created:
                etudiant.set_password('Etudiant1234!')
                etudiant.save()

            InscriptionNiveau.objects.get_or_create(
                etudiant=etudiant,
                niveau=niveau,
            )
            etudiants.append(etudiant)

        self.stdout.write(
            f'  ✅ {len(etudiants)} étudiants créés '
            f'→ password: Etudiant1234!'
        )

        # ── 7. Séances passées avec présences ──
        codes_utilises = set(
            Seance.objects.values_list('code_unique', flat=True)
        )

        dates_passees = [
            timezone.now().date() - timezone.timedelta(days=d)
            for d in [14, 11, 7, 4, 1]
        ]

        for i, date in enumerate(dates_passees):
            # Code unique qui n'existe pas encore
            code = f'SEED{i:02d}'
            if code in codes_utilises:
                continue

            seance = Seance.objects.create(
                matiere              = matiere1,
                professeur           = prof,
                date_seance          = date,
                heure_debut          = '08:00',
                heure_fin            = '10:00',
                code_unique          = code,
                statut               = 'CLOTUREE',
                latitude_prof        = 5.3600,
                longitude_prof       = -4.0083,
                heure_demarrage_reel = timezone.now(),
                heure_cloture_reel   = timezone.now(),
            )

            for etudiant in etudiants:
                # Ibrahim toujours absent → zone rouge
                if etudiant.matricule == 'ETU-2024-004':
                    statut   = 'ABSENT'
                    distance = None
                    heure    = None
                else:
                    statut = random.choice([
                        'PRESENT', 'PRESENT', 'PRESENT',
                        'ABSENT', 'RETARD'
                    ])
                    distance = (
                        round(random.uniform(2, 13), 1)
                        if statut != 'ABSENT' else None
                    )
                    heure = timezone.now() if statut != 'ABSENT' else None

                Presence.objects.create(
                    seance            = seance,
                    etudiant          = etudiant,
                    statut            = statut,
                    heure_pointage    = heure,
                    methode_pointage  = 'CODE_GPS',
                    distance_calculee = distance,
                )

        self.stdout.write('  ✅ 5 séances avec présences créées')

        # ── Résumé ──
        self.stdout.write('\n' + '=' * 55)
        self.stdout.write('🎉 DONNÉES DE TEST CRÉÉES AVEC SUCCÈS !')
        self.stdout.write('=' * 55)
        self.stdout.write('\n📋 COMPTES DISPONIBLES :')
        self.stdout.write(
            '  👨‍💼 Admin    → nehemie          / ton mot de passe'
        )
        self.stdout.write(
            '  👨‍🏫 Prof     → prof.faustin     / Prof1234!'
        )
        self.stdout.write(
            '  👨‍🎓 Étudiant → etu.2024.001     / Etudiant1234!'
        )
        self.stdout.write(
            '  👨‍🎓 Étudiant → etu.2024.002     / Etudiant1234!'
        )
        self.stdout.write(
            '  👨‍🎓 Étudiant → etu.2024.003     / Etudiant1234!'
        )
        self.stdout.write(
            '  ⚠️  Zone rouge → Ibrahim TRAORE  (5 absences sur 5)'
        )
        self.stdout.write('=' * 55 + '\n')