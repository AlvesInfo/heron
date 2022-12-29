# pylint: disable=E0401,R0903
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


class ChangeCttForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.CCT_CHOICES = [("", "")] + [
            (
                maison.cct,
                f"{maison.cct}-"
                f"{maison.intitule}-"
                f"{maison.adresse[:50]}-"
                f"{maison.ville}",
            )
            for maison in Maison.objects.all()
        ]
        cct = forms.ChoiceField(
            choices=self.CCT_CHOICES,
            label="CCT X3",
            required=True,
        )
        self.fields["cct"] = cct

        uuid_identification = forms.UUIDField()
        self.fields["uuid_identification"] = uuid_identification

    class Meta:
        model = EdiImport
        fields = ("third_party_num", "invoice_number", "invoice_year")
