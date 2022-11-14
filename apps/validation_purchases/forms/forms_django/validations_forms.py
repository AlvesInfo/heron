# pylint: disable=E0401,R0903
"""
FR : Module des formulaires de validation des imports Sage X3
EN : Sage X3 import validation forms module

Commentaire:

created at: 2022-11-11
created by: Paulo ALVES

modified at: 2021-11-11
modified by: Paulo ALVES
"""
from django import forms

from apps.validation_purchases.models import EdiImportControl


class EdiImportControlForm(forms.ModelForm):
    """Formulaire pour l'update des factures founisseurs importées"""
    class Meta:
        model = EdiImportControl
        fields = [
            "statement_without_tax",
            "statement_amount_with_tax",
            "comment",
        ]


