"""
Views du Dashboard
"""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from accounts.views import role_required
from accounts.models import User
from academic.models import Departement, Filiere, Niveau, Matiere, InscriptionNiveau
from attendance.models import Seance, Presence, Notification
from django.utils import timezone


# ─────────────────────────────────────────
# REDIRECTION ACCUEIL
# ─────────────────────────────────────────

def accueil_redirect(request):
    """Redirige vers la bonne page selon le statut."""
    if request.user.is_authenticated:
        if request.user.role == 'ADMIN':
            return redirect('admin_dashboard')
        elif request.user.role == 'PROFESSEUR':
            return redirect('prof_dashboard')
        elif request.user.role == 'ETUDIANT':
            return redirect('etudiant_dashboard')
    return redirect('login')


# ─────────────────────────────────────────
# PAGE PLACEHOLDER (En construction)
# ─────────────────────────────────────────

@login_required
def placeholder(request):
    """Page temporaire - sera remplacée dans les prochains blocs."""
    return render(request, 'dashboard/placeholder.html')


# ─────────────────────────────────────────
# DASHBOARD ADMIN
# ─────────────────────────────────────────

@login_required
@role_required('ADMIN')
def admin_dashboard(request):
    """Dashboard principal de l'administrateur."""

    aujourd_hui = timezone.now().date()

    # ── Statistiques générales ──
    total_etudiants = User.objects.filter(
        role='ETUDIANT', statut='ACTIF'
    ).count()

    total_professeurs = User.objects.filter(
        role='PROFESSEUR', statut='ACTIF'
    ).count()

    total_matieres = Matiere.objects.filter(is_active=True).count()

    total_seances = Seance.objects.count()

    # ── Séances d'aujourd'hui ──
    seances_aujourd_hui = Seance.objects.filter(
        date_seance=aujourd_hui
    ).select_related('matiere', 'professeur').order_by('heure_debut')

    # ── Séances actives en ce moment ──
    seances_actives = Seance.objects.filter(
        statut='ACTIVE'
    ).select_related('matiere', 'professeur')

    # ── Étudiants en zone rouge ──
    etudiants_zone_rouge = _get_etudiants_zone_rouge()
    nb_zone_rouge = len(etudiants_zone_rouge)

    # ── Notifications non lues ──
    nb_notifications = Notification.objects.filter(
        destinataire=request.user,
        lu=False
    ).count()

    # ── Dernières séances clôturées ──
    dernieres_seances = Seance.objects.filter(
        statut='CLOTUREE'
    ).order_by('-date_seance', '-heure_debut')[:5].select_related(
        'matiere', 'professeur'
    )

    context = {
        'total_etudiants': total_etudiants,
        'total_professeurs': total_professeurs,
        'total_matieres': total_matieres,
        'total_seances': total_seances,
        'nb_zone_rouge': nb_zone_rouge,
        'nb_notifications': nb_notifications,
        'seances_aujourd_hui': seances_aujourd_hui,
        'seances_actives': seances_actives,
        'etudiants_zone_rouge': etudiants_zone_rouge[:5],
        'dernieres_seances': dernieres_seances,
        'aujourd_hui': aujourd_hui,
    }

    return render(request, 'dashboard/admin_dashboard.html', context)


# ─────────────────────────────────────────
# DASHBOARD PROFESSEUR
# ─────────────────────────────────────────

@login_required
@role_required('PROFESSEUR')
def prof_dashboard(request):
    """Dashboard du professeur."""

    aujourd_hui = timezone.now().date()

    # Mes matières
    mes_matieres = Matiere.objects.filter(
        professeur=request.user,
        is_active=True
    ).select_related('niveau__filiere')

    # Mes séances d'aujourd'hui
    mes_seances_aujourd_hui = Seance.objects.filter(
        professeur=request.user,
        date_seance=aujourd_hui
    ).select_related('matiere').order_by('heure_debut')

    # Ma séance active
    seance_active = Seance.objects.filter(
        professeur=request.user,
        statut='ACTIVE'
    ).select_related('matiere').first()

    # Total de mes séances
    total_mes_seances = Seance.objects.filter(
        professeur=request.user
    ).count()

    # Étudiants en zone rouge dans mes cours
    etudiants_rouge_mes_cours = _get_etudiants_zone_rouge(
        professeur=request.user
    )

    # Notifications non lues
    nb_notifications = Notification.objects.filter(
        destinataire=request.user,
        lu=False
    ).count()

    context = {
        'mes_matieres': mes_matieres,
        'mes_seances_aujourd_hui': mes_seances_aujourd_hui,
        'seance_active': seance_active,
        'total_mes_seances': total_mes_seances,
        'etudiants_rouge_mes_cours': etudiants_rouge_mes_cours,
        'nb_zone_rouge': len(etudiants_rouge_mes_cours),
        'nb_notifications': nb_notifications,
        'aujourd_hui': aujourd_hui,
    }

    return render(request, 'dashboard/prof_dashboard.html', context)


# ─────────────────────────────────────────
# DASHBOARD ÉTUDIANT
# ─────────────────────────────────────────

@login_required
@role_required('ETUDIANT')
def etudiant_dashboard(request):
    """Dashboard de l'étudiant."""

    # Mes inscriptions
    mes_inscriptions = InscriptionNiveau.objects.filter(
        etudiant=request.user,
        is_active=True
    ).select_related('niveau__filiere__departement')

    # Mes présences
    mes_presences = Presence.objects.filter(
        etudiant=request.user
    ).select_related('seance__matiere')

    total_seances = mes_presences.count()
    total_present = mes_presences.filter(statut='PRESENT').count()
    total_absent  = mes_presences.filter(statut='ABSENT').count()
    total_retard  = mes_presences.filter(statut='RETARD').count()

    # Pourcentages
    pct_presence = round((total_present / total_seances * 100), 1) if total_seances > 0 else 0
    pct_absence  = round((total_absent  / total_seances * 100), 1) if total_seances > 0 else 0
    pct_retard   = round((total_retard  / total_seances * 100), 1) if total_seances > 0 else 0

    # Statut global
    statut_global = _get_statut_etudiant(request.user)

    # Stats par matière
    stats_par_matiere = _get_stats_par_matiere(request.user)

    # Dernières présences
    dernieres_presences = mes_presences.order_by(
        '-seance__date_seance'
    )[:10]

    # Notifications
    nb_notifications = Notification.objects.filter(
        destinataire=request.user,
        lu=False
    ).count()

    context = {
        'mes_inscriptions'   : mes_inscriptions,
        'total_seances'      : total_seances,
        'total_present'      : total_present,
        'total_absent'       : total_absent,
        'total_retard'       : total_retard,
        'pct_presence'       : pct_presence,
        'pct_absence'        : pct_absence,
        'pct_retard'         : pct_retard,
        'statut_global'      : statut_global,
        'stats_par_matiere'  : stats_par_matiere,
        'dernieres_presences': dernieres_presences,
        'nb_notifications'   : nb_notifications,
    }

    return render(request, 'dashboard/etudiant_dashboard.html', context)


# ─────────────────────────────────────────
# FONCTIONS UTILITAIRES PRIVÉES
# ─────────────────────────────────────────

def _get_etudiants_zone_rouge(professeur=None):
    """
    Retourne la liste des étudiants qui ont dépassé
    le seuil d'absences dans au moins une matière.
    """
    resultats = []

    matieres_query = Matiere.objects.filter(is_active=True)
    if professeur:
        matieres_query = matieres_query.filter(professeur=professeur)

    for matiere in matieres_query:
        etudiants = User.objects.filter(
            inscriptions__niveau=matiere.niveau,
            inscriptions__is_active=True,
            role='ETUDIANT',
            statut='ACTIF'
        )

        for etudiant in etudiants:
            total_seances = Presence.objects.filter(
                etudiant=etudiant,
                seance__matiere=matiere
            ).count()

            nb_absences = Presence.objects.filter(
                etudiant=etudiant,
                seance__matiere=matiere,
                statut='ABSENT'
            ).count()

            if nb_absences >= matiere.seuil_absences and total_seances > 0:
                pct_absence = round((nb_absences / total_seances * 100), 1)
                resultats.append({
                    'etudiant'    : etudiant,
                    'matiere'     : matiere,
                    'nb_absences' : nb_absences,
                    'total_seances': total_seances,
                    'pct_absence' : pct_absence,
                    'seuil'       : matiere.seuil_absences,
                })

    return resultats


def _get_statut_etudiant(etudiant):
    """
    Détermine le statut global d'un étudiant.
    Retourne : 'VERT', 'ORANGE' ou 'ROUGE'
    """
    matieres = Matiere.objects.filter(
        niveau__inscriptions__etudiant=etudiant,
        niveau__inscriptions__is_active=True,
        is_active=True
    )

    statut = 'VERT'

    for matiere in matieres:
        nb_absences = Presence.objects.filter(
            etudiant=etudiant,
            seance__matiere=matiere,
            statut='ABSENT'
        ).count()

        if nb_absences >= matiere.seuil_absences:
            return 'ROUGE'
        elif nb_absences >= matiere.seuil_absences - 1:
            statut = 'ORANGE'

    return statut


def _get_stats_par_matiere(etudiant):
    """Retourne les statistiques de présence par matière."""
    matieres = Matiere.objects.filter(
        niveau__inscriptions__etudiant=etudiant,
        niveau__inscriptions__is_active=True,
        is_active=True
    ).select_related('niveau__filiere')

    stats = []
    for matiere in matieres:
        presences = Presence.objects.filter(
            etudiant=etudiant,
            seance__matiere=matiere
        )
        total   = presences.count()
        presents = presences.filter(statut='PRESENT').count()
        absents  = presences.filter(statut='ABSENT').count()
        retards  = presences.filter(statut='RETARD').count()

        pct = round((presents / total * 100), 1) if total > 0 else 0

        if absents >= matiere.seuil_absences:
            statut = 'ROUGE'
        elif absents >= matiere.seuil_absences - 1:
            statut = 'ORANGE'
        else:
            statut = 'VERT'

        stats.append({
            'matiere'    : matiere,
            'total'      : total,
            'presents'   : presents,
            'absents'    : absents,
            'retards'    : retards,
            'pct_presence': pct,
            'statut'     : statut,
        })

    return stats