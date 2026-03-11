"""
Views du contôle de refacturation
"""
import pendulum
from django.shortcuts import render


# CONTROLES DE REFCATURATION ETAPE 2.3 =============================================================

def control_rebilling_m_m_1(request):
    """Ecran de contrôle de refacturation"""
