# pylint: disable=E0401,R0903,E1101
"""
FR : Module des formulaires de validation des imports des factures
EN : Imported invoices forms module

Commentaire:

created at: 2022-11-11
created by: Paulo ALVES

modified at: 2021-12-29
modified by: Paulo ALVES
"""
from django import forms

from apps.centers_clients.models import Maison
from apps.edi.models import EdiImport
from apps.parameters.models import Category


class ChangeBigCategoryForm(forms.ModelForm):
    """Pour changer la grande catégorie des factures fournisseurs"""

    def __init__(self, *args, **kwargs):
        """Ajout ou transformation des champs de formulaires"""
        super().__init__(*args, **kwargs)

        self.big_category_choices = [("", "")] + [
            (category.uuid_identification, category.name) for category in Category.objects.all()
        ]
        big_category_default = forms.ChoiceField(
            choices=self.big_category_choices,
            label="grande catégorie",
            required=True,
        )
        self.fields["big_category_default"] = big_category_default
        self.fields["uuid_origin"] = forms.UUIDField()

        self.fields["id"] = forms.IntegerField(initial=0, required=False)

    class Meta:
        """class Meta Django"""

        model = EdiImport
        fields = ("id", "big_category", "third_party_num", "invoice_month")


class ChangeCttForm(forms.ModelForm):
    """Formulaire de chanagement des cct"""

    def __init__(self, *args, **kwargs):
        """Ajout ou transformation des champs de formulaires"""
        super().__init__(*args, **kwargs)

        self.cct_choices = [("", "")] + [
            (
                maison.cct,
                f"{maison.cct}-" f"{maison.intitule}-" f"{maison.adresse[:50]}-" f"{maison.ville}",
            )
            for maison in Maison.objects.all()
        ]
        cct = forms.ChoiceField(
            choices=self.cct_choices,
            label="CCT X3",
            required=True,
        )
        self.fields["cct"] = cct

        uuid_identification = forms.UUIDField()
        self.fields["uuid_identification"] = uuid_identification

        self.fields["id"] = forms.IntegerField(initial=0, required=False)

    class Meta:
        """class Meta Django"""

        model = EdiImport
        fields = ("id", "third_party_num", "invoice_number", "invoice_year")
