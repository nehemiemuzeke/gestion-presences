"""
Views de configuration globale
Pages d'erreur personnalisées
"""

from django.shortcuts import render


def page_404(request, exception=None):
    """Page 404 personnalisée."""
    return render(request, '404.html', status=404)


def page_500(request):
    """Page 500 personnalisée."""
    return render(request, '500.html', status=500)