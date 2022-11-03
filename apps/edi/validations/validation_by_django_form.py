"""
FR: Formulaires de validation
EN: Django forms for validation
for django verions == 1.11 | 2.0 | 2.1 | 2.2 | 3.2
    author: Paulo ALVES
    created at: 2022-03-11
    modified at: 2022-03-11
    version : 0.02
"""
from django import forms

from apps.core.validations.forms_base import TruncatedTextField, NullZeroDecimalField
from apps.edi.models import EdiImport


class EdiForm(forms.ModelForm):
    """
    FR : EdiForm pour la validation des fichiers edi
    EN : EdiForm for edi files validation
    """
    supplier = TruncatedTextField()
    supplier_ident = TruncatedTextField()
    siret_payeur = TruncatedTextField()
    code_fournisseur = TruncatedTextField()
    code_maison = TruncatedTextField()
    maison = TruncatedTextField()
    num_commande_acuitis = TruncatedTextField()
    num_bl = TruncatedTextField()
    nature_facture = TruncatedTextField()
    devise = TruncatedTextField()
    reference_article = TruncatedTextField()
    code_ean = TruncatedTextField()
    libelle = TruncatedTextField()
    famille = TruncatedTextField()
    nom_client = TruncatedTextField()
    Commentaire = TruncatedTextField()
    date_commande_acuitis = forms.DateField(input_formats=["%Y-%m-%d"])
    date_bl = forms.DateField(input_formats=["%Y-%m-%d"])
    date_facture = forms.DateField(input_formats=["%Y-%m-%d"])
    qte = NullZeroDecimalField()
    qte_emballage = NullZeroDecimalField()
    px_unitaire_brut = NullZeroDecimalField()
    px_unitaire_net = NullZeroDecimalField()
    emballage = NullZeroDecimalField()
    port = NullZeroDecimalField()
    montant_brut = NullZeroDecimalField()
    montant_remise_1 = NullZeroDecimalField()
    montant_remise_2 = NullZeroDecimalField()
    montant_remise_3 = NullZeroDecimalField()
    montant_net = NullZeroDecimalField()
    taux_tva = NullZeroDecimalField()
    montant_tva = NullZeroDecimalField()
    montant_ttc = NullZeroDecimalField()
    invoice_amount_without_tax = NullZeroDecimalField()
    invoice_amount_tax = NullZeroDecimalField()
    invoice_amount_with_tax = NullZeroDecimalField()

    class Meta:
        """class Meta du modèle django"""
        model = EdiImport
        exclude = ["pk"]
