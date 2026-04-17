"""
Views d'Authentification et Gestion des Utilisateurs
Gère : Login, Logout, Profil, Professeurs, Étudiants
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import never_cache
from django.db.models import Q, Count
from .models import User


# ─────────────────────────────────────────
# DÉCORATEURS PERSONNALISÉS
# ─────────────────────────────────────────

def role_required(*roles):
    """
    Décorateur qui vérifie que l'utilisateur a le bon rôle.
    Usage : @role_required('ADMIN') ou @role_required('ADMIN', 'PROFESSEUR')
    """
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.warning(request, "Veuillez vous connecter.")
                return redirect('login')
            if request.user.role not in roles:
                messages.error(
                    request,
                    "Vous n'avez pas les permissions pour accéder à cette page."
                )
                return redirect('accueil')
            return view_func(request, *args, **kwargs)
        wrapper.__name__ = view_func.__name__
        return wrapper
    return decorator


# ─────────────────────────────────────────
# AUTHENTIFICATION
# ─────────────────────────────────────────

@never_cache
@require_http_methods(["GET", "POST"])
def login_view(request):
    """
    Page de connexion.
    Redirige vers le bon dashboard selon le rôle.
    """

    # Si déjà connecté → redirige
    if request.user.is_authenticated:
        return _redirect_by_role(request.user)

    error = None

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        if not username or not password:
            error = "Veuillez remplir tous les champs."
        else:
            user = authenticate(request, username=username, password=password)

            if user is not None:
                if user.statut == 'ACTIF':
                    login(request, user)
                    messages.success(
                        request,
                        f"Bienvenue, {user.nom_complet} ! 👋"
                    )
                    next_url = request.GET.get('next')
                    if next_url:
                        return redirect(next_url)
                    return _redirect_by_role(user)
                else:
                    error = "Votre compte est suspendu ou inactif. Contactez l'administrateur."
            else:
                error = "Identifiant ou mot de passe incorrect."

    return render(request, 'accounts/login.html', {'error': error})


@login_required
def logout_view(request):
    """Déconnexion de l'utilisateur."""
    nom = request.user.nom_complet
    logout(request)
    messages.info(request, f"Au revoir, {nom} ! À bientôt. 👋")
    return redirect('login')


@login_required
def profil_view(request):
    """Page de profil de l'utilisateur connecté."""

    if request.method == 'POST':
        user           = request.user
        user.first_name = request.POST.get('first_name', user.first_name).strip()
        user.last_name  = request.POST.get('last_name', user.last_name).strip()
        user.email      = request.POST.get('email', user.email).strip()
        user.telephone  = request.POST.get('telephone', user.telephone)
        user.adresse    = request.POST.get('adresse', user.adresse)

        if request.FILES.get('photo'):
            user.photo = request.FILES['photo']

        new_password     = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        current_password = request.POST.get('current_password')

        if new_password:
            if not current_password:
                messages.error(request, "Veuillez entrer votre mot de passe actuel.")
                return redirect('profil')
            if not request.user.check_password(current_password):
                messages.error(request, "Mot de passe actuel incorrect.")
                return redirect('profil')
            if new_password != confirm_password:
                messages.error(request, "Les nouveaux mots de passe ne correspondent pas.")
                return redirect('profil')
            if len(new_password) < 8:
                messages.error(request, "Le mot de passe doit contenir au moins 8 caractères.")
                return redirect('profil')
            user.set_password(new_password)
            messages.success(request, "Mot de passe modifié avec succès.")

        user.save()
        messages.success(request, "Profil mis à jour avec succès. ✅")
        return redirect('profil')

    return render(request, 'accounts/profil.html', {'user': request.user})


# ─────────────────────────────────────────
# FONCTION UTILITAIRE
# ─────────────────────────────────────────

def _redirect_by_role(user):
    """Redirige l'utilisateur vers son dashboard selon son rôle."""
    redirections = {
        'ADMIN'      : 'admin_dashboard',
        'PROFESSEUR' : 'prof_dashboard',
        'ETUDIANT'   : 'etudiant_dashboard',
    }
    url_name = redirections.get(user.role, 'login')
    return redirect(url_name)


# ═══════════════════════════════════════════════════════════
# GESTION DES PROFESSEURS (Admin)
# ═══════════════════════════════════════════════════════════

@login_required
@role_required('ADMIN')
def professeurs_list(request):
    """Liste de tous les professeurs."""

    search = request.GET.get('search', '')

    professeurs = User.objects.filter(
        role='PROFESSEUR'
    ).annotate(
        nb_matieres=Count('matieres_enseignees')
    ).order_by('last_name', 'first_name')

    if search:
        professeurs = professeurs.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search)  |
            Q(email__icontains=search)      |
            Q(matricule__icontains=search)
        )

    context = {
        'professeurs'     : professeurs,
        'search'          : search,
        'total'           : professeurs.count(),
        'nb_notifications': 0,
        'nb_zone_rouge'   : 0,
    }
    return render(request, 'accounts/professeurs_list.html', context)


@login_required
@role_required('ADMIN')
def professeur_create(request):
    """Créer un nouveau professeur."""

    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name  = request.POST.get('last_name', '').strip()
        email      = request.POST.get('email', '').strip()
        matricule  = request.POST.get('matricule', '').strip()
        telephone  = request.POST.get('telephone', '').strip()
        password   = request.POST.get('password', '')

        errors = []
        if not first_name:
            errors.append("Le prénom est obligatoire.")
        if not last_name:
            errors.append("Le nom est obligatoire.")
        if not email:
            errors.append("L'email est obligatoire.")
        if not matricule:
            errors.append("Le matricule est obligatoire.")
        if not password:
            errors.append("Le mot de passe est obligatoire.")
        if len(password) < 8:
            errors.append("Le mot de passe doit contenir au moins 8 caractères.")
        if User.objects.filter(email=email).exists():
            errors.append(f"L'email '{email}' est déjà utilisé.")
        if User.objects.filter(matricule=matricule).exists():
            errors.append(f"Le matricule '{matricule}' existe déjà.")

        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            user = User.objects.create_user(
                username   = matricule,
                first_name = first_name,
                last_name  = last_name,
                email      = email,
                matricule  = matricule,
                telephone  = telephone,
                password   = password,
                role       = 'PROFESSEUR',
                statut     = 'ACTIF',
            )
            messages.success(
                request,
                f"✅ Professeur '{user.nom_complet}' créé avec succès !"
            )
            return redirect('admin_professeurs')

    context = {
        'nb_notifications': 0,
        'nb_zone_rouge'   : 0,
    }
    return render(request, 'accounts/professeur_form.html', context)


@login_required
@role_required('ADMIN')
def professeur_edit(request, pk):
    """Modifier un professeur."""

    professeur = get_object_or_404(User, pk=pk, role='PROFESSEUR')

    if request.method == 'POST':
        first_name   = request.POST.get('first_name', '').strip()
        last_name    = request.POST.get('last_name', '').strip()
        email        = request.POST.get('email', '').strip()
        matricule    = request.POST.get('matricule', '').strip()
        telephone    = request.POST.get('telephone', '').strip()
        statut       = request.POST.get('statut', 'ACTIF')
        new_password = request.POST.get('new_password', '').strip()

        errors = []
        if not first_name:
            errors.append("Le prénom est obligatoire.")
        if not last_name:
            errors.append("Le nom est obligatoire.")
        if not email:
            errors.append("L'email est obligatoire.")
        if User.objects.filter(email=email).exclude(pk=pk).exists():
            errors.append(f"L'email '{email}' est déjà utilisé.")
        if User.objects.filter(matricule=matricule).exclude(pk=pk).exists():
            errors.append(f"Le matricule '{matricule}' existe déjà.")

        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            professeur.first_name = first_name
            professeur.last_name  = last_name
            professeur.email      = email
            professeur.matricule  = matricule
            professeur.username   = matricule
            professeur.telephone  = telephone
            professeur.statut     = statut

            if new_password:
                if len(new_password) < 8:
                    messages.error(
                        request,
                        "Le mot de passe doit contenir au moins 8 caractères."
                    )
                    return redirect('professeur_edit', pk=pk)
                professeur.set_password(new_password)

            professeur.save()
            messages.success(
                request,
                f"✅ Professeur '{professeur.nom_complet}' modifié !"
            )
            return redirect('admin_professeurs')

    context = {
        'professeur'      : professeur,
        'statut_choices'  : User.Statut.choices,
        'nb_notifications': 0,
        'nb_zone_rouge'   : 0,
    }
    return render(request, 'accounts/professeur_form.html', context)


@login_required
@role_required('ADMIN')
def professeur_delete(request, pk):
    """Supprimer un professeur."""

    professeur = get_object_or_404(User, pk=pk, role='PROFESSEUR')

    if request.method == 'POST':
        nom = professeur.nom_complet
        professeur.delete()
        messages.success(request, f"🗑️ Professeur '{nom}' supprimé.")
        return redirect('admin_professeurs')

    context = {
        'objet'           : professeur,
        'type'            : 'professeur',
        'retour_url'      : 'admin_professeurs',
        'nb_notifications': 0,
        'nb_zone_rouge'   : 0,
    }
    return render(request, 'components/confirm_delete.html', context)


# ═══════════════════════════════════════════════════════════
# GESTION DES ÉTUDIANTS (Admin)
# ═══════════════════════════════════════════════════════════

@login_required
@role_required('ADMIN')
def etudiants_list(request):
    """Liste de tous les étudiants."""

    from academic.models import Niveau, InscriptionNiveau

    search      = request.GET.get('search', '')
    niv_filter  = request.GET.get('niveau', '')
    stat_filter = request.GET.get('statut', '')

    etudiants = User.objects.filter(
        role='ETUDIANT'
    ).order_by('last_name', 'first_name')

    if search:
        etudiants = etudiants.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search)  |
            Q(email__icontains=search)      |
            Q(matricule__icontains=search)
        )

    if niv_filter:
        etudiants = etudiants.filter(
            inscriptions__niveau_id=niv_filter,
            inscriptions__is_active=True
        )

    if stat_filter:
        etudiants = etudiants.filter(statut=stat_filter)

    # Calcul du statut zone pour chaque étudiant
    etudiants_data = []
    for etudiant in etudiants:
        from dashboard.views import _get_statut_etudiant
        statut_zone = _get_statut_etudiant(etudiant)
        etudiants_data.append({
            'etudiant'    : etudiant,
            'statut_zone' : statut_zone,
            'niveau'      : etudiant.inscriptions.filter(
                is_active=True
            ).select_related('niveau__filiere').first(),
        })

    niveaux = Niveau.objects.filter(
        is_active=True
    ).select_related('filiere')

    context = {
        'etudiants_data'  : etudiants_data,
        'niveaux'         : niveaux,
        'search'          : search,
        'niv_filter'      : niv_filter,
        'stat_filter'     : stat_filter,
        'total'           : etudiants.count(),
        'statut_choices'  : User.Statut.choices,
        'nb_notifications': 0,
        'nb_zone_rouge'   : sum(
            1 for e in etudiants_data if e['statut_zone'] == 'ROUGE'
        ),
    }
    return render(request, 'accounts/etudiants_list.html', context)


@login_required
@role_required('ADMIN')
def etudiant_create(request):
    """Créer un nouvel étudiant."""

    from academic.models import Niveau, InscriptionNiveau

    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name  = request.POST.get('last_name', '').strip()
        email      = request.POST.get('email', '').strip()
        matricule  = request.POST.get('matricule', '').strip()
        telephone  = request.POST.get('telephone', '').strip()
        niveau_id  = request.POST.get('niveau')
        password   = request.POST.get('password', '')

        errors = []
        if not first_name:
            errors.append("Le prénom est obligatoire.")
        if not last_name:
            errors.append("Le nom est obligatoire.")
        if not email:
            errors.append("L'email est obligatoire.")
        if not matricule:
            errors.append("Le matricule est obligatoire.")
        if not password:
            errors.append("Le mot de passe est obligatoire.")
        if not niveau_id:
            errors.append("Le niveau est obligatoire.")
        if User.objects.filter(email=email).exists():
            errors.append(f"L'email '{email}' est déjà utilisé.")
        if User.objects.filter(matricule=matricule).exists():
            errors.append(f"Le matricule '{matricule}' existe déjà.")

        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            user = User.objects.create_user(
                username   = matricule,
                first_name = first_name,
                last_name  = last_name,
                email      = email,
                matricule  = matricule,
                telephone  = telephone,
                password   = password,
                role       = 'ETUDIANT',
                statut     = 'ACTIF',
            )

            # Inscription au niveau
            InscriptionNiveau.objects.create(
                etudiant  = user,
                niveau_id = niveau_id,
            )

            messages.success(
                request,
                f"✅ Étudiant '{user.nom_complet}' créé et inscrit avec succès !"
            )
            return redirect('admin_etudiants')

    niveaux = Niveau.objects.filter(
        is_active=True
    ).select_related('filiere__departement').order_by('filiere__nom', 'nom')

    context = {
        'niveaux'         : niveaux,
        'nb_notifications': 0,
        'nb_zone_rouge'   : 0,
    }
    return render(request, 'accounts/etudiant_form.html', context)


@login_required
@role_required('ADMIN')
def etudiant_edit(request, pk):
    """Modifier un étudiant."""

    from academic.models import Niveau, InscriptionNiveau

    etudiant = get_object_or_404(User, pk=pk, role='ETUDIANT')

    if request.method == 'POST':
        first_name   = request.POST.get('first_name', '').strip()
        last_name    = request.POST.get('last_name', '').strip()
        email        = request.POST.get('email', '').strip()
        matricule    = request.POST.get('matricule', '').strip()
        telephone    = request.POST.get('telephone', '').strip()
        statut       = request.POST.get('statut', 'ACTIF')
        niveau_id    = request.POST.get('niveau')
        new_password = request.POST.get('new_password', '').strip()

        errors = []
        if not first_name:
            errors.append("Le prénom est obligatoire.")
        if not last_name:
            errors.append("Le nom est obligatoire.")
        if not email:
            errors.append("L'email est obligatoire.")
        if User.objects.filter(email=email).exclude(pk=pk).exists():
            errors.append(f"L'email '{email}' est déjà utilisé.")
        if User.objects.filter(matricule=matricule).exclude(pk=pk).exists():
            errors.append(f"Le matricule '{matricule}' existe déjà.")

        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            etudiant.first_name = first_name
            etudiant.last_name  = last_name
            etudiant.email      = email
            etudiant.matricule  = matricule
            etudiant.username   = matricule
            etudiant.telephone  = telephone
            etudiant.statut     = statut

            if new_password:
                if len(new_password) < 8:
                    messages.error(
                        request,
                        "Le mot de passe doit contenir au moins 8 caractères."
                    )
                    return redirect('etudiant_edit', pk=pk)
                etudiant.set_password(new_password)

            etudiant.save()

            # Mise à jour du niveau
            if niveau_id:
                InscriptionNiveau.objects.filter(
                    etudiant=etudiant,
                    is_active=True
                ).update(is_active=False)

                InscriptionNiveau.objects.get_or_create(
                    etudiant  = etudiant,
                    niveau_id = niveau_id,
                    defaults  = {'is_active': True}
                )

            messages.success(
                request,
                f"✅ Étudiant '{etudiant.nom_complet}' modifié !"
            )
            return redirect('admin_etudiants')

    niveaux = Niveau.objects.filter(
        is_active=True
    ).select_related('filiere__departement').order_by('filiere__nom', 'nom')

    inscription_active = etudiant.inscriptions.filter(
        is_active=True
    ).select_related('niveau').first()

    context = {
        'etudiant'        : etudiant,
        'niveaux'         : niveaux,
        'inscription'     : inscription_active,
        'statut_choices'  : User.Statut.choices,
        'nb_notifications': 0,
        'nb_zone_rouge'   : 0,
    }
    return render(request, 'accounts/etudiant_form.html', context)


@login_required
@role_required('ADMIN')
def etudiant_delete(request, pk):
    """Supprimer un étudiant."""

    etudiant = get_object_or_404(User, pk=pk, role='ETUDIANT')

    if request.method == 'POST':
        nom = etudiant.nom_complet
        etudiant.delete()
        messages.success(request, f"🗑️ Étudiant '{nom}' supprimé.")
        return redirect('admin_etudiants')

    context = {
        'objet'           : etudiant,
        'type'            : 'étudiant',
        'retour_url'      : 'admin_etudiants',
        'nb_notifications': 0,
        'nb_zone_rouge'   : 0,
    }
    return render(request, 'components/confirm_delete.html', context)


@login_required
@role_required('ADMIN')
def zone_rouge_list(request):
    """Liste des étudiants en zone rouge."""

    from dashboard.views import _get_etudiants_zone_rouge
    etudiants_rouge = _get_etudiants_zone_rouge()

    context = {
        'etudiants_rouge' : etudiants_rouge,
        'total'           : len(etudiants_rouge),
        'nb_notifications': 0,
        'nb_zone_rouge'   : len(etudiants_rouge),
    }
    return render(request, 'accounts/zone_rouge.html', context)


@login_required
@role_required('ADMIN')
def parametres_view(request):
    """Page de paramètres globaux."""

    from django.conf import settings as django_settings

    if request.method == 'POST':
        messages.success(request, "✅ Paramètres sauvegardés !")
        return redirect('admin_parametres')

    context = {
        'gps_radius'       : getattr(django_settings, 'GPS_RADIUS_METERS', 15),
        'code_duration'    : getattr(django_settings, 'ATTENDANCE_CODE_DURATION', 10),
        'absence_threshold': getattr(django_settings, 'ABSENCE_THRESHOLD', 3),
        'late_threshold'   : getattr(django_settings, 'LATE_THRESHOLD_MINUTES', 15),
        'nb_notifications' : 0,
        'nb_zone_rouge'    : 0,
    }
    return render(request, 'accounts/parametres.html', context)