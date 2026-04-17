"""
Views Attendance
Gère : Séances, Pointage GPS, Présences
"""

import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.conf import settings

from accounts.views import role_required
from accounts.models import User
from academic.models import Matiere, InscriptionNiveau
from .models import Seance, Presence, Notification, calculer_distance_gps


# ═══════════════════════════════════════════════════════════
# VUES PROFESSEUR - GESTION DES SÉANCES
# ═══════════════════════════════════════════════════════════

@login_required
@role_required('PROFESSEUR')
def prof_seances_list(request):
    """
    Liste de toutes les séances du professeur.
    """
    seances = Seance.objects.filter(
        professeur=request.user
    ).select_related(
        'matiere__niveau__filiere'
    ).order_by('-date_seance', '-heure_debut')

    # Statistiques rapides
    total_seances  = seances.count()
    seances_active = seances.filter(statut='ACTIVE').first()
    seances_today  = seances.filter(
        date_seance=timezone.now().date()
    )

    nb_notifications = Notification.objects.filter(
        destinataire=request.user,
        lu=False
    ).count()

    context = {
        'seances'         : seances[:20],
        'total_seances'   : total_seances,
        'seance_active'   : seances_active,
        'seances_today'   : seances_today,
        'nb_notifications': nb_notifications,
        'nb_zone_rouge'   : 0,
    }
    return render(request, 'attendance/prof_seances_list.html', context)


@login_required
@role_required('PROFESSEUR')
def prof_seance_creer(request):
    """
    Créer une nouvelle séance.
    Le professeur sélectionne sa matière, la date et l'heure.
    """
    # Vérifier qu'il n'y a pas déjà une séance active
    seance_active = Seance.objects.filter(
        professeur=request.user,
        statut='ACTIVE'
    ).first()

    if seance_active:
        messages.warning(
            request,
            f"⚠️ Vous avez déjà une séance active : "
            f"{seance_active.matiere.nom}. "
            f"Veuillez la clôturer avant d'en créer une nouvelle."
        )
        return redirect('prof_seance_active', pk=seance_active.pk)

    if request.method == 'POST':
        matiere_id       = request.POST.get('matiere')
        date_seance      = request.POST.get('date_seance')
        heure_debut      = request.POST.get('heure_debut')
        heure_fin        = request.POST.get('heure_fin', '')
        salle            = request.POST.get('salle', '').strip()
        duree_code       = int(request.POST.get('duree_code', 10))

        errors = []
        if not matiere_id:
            errors.append("Veuillez sélectionner une matière.")
        if not date_seance:
            errors.append("La date est obligatoire.")
        if not heure_debut:
            errors.append("L'heure de début est obligatoire.")

        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            # Génère un code unique AVANT de démarrer
            from .models import generer_code_unique
            code = generer_code_unique()

            # S'assure que le code est vraiment unique
            while Seance.objects.filter(code_unique=code).exists():
                code = generer_code_unique()

            seance = Seance.objects.create(
                matiere_id        = matiere_id,
                professeur        = request.user,
                date_seance       = date_seance,
                heure_debut       = heure_debut,
                heure_fin         = heure_fin if heure_fin else None,
                salle             = salle,
                duree_code_minutes = duree_code,
                code_unique       = code,
                statut            = 'EN_ATTENTE',
            )

            messages.success(
                request,
                f"✅ Séance créée ! Vous pouvez maintenant la démarrer."
            )
            return redirect('prof_seance_demarrer', pk=seance.pk)

    # Mes matières assignées
    mes_matieres = Matiere.objects.filter(
        professeur=request.user,
        is_active=True
    ).select_related('niveau__filiere')

    nb_notifications = Notification.objects.filter(
        destinataire=request.user, lu=False
    ).count()

    context = {
        'mes_matieres'    : mes_matieres,
        'aujourd_hui'     : timezone.now().date(),
        'heure_actuelle'  : timezone.now().strftime('%H:%M'),
        'nb_notifications': nb_notifications,
        'nb_zone_rouge'   : 0,
    }
    return render(request, 'attendance/prof_seance_creer.html', context)


@login_required
@role_required('PROFESSEUR')
def prof_seance_demarrer(request, pk):
    """
    Démarrer une séance :
    - Capture le GPS du professeur
    - Active le code
    - Initialise toutes les absences
    """
    seance = get_object_or_404(
        Seance,
        pk=pk,
        professeur=request.user
    )

    if seance.statut == 'CLOTUREE':
        messages.error(request, "Cette séance est déjà clôturée.")
        return redirect('prof_seances_list')

    if seance.statut == 'ACTIVE':
        return redirect('prof_seance_active', pk=seance.pk)

    if request.method == 'POST':
        latitude  = request.POST.get('latitude')
        longitude = request.POST.get('longitude')

        if not latitude or not longitude:
            messages.error(
                request,
                "❌ Impossible de récupérer votre position GPS. "
                "Veuillez autoriser la géolocalisation."
            )
        else:
            try:
                # Démarre la séance avec la position GPS
                seance.demarrer(
                    latitude  = float(latitude),
                    longitude = float(longitude)
                )

                messages.success(
                    request,
                    f"🟢 Séance démarrée ! Code : {seance.code_unique}"
                )
                return redirect('prof_seance_active', pk=seance.pk)

            except Exception as e:
                messages.error(request, f"Erreur lors du démarrage : {str(e)}")

    nb_notifications = Notification.objects.filter(
        destinataire=request.user, lu=False
    ).count()

    context = {
        'seance'          : seance,
        'nb_notifications': nb_notifications,
        'nb_zone_rouge'   : 0,
    }
    return render(request, 'attendance/prof_seance_demarrer.html', context)


@login_required
@role_required('PROFESSEUR')
def prof_seance_active(request, pk):
    """
    Vue de la séance active.
    Affiche le code, le timer, et les présences en temps réel.
    """
    seance = get_object_or_404(
        Seance,
        pk=pk,
        professeur=request.user
    )

    if seance.statut == 'CLOTUREE':
        return redirect('prof_seance_detail', pk=seance.pk)

    # Liste des présences
    presences = Presence.objects.filter(
        seance=seance
    ).select_related('etudiant').order_by(
        '-heure_pointage', 'etudiant__last_name'
    )

    nb_notifications = Notification.objects.filter(
        destinataire=request.user, lu=False
    ).count()

    context = {
        'seance'            : seance,
        'presences'         : presences,
        'presents'          : presences.filter(statut='PRESENT'),
        'absents'           : presences.filter(statut='ABSENT'),
        'retards'           : presences.filter(statut='RETARD'),
        'nb_notifications'  : nb_notifications,
        'nb_zone_rouge'     : 0,
        'secondes_restantes': seance.code_expire_dans_secondes,
    }
    return render(request, 'attendance/prof_seance_active.html', context)


@login_required
@role_required('PROFESSEUR')
def prof_seance_cloturer(request, pk):
    """Clôturer une séance."""

    seance = get_object_or_404(
        Seance,
        pk=pk,
        professeur=request.user
    )

    if request.method == 'POST':
        seance.cloturer()
        messages.success(
            request,
            f"✅ Séance clôturée. "
            f"{seance.nombre_presents}/{seance.total_etudiants} présents."
        )
        return redirect('prof_seance_detail', pk=seance.pk)

    context = {'seance': seance}
    return render(request, 'attendance/prof_seance_cloturer.html', context)


@login_required
@role_required('PROFESSEUR')
def prof_seance_detail(request, pk):
    """Détail d'une séance clôturée."""

    seance = get_object_or_404(
        Seance,
        pk=pk,
        professeur=request.user
    )

    presences = Presence.objects.filter(
        seance=seance
    ).select_related('etudiant').order_by('etudiant__last_name')

    nb_notifications = Notification.objects.filter(
        destinataire=request.user, lu=False
    ).count()

    context = {
        'seance'          : seance,
        'presences'       : presences,
        'presents'        : presences.filter(statut='PRESENT'),
        'absents'         : presences.filter(statut='ABSENT'),
        'retards'         : presences.filter(statut='RETARD'),
        'excuses'         : presences.filter(statut='EXCUSE'),
        'nb_notifications': nb_notifications,
        'nb_zone_rouge'   : 0,
    }
    return render(request, 'attendance/prof_seance_detail.html', context)


@login_required
@role_required('PROFESSEUR')
def prof_regenerer_code(request, pk):
    """Régénérer le code de présence."""

    seance = get_object_or_404(
        Seance,
        pk=pk,
        professeur=request.user,
        statut='ACTIVE'
    )

    seance.regenerer_code()
    messages.success(
        request,
        f"🔄 Nouveau code généré : {seance.code_unique}"
    )
    return redirect('prof_seance_active', pk=seance.pk)


@login_required
@role_required('PROFESSEUR')
def prof_modifier_presence(request, presence_pk):
    """
    Modifier manuellement le statut de présence d'un étudiant.
    Uniquement pour le professeur responsable de la séance.
    """
    presence = get_object_or_404(Presence, pk=presence_pk)

    # Vérifie que le prof est bien responsable de cette séance
    if presence.seance.professeur != request.user:
        messages.error(request, "Vous n'êtes pas autorisé à modifier cette présence.")
        return redirect('prof_seances_list')

    if request.method == 'POST':
        nouveau_statut  = request.POST.get('statut')
        justification   = request.POST.get('justification', '').strip()

        statuts_valides = ['PRESENT', 'ABSENT', 'RETARD', 'EXCUSE']
        if nouveau_statut not in statuts_valides:
            messages.error(request, "Statut invalide.")
        else:
            presence.statut          = nouveau_statut
            presence.justification   = justification
            presence.methode_pointage = 'MANUEL'
            presence.modifie_par     = request.user

            if nouveau_statut == 'PRESENT' and not presence.heure_pointage:
                presence.heure_pointage = timezone.now()

            presence.save()
            messages.success(
                request,
                f"✅ Présence de {presence.etudiant.nom_complet} "
                f"modifiée → {presence.get_statut_display()}"
            )

    return redirect('prof_seance_detail', pk=presence.seance.pk)


# ═══════════════════════════════════════════════════════════
# API - POINTAGE ÉTUDIANT (JSON)
# ═══════════════════════════════════════════════════════════

@login_required
@require_http_methods(["POST"])
def api_pointer_presence(request):
    """
    API de pointage de présence.

    Reçoit : { code, latitude, longitude }
    Retourne : { success, message, distance, statut }

    Vérifications :
    1. Le code est-il valide et actif ?
    2. L'étudiant est-il inscrit à ce cours ?
    3. L'étudiant n'a-t-il pas déjà pointé ?
    4. La distance GPS est-elle ≤ 15m ?
    """
    try:
        data      = json.loads(request.body)
        code      = data.get('code', '').strip().upper()
        latitude  = data.get('latitude')
        longitude = data.get('longitude')

        # ── Validation des données ──
        if not code:
            return JsonResponse({
                'success': False,
                'message': "Veuillez entrer le code de présence."
            })

        if not latitude or not longitude:
            return JsonResponse({
                'success': False,
                'message': "Position GPS non disponible. "
                           "Veuillez autoriser la géolocalisation."
            })

        # ── Vérification 1 : Le code existe et est actif ──
        try:
            seance = Seance.objects.get(code_unique=code)
        except Seance.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': "❌ Code invalide. Vérifiez le code saisi."
            })

        if not seance.est_active:
            if seance.statut == 'CLOTUREE':
                return JsonResponse({
                    'success': False,
                    'message': "❌ Cette séance est terminée."
                })
            return JsonResponse({
                'success': False,
                'message': "❌ Le code a expiré. "
                           "Demandez un nouveau code au professeur."
            })

        # ── Vérification 2 : L'étudiant est-il inscrit ? ──
        est_inscrit = InscriptionNiveau.objects.filter(
            etudiant  = request.user,
            niveau    = seance.matiere.niveau,
            is_active = True
        ).exists()

        if not est_inscrit:
            return JsonResponse({
                'success': False,
                'message': "❌ Vous n'êtes pas inscrit à ce cours."
            })

        # ── Vérification 3 : Déjà pointé ? ──
        presence = Presence.objects.filter(
            seance   = seance,
            etudiant = request.user
        ).first()

        if presence and presence.statut in ['PRESENT', 'RETARD']:
            return JsonResponse({
                'success': False,
                'message': f"✅ Vous avez déjà pointé votre présence "
                           f"({presence.get_statut_display()})."
            })

        # ── Vérification 4 : Distance GPS ──
        if not seance.latitude_prof or not seance.longitude_prof:
            return JsonResponse({
                'success': False,
                'message': "❌ Position du professeur non disponible."
            })

        distance = calculer_distance_gps(
            lat1 = seance.latitude_prof,
            lon1 = seance.longitude_prof,
            lat2 = float(latitude),
            lon2 = float(longitude)
        )

        rayon_autorise = seance.rayon_metres or getattr(
            settings, 'GPS_RADIUS_METERS', 15
        )

        if distance > rayon_autorise:
            return JsonResponse({
                'success' : False,
                'message' : f"❌ Vous êtes trop loin ! "
                            f"Distance : {distance:.1f}m "
                            f"(max autorisé : {rayon_autorise}m). "
                            f"Rapprochez-vous du professeur.",
                'distance': round(distance, 1),
            })

        # ── Pointage validé ! ──
        # Détermine si c'est un retard
        maintenant    = timezone.now()
        seuil_retard  = getattr(settings, 'LATE_THRESHOLD_MINUTES', 15)
        heure_limite  = timezone.datetime.combine(
            seance.date_seance,
            seance.heure_debut,
            tzinfo=maintenant.tzinfo
        )
        est_en_retard = (
            maintenant > heure_limite + timezone.timedelta(minutes=seuil_retard)
        )

        statut_final = 'RETARD' if est_en_retard else 'PRESENT'

        # Met à jour ou crée la présence
        ip_address = (
            request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip()
            or request.META.get('REMOTE_ADDR', '')
        )

        if presence:
            # Mise à jour de la présence existante
            presence.statut              = statut_final
            presence.heure_pointage      = maintenant
            presence.latitude_etudiant   = float(latitude)
            presence.longitude_etudiant  = float(longitude)
            presence.distance_calculee   = distance
            presence.methode_pointage    = 'CODE_GPS'
            presence.ip_address          = ip_address
            presence.save()
        else:
            # Création d'une nouvelle présence
            presence = Presence.objects.create(
                seance              = seance,
                etudiant            = request.user,
                statut              = statut_final,
                heure_pointage      = maintenant,
                latitude_etudiant   = float(latitude),
                longitude_etudiant  = float(longitude),
                distance_calculee   = distance,
                methode_pointage    = 'CODE_GPS',
                ip_address          = ip_address,
            )

        # ── Notification au professeur ──
        _notifier_professeur(seance, request.user, statut_final)

        # ── Vérification du seuil d'absences ──
        _verifier_seuil_absences(request.user, seance.matiere)

        # ── Réponse succès ──
        message_statut = (
            "⏰ Présence enregistrée avec retard."
            if statut_final == 'RETARD'
            else "✅ Présence validée avec succès !"
        )

        return JsonResponse({
            'success'  : True,
            'message'  : message_statut,
            'distance' : round(distance, 1),
            'statut'   : statut_final,
            'heure'    : maintenant.strftime('%H:%M'),
            'matiere'  : seance.matiere.nom,
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': "Données invalides."
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f"Une erreur est survenue : {str(e)}"
        })


@login_required
def api_seance_status(request, pk):
    """
    API pour récupérer le statut d'une séance en temps réel.
    Utilisé par le JavaScript du professeur pour rafraîchir la liste.
    """
    seance = get_object_or_404(Seance, pk=pk)

    presences = Presence.objects.filter(
        seance=seance
    ).select_related('etudiant')

    presents_data = []
    for p in presences.filter(statut__in=['PRESENT', 'RETARD']):
        presents_data.append({
            'nom'      : p.etudiant.nom_complet,
            'matricule': p.etudiant.matricule or '',
            'statut'   : p.statut,
            'heure'    : p.heure_pointage.strftime('%H:%M') if p.heure_pointage else '',
            'distance' : float(p.distance_calculee) if p.distance_calculee else 0,
        })

    return JsonResponse({
        'statut'          : seance.statut,
        'est_active'      : seance.est_active,
        'secondes_restantes': seance.code_expire_dans_secondes,
        'code_unique'     : seance.code_unique,
        'nb_presents'     : seance.nombre_presents,
        'nb_absents'      : seance.nombre_absents,
        'nb_retards'      : seance.nombre_retards,
        'total'           : seance.total_etudiants,
        'presents'        : presents_data,
    })


# ═══════════════════════════════════════════════════════════
# VUES ÉTUDIANT - POINTAGE
# ═══════════════════════════════════════════════════════════

@login_required
@role_required('ETUDIANT')
def etudiant_pointer(request):
    """
    Page de pointage pour l'étudiant.
    L'étudiant saisit le code et sa position GPS est vérifiée.
    """
    nb_notifications = Notification.objects.filter(
        destinataire=request.user,
        lu=False
    ).count()

    context = {
        'nb_notifications': nb_notifications,
    }
    return render(request, 'attendance/etudiant_pointer.html', context)


@login_required
@role_required('ETUDIANT')
def etudiant_historique(request):
    """
    Historique complet des présences de l'étudiant.
    """
    presences = Presence.objects.filter(
        etudiant=request.user
    ).select_related(
        'seance__matiere__niveau__filiere'
    ).order_by('-seance__date_seance')

    # Filtrage par matière
    matiere_filter = request.GET.get('matiere', '')
    if matiere_filter:
        presences = presences.filter(seance__matiere_id=matiere_filter)

    # Mes matières pour le filtre
    from academic.models import Matiere
    mes_matieres = Matiere.objects.filter(
        niveau__inscriptions__etudiant=request.user,
        niveau__inscriptions__is_active=True,
    )

    nb_notifications = Notification.objects.filter(
        destinataire=request.user, lu=False
    ).count()

    context = {
        'presences'       : presences,
        'mes_matieres'    : mes_matieres,
        'matiere_filter'  : matiere_filter,
        'nb_notifications': nb_notifications,
    }
    return render(request, 'attendance/etudiant_historique.html', context)


# ═══════════════════════════════════════════════════════════
# FONCTIONS UTILITAIRES PRIVÉES
# ═══════════════════════════════════════════════════════════

def _notifier_professeur(seance, etudiant, statut):
    """Envoie une notification au professeur quand un étudiant pointe."""
    try:
        Notification.objects.create(
            destinataire      = seance.professeur,
            titre             = f"Pointage : {etudiant.nom_complet}",
            message           = (
                f"{etudiant.nom_complet} a pointé sa présence "
                f"({statut}) pour {seance.matiere.nom}."
            ),
            type_notification = 'INFO',
            lien              = f"/attendance/seance/{seance.pk}/active/",
        )
    except Exception:
        pass  # Ne bloque pas le pointage si la notif échoue


def _verifier_seuil_absences(etudiant, matiere):
    """
    Vérifie si l'étudiant a dépassé le seuil d'absences.
    Si oui, crée une notification d'alerte.
    """
    try:
        total_seances = Presence.objects.filter(
            etudiant         = etudiant,
            seance__matiere  = matiere
        ).count()

        nb_absences = Presence.objects.filter(
            etudiant         = etudiant,
            seance__matiere  = matiere,
            statut           = 'ABSENT'
        ).count()

        seuil = matiere.seuil_absences

        # Alerte à 1 absence du seuil
        if nb_absences == seuil - 1:
            Notification.objects.create(
                destinataire      = etudiant,
                titre             = f"⚠️ Attention : {matiere.nom}",
                message           = (
                    f"Vous avez {nb_absences} absence(s) en {matiere.nom}. "
                    f"Encore 1 absence et vous serez convoqué !"
                ),
                type_notification = 'ALERTE_ABSENCE',
            )

        # Zone rouge : seuil dépassé
        elif nb_absences >= seuil:
            # Vérifie si une notif de convocation existe déjà
            deja_notifie = Notification.objects.filter(
                destinataire      = etudiant,
                type_notification = 'CONVOCATION',
                titre__contains   = matiere.nom,
            ).exists()

            if not deja_notifie:
                Notification.objects.create(
                    destinataire      = etudiant,
                    titre             = f"🔴 Convocation : {matiere.nom}",
                    message           = (
                        f"Vous avez dépassé le seuil d'absences "
                        f"({nb_absences}/{seuil}) en {matiere.nom}. "
                        f"Vous devez vous présenter à l'administration."
                    ),
                    type_notification = 'CONVOCATION',
                )

                # Notifie aussi le professeur
                if matiere.professeur:
                    Notification.objects.create(
                        destinataire      = matiere.professeur,
                        titre             = f"🔴 Zone rouge : {etudiant.nom_complet}",
                        message           = (
                            f"{etudiant.nom_complet} a dépassé le seuil "
                            f"d'absences ({nb_absences}/{seuil}) "
                            f"en {matiere.nom}."
                        ),
                        type_notification = 'ALERTE_ABSENCE',
                    )
    except Exception:
        pass  # Ne bloque jamais le pointage

# ═══════════════════════════════════════════════════════════
# VUES NOTIFICATIONS
# ═══════════════════════════════════════════════════════════

@login_required
def notifications_list(request):
    """Page de toutes les notifications."""

    notifications = Notification.objects.filter(
        destinataire=request.user
    ).order_by('-created_at')

    # Marquer toutes comme lues
    notifications.filter(lu=False).update(lu=True)

    # Layout selon le rôle
    if request.user.role == 'ADMIN':
        template = 'attendance/notifications_admin.html'
    elif request.user.role == 'PROFESSEUR':
        template = 'attendance/notifications_prof.html'
    else:
        template = 'attendance/notifications_etudiant.html'

    context = {
        'notifications'   : notifications,
        'nb_notifications': 0,  # déjà marquées lues
        'nb_zone_rouge'   : 0,
    }
    return render(request, template, context)


@login_required
def api_notifications(request):
    """API JSON pour récupérer les notifications."""

    notifications = Notification.objects.filter(
        destinataire=request.user,
        lu=False
    ).order_by('-created_at')[:10]

    data = []
    for n in notifications:
        data.append({
            'id'     : n.id,
            'titre'  : n.titre,
            'message': n.message,
            'type'   : n.type_notification,
            'lien'   : n.lien or '#',
            'date'   : n.created_at.strftime('%d/%m %H:%M'),
        })

    return JsonResponse({
        'notifications': data,
        'total'        : notifications.count(),
    })


@login_required
def api_marquer_notification_lue(request, pk):
    """Marquer une notification comme lue."""

    notification = get_object_or_404(
        Notification,
        pk=pk,
        destinataire=request.user
    )
    notification.lu = True
    notification.save()

    return JsonResponse({'success': True})


@login_required
def api_marquer_toutes_lues(request):
    """Marquer toutes les notifications comme lues."""

    Notification.objects.filter(
        destinataire=request.user,
        lu=False
    ).update(lu=True)

    return JsonResponse({'success': True})