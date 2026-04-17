"""
Views Academic
CRUD : Départements, Filières, Niveaux, Matières
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from accounts.views import role_required
from accounts.models import User
from .models import Departement, Filiere, Niveau, Matiere, InscriptionNiveau


# ═══════════════════════════════════════════════════════════
# DÉPARTEMENTS
# ═══════════════════════════════════════════════════════════

@login_required
@role_required('ADMIN')
def departements_list(request):
    """Liste de tous les départements."""

    search = request.GET.get('search', '')

    departements = Departement.objects.annotate(
        nb_filieres=Count('filieres', distinct=True)
    ).order_by('nom')

    if search:
        departements = departements.filter(
            Q(nom__icontains=search) |
            Q(code__icontains=search)
        )

    context = {
        'departements' : departements,
        'search'       : search,
        'total'        : departements.count(),
        'nb_notifications': 0,
        'nb_zone_rouge': 0,
    }
    return render(request, 'academic/departements_list.html', context)


@login_required
@role_required('ADMIN')
def departement_create(request):
    """Créer un nouveau département."""

    if request.method == 'POST':
        nom         = request.POST.get('nom', '').strip()
        code        = request.POST.get('code', '').strip().upper()
        description = request.POST.get('description', '').strip()
        responsable_id = request.POST.get('responsable')

        # Validation
        errors = []
        if not nom:
            errors.append("Le nom est obligatoire.")
        if not code:
            errors.append("Le code est obligatoire.")
        if Departement.objects.filter(code=code).exists():
            errors.append(f"Le code '{code}' existe déjà.")

        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            departement = Departement.objects.create(
                nom=nom,
                code=code,
                description=description,
                responsable_id=responsable_id if responsable_id else None,
            )
            messages.success(
                request,
                f"✅ Département '{departement.nom}' créé avec succès !"
            )
            return redirect('admin_departements')

    # Professeurs pour le champ responsable
    professeurs = User.objects.filter(
        role__in=['ADMIN', 'PROFESSEUR'],
        statut='ACTIF'
    ).order_by('last_name')

    context = {
        'professeurs'     : professeurs,
        'nb_notifications': 0,
        'nb_zone_rouge'   : 0,
    }
    return render(request, 'academic/departement_form.html', context)


@login_required
@role_required('ADMIN')
def departement_edit(request, pk):
    """Modifier un département existant."""

    departement = get_object_or_404(Departement, pk=pk)

    if request.method == 'POST':
        nom            = request.POST.get('nom', '').strip()
        code           = request.POST.get('code', '').strip().upper()
        description    = request.POST.get('description', '').strip()
        responsable_id = request.POST.get('responsable')
        is_active      = request.POST.get('is_active') == 'on'

        errors = []
        if not nom:
            errors.append("Le nom est obligatoire.")
        if not code:
            errors.append("Le code est obligatoire.")
        if Departement.objects.filter(code=code).exclude(pk=pk).exists():
            errors.append(f"Le code '{code}' existe déjà.")

        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            departement.nom            = nom
            departement.code           = code
            departement.description    = description
            departement.responsable_id = responsable_id if responsable_id else None
            departement.is_active      = is_active
            departement.save()

            messages.success(
                request,
                f"✅ Département '{departement.nom}' modifié avec succès !"
            )
            return redirect('admin_departements')

    professeurs = User.objects.filter(
        role__in=['ADMIN', 'PROFESSEUR'],
        statut='ACTIF'
    ).order_by('last_name')

    context = {
        'departement'     : departement,
        'professeurs'     : professeurs,
        'nb_notifications': 0,
        'nb_zone_rouge'   : 0,
    }
    return render(request, 'academic/departement_form.html', context)


@login_required
@role_required('ADMIN')
def departement_delete(request, pk):
    """Supprimer un département."""

    departement = get_object_or_404(Departement, pk=pk)

    if request.method == 'POST':
        nom = departement.nom
        departement.delete()
        messages.success(request, f"🗑️ Département '{nom}' supprimé.")
        return redirect('admin_departements')

    context = {
        'objet'           : departement,
        'type'            : 'département',
        'retour_url'      : 'admin_departements',
        'nb_notifications': 0,
        'nb_zone_rouge'   : 0,
    }
    return render(request, 'components/confirm_delete.html', context)


# ═══════════════════════════════════════════════════════════
# FILIÈRES
# ═══════════════════════════════════════════════════════════

@login_required
@role_required('ADMIN')
def filieres_list(request):
    """Liste de toutes les filières."""

    search = request.GET.get('search', '')
    dept_filter = request.GET.get('departement', '')

    filieres = Filiere.objects.select_related('departement').annotate(
        nb_niveaux=Count('niveaux', distinct=True)
    ).order_by('departement__nom', 'nom')

    if search:
        filieres = filieres.filter(
            Q(nom__icontains=search) |
            Q(code__icontains=search)
        )

    if dept_filter:
        filieres = filieres.filter(departement_id=dept_filter)

    departements = Departement.objects.filter(is_active=True)

    context = {
        'filieres'        : filieres,
        'departements'    : departements,
        'search'          : search,
        'dept_filter'     : dept_filter,
        'total'           : filieres.count(),
        'nb_notifications': 0,
        'nb_zone_rouge'   : 0,
    }
    return render(request, 'academic/filieres_list.html', context)


@login_required
@role_required('ADMIN')
def filiere_create(request):
    """Créer une nouvelle filière."""

    if request.method == 'POST':
        nom             = request.POST.get('nom', '').strip()
        code            = request.POST.get('code', '').strip().upper()
        departement_id  = request.POST.get('departement')
        description     = request.POST.get('description', '').strip()

        errors = []
        if not nom:
            errors.append("Le nom est obligatoire.")
        if not code:
            errors.append("Le code est obligatoire.")
        if not departement_id:
            errors.append("Le département est obligatoire.")
        if Filiere.objects.filter(code=code).exists():
            errors.append(f"Le code '{code}' existe déjà.")

        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            filiere = Filiere.objects.create(
                nom=nom,
                code=code,
                departement_id=departement_id,
                description=description,
            )
            messages.success(
                request,
                f"✅ Filière '{filiere.nom}' créée avec succès !"
            )
            return redirect('admin_filieres')

    departements = Departement.objects.filter(is_active=True).order_by('nom')

    context = {
        'departements'    : departements,
        'nb_notifications': 0,
        'nb_zone_rouge'   : 0,
    }
    return render(request, 'academic/filiere_form.html', context)


@login_required
@role_required('ADMIN')
def filiere_edit(request, pk):
    """Modifier une filière."""

    filiere = get_object_or_404(Filiere, pk=pk)

    if request.method == 'POST':
        nom            = request.POST.get('nom', '').strip()
        code           = request.POST.get('code', '').strip().upper()
        departement_id = request.POST.get('departement')
        description    = request.POST.get('description', '').strip()
        is_active      = request.POST.get('is_active') == 'on'

        errors = []
        if not nom:
            errors.append("Le nom est obligatoire.")
        if not code:
            errors.append("Le code est obligatoire.")
        if not departement_id:
            errors.append("Le département est obligatoire.")
        if Filiere.objects.filter(code=code).exclude(pk=pk).exists():
            errors.append(f"Le code '{code}' existe déjà.")

        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            filiere.nom            = nom
            filiere.code           = code
            filiere.departement_id = departement_id
            filiere.description    = description
            filiere.is_active      = is_active
            filiere.save()

            messages.success(
                request,
                f"✅ Filière '{filiere.nom}' modifiée avec succès !"
            )
            return redirect('admin_filieres')

    departements = Departement.objects.filter(is_active=True).order_by('nom')

    context = {
        'filiere'         : filiere,
        'departements'    : departements,
        'nb_notifications': 0,
        'nb_zone_rouge'   : 0,
    }
    return render(request, 'academic/filiere_form.html', context)


@login_required
@role_required('ADMIN')
def filiere_delete(request, pk):
    """Supprimer une filière."""

    filiere = get_object_or_404(Filiere, pk=pk)

    if request.method == 'POST':
        nom = filiere.nom
        filiere.delete()
        messages.success(request, f"🗑️ Filière '{nom}' supprimée.")
        return redirect('admin_filieres')

    context = {
        'objet'           : filiere,
        'type'            : 'filière',
        'retour_url'      : 'admin_filieres',
        'nb_notifications': 0,
        'nb_zone_rouge'   : 0,
    }
    return render(request, 'components/confirm_delete.html', context)


# ═══════════════════════════════════════════════════════════
# NIVEAUX
# ═══════════════════════════════════════════════════════════

@login_required
@role_required('ADMIN')
def niveaux_list(request):
    """Liste de tous les niveaux."""

    search      = request.GET.get('search', '')
    fil_filter  = request.GET.get('filiere', '')

    niveaux = Niveau.objects.select_related(
        'filiere__departement'
    ).annotate(
        nb_etudiants=Count('inscriptions', distinct=True),
        nb_matieres=Count('matieres', distinct=True),
    ).order_by('filiere__nom', 'nom')

    if search:
        niveaux = niveaux.filter(
            Q(nom__icontains=search) |
            Q(filiere__nom__icontains=search) |
            Q(annee_academique__icontains=search)
        )

    if fil_filter:
        niveaux = niveaux.filter(filiere_id=fil_filter)

    filieres = Filiere.objects.filter(is_active=True).select_related('departement')

    context = {
        'niveaux'         : niveaux,
        'filieres'        : filieres,
        'search'          : search,
        'fil_filter'      : fil_filter,
        'total'           : niveaux.count(),
        'nb_notifications': 0,
        'nb_zone_rouge'   : 0,
    }
    return render(request, 'academic/niveaux_list.html', context)


@login_required
@role_required('ADMIN')
def niveau_create(request):
    """Créer un nouveau niveau."""

    if request.method == 'POST':
        filiere_id      = request.POST.get('filiere')
        nom             = request.POST.get('nom', '').strip()
        annee_academique = request.POST.get('annee_academique', '').strip()

        errors = []
        if not filiere_id:
            errors.append("La filière est obligatoire.")
        if not nom:
            errors.append("Le niveau est obligatoire.")
        if not annee_academique:
            errors.append("L'année académique est obligatoire.")
        if Niveau.objects.filter(
            filiere_id=filiere_id,
            nom=nom,
            annee_academique=annee_academique
        ).exists():
            errors.append("Ce niveau existe déjà pour cette filière et cette année.")

        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            niveau = Niveau.objects.create(
                filiere_id=filiere_id,
                nom=nom,
                annee_academique=annee_academique,
            )
            messages.success(
                request,
                f"✅ Niveau '{niveau}' créé avec succès !"
            )
            return redirect('admin_niveaux')

    filieres       = Filiere.objects.filter(is_active=True).select_related('departement')
    niveau_choices = Niveau.NiveauChoix.choices

    context = {
        'filieres'        : filieres,
        'niveau_choices'  : niveau_choices,
        'nb_notifications': 0,
        'nb_zone_rouge'   : 0,
    }
    return render(request, 'academic/niveau_form.html', context)


@login_required
@role_required('ADMIN')
def niveau_edit(request, pk):
    """Modifier un niveau."""

    niveau = get_object_or_404(Niveau, pk=pk)

    if request.method == 'POST':
        filiere_id       = request.POST.get('filiere')
        nom              = request.POST.get('nom', '').strip()
        annee_academique = request.POST.get('annee_academique', '').strip()
        is_active        = request.POST.get('is_active') == 'on'

        errors = []
        if not filiere_id:
            errors.append("La filière est obligatoire.")
        if not nom:
            errors.append("Le niveau est obligatoire.")
        if not annee_academique:
            errors.append("L'année académique est obligatoire.")
        if Niveau.objects.filter(
            filiere_id=filiere_id,
            nom=nom,
            annee_academique=annee_academique
        ).exclude(pk=pk).exists():
            errors.append("Ce niveau existe déjà pour cette filière et cette année.")

        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            niveau.filiere_id       = filiere_id
            niveau.nom              = nom
            niveau.annee_academique = annee_academique
            niveau.is_active        = is_active
            niveau.save()

            messages.success(
                request,
                f"✅ Niveau '{niveau}' modifié avec succès !"
            )
            return redirect('admin_niveaux')

    filieres       = Filiere.objects.filter(is_active=True).select_related('departement')
    niveau_choices = Niveau.NiveauChoix.choices

    context = {
        'niveau'          : niveau,
        'filieres'        : filieres,
        'niveau_choices'  : niveau_choices,
        'nb_notifications': 0,
        'nb_zone_rouge'   : 0,
    }
    return render(request, 'academic/niveau_form.html', context)


@login_required
@role_required('ADMIN')
def niveau_delete(request, pk):
    """Supprimer un niveau."""

    niveau = get_object_or_404(Niveau, pk=pk)

    if request.method == 'POST':
        nom = str(niveau)
        niveau.delete()
        messages.success(request, f"🗑️ Niveau '{nom}' supprimé.")
        return redirect('admin_niveaux')

    context = {
        'objet'           : niveau,
        'type'            : 'niveau',
        'retour_url'      : 'admin_niveaux',
        'nb_notifications': 0,
        'nb_zone_rouge'   : 0,
    }
    return render(request, 'components/confirm_delete.html', context)


# ═══════════════════════════════════════════════════════════
# MATIÈRES
# ═══════════════════════════════════════════════════════════

@login_required
@role_required('ADMIN')
def matieres_list(request):
    """Liste de toutes les matières."""

    search     = request.GET.get('search', '')
    niv_filter = request.GET.get('niveau', '')

    matieres = Matiere.objects.select_related(
        'niveau__filiere__departement', 'professeur'
    ).order_by('niveau__filiere__nom', 'nom')

    if search:
        matieres = matieres.filter(
            Q(nom__icontains=search) |
            Q(code__icontains=search) |
            Q(professeur__last_name__icontains=search)
        )

    if niv_filter:
        matieres = matieres.filter(niveau_id=niv_filter)

    niveaux = Niveau.objects.filter(
        is_active=True
    ).select_related('filiere')

    context = {
        'matieres'        : matieres,
        'niveaux'         : niveaux,
        'search'          : search,
        'niv_filter'      : niv_filter,
        'total'           : matieres.count(),
        'nb_notifications': 0,
        'nb_zone_rouge'   : 0,
    }
    return render(request, 'academic/matieres_list.html', context)


@login_required
@role_required('ADMIN')
def matiere_create(request):
    """Créer une nouvelle matière."""

    if request.method == 'POST':
        nom             = request.POST.get('nom', '').strip()
        code            = request.POST.get('code', '').strip().upper()
        niveau_id       = request.POST.get('niveau')
        professeur_id   = request.POST.get('professeur')
        volume_horaire  = request.POST.get('volume_horaire', 30)
        coefficient     = request.POST.get('coefficient', 1)
        seuil_absences  = request.POST.get('seuil_absences', 3)
        description     = request.POST.get('description', '').strip()

        errors = []
        if not nom:
            errors.append("Le nom est obligatoire.")
        if not code:
            errors.append("Le code est obligatoire.")
        if not niveau_id:
            errors.append("Le niveau est obligatoire.")
        if Matiere.objects.filter(code=code).exists():
            errors.append(f"Le code '{code}' existe déjà.")

        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            matiere = Matiere.objects.create(
                nom=nom,
                code=code,
                niveau_id=niveau_id,
                professeur_id=professeur_id if professeur_id else None,
                volume_horaire=int(volume_horaire),
                coefficient=int(coefficient),
                seuil_absences=int(seuil_absences),
                description=description,
            )
            messages.success(
                request,
                f"✅ Matière '{matiere.nom}' créée avec succès !"
            )
            return redirect('admin_matieres')

    niveaux     = Niveau.objects.filter(is_active=True).select_related('filiere')
    professeurs = User.objects.filter(role='PROFESSEUR', statut='ACTIF').order_by('last_name')

    context = {
        'niveaux'         : niveaux,
        'professeurs'     : professeurs,
        'nb_notifications': 0,
        'nb_zone_rouge'   : 0,
    }
    return render(request, 'academic/matiere_form.html', context)


@login_required
@role_required('ADMIN')
def matiere_edit(request, pk):
    """Modifier une matière."""

    matiere = get_object_or_404(Matiere, pk=pk)

    if request.method == 'POST':
        nom            = request.POST.get('nom', '').strip()
        code           = request.POST.get('code', '').strip().upper()
        niveau_id      = request.POST.get('niveau')
        professeur_id  = request.POST.get('professeur')
        volume_horaire = request.POST.get('volume_horaire', 30)
        coefficient    = request.POST.get('coefficient', 1)
        seuil_absences = request.POST.get('seuil_absences', 3)
        description    = request.POST.get('description', '').strip()
        is_active      = request.POST.get('is_active') == 'on'

        errors = []
        if not nom:
            errors.append("Le nom est obligatoire.")
        if not code:
            errors.append("Le code est obligatoire.")
        if not niveau_id:
            errors.append("Le niveau est obligatoire.")
        if Matiere.objects.filter(code=code).exclude(pk=pk).exists():
            errors.append(f"Le code '{code}' existe déjà.")

        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            matiere.nom            = nom
            matiere.code           = code
            matiere.niveau_id      = niveau_id
            matiere.professeur_id  = professeur_id if professeur_id else None
            matiere.volume_horaire = int(volume_horaire)
            matiere.coefficient    = int(coefficient)
            matiere.seuil_absences = int(seuil_absences)
            matiere.description    = description
            matiere.is_active      = is_active
            matiere.save()

            messages.success(
                request,
                f"✅ Matière '{matiere.nom}' modifiée avec succès !"
            )
            return redirect('admin_matieres')

    niveaux     = Niveau.objects.filter(is_active=True).select_related('filiere')
    professeurs = User.objects.filter(role='PROFESSEUR', statut='ACTIF').order_by('last_name')

    context = {
        'matiere'         : matiere,
        'niveaux'         : niveaux,
        'professeurs'     : professeurs,
        'nb_notifications': 0,
        'nb_zone_rouge'   : 0,
    }
    return render(request, 'academic/matiere_form.html', context)


@login_required
@role_required('ADMIN')
def matiere_delete(request, pk):
    """Supprimer une matière."""

    matiere = get_object_or_404(Matiere, pk=pk)

    if request.method == 'POST':
        nom = matiere.nom
        matiere.delete()
        messages.success(request, f"🗑️ Matière '{nom}' supprimée.")
        return redirect('admin_matieres')

    context = {
        'objet'           : matiere,
        'type'            : 'matière',
        'retour_url'      : 'admin_matieres',
        'nb_notifications': 0,
        'nb_zone_rouge'   : 0,
    }
    return render(request, 'components/confirm_delete.html', context)