# pylint: disable=E0401,R0903
"""
FR : Module des formulaires de validation des imports Sage X3
EN : Sage X3 import validation forms module

Commentaire:

created at: 2021-11-07
created by: Paulo ALVES

modified at: 2021-11-07
modified by: Paulo ALVES
"""
from psycopg2 import sql
from django import forms
from django.core.exceptions import ValidationError
from django.db import connection

from apps.parameters.forms.forms_django.const_forms import SELECT_FLUIDE_DICT
from apps.book.models import Society, SupplierCct


class SocietyForm(forms.ModelForm):
    def clean(self):
        cleaned_data = super().clean()

        if cleaned_data.get("centers_suppliers_indentifier"):
            set_identifier = {
                str(value).strip()
                for value in cleaned_data.get("centers_suppliers_indentifier").split("|")
                if str(value).strip()
            }

            cleaned_data["centers_suppliers_indentifier"] = "|".join(sorted(set_identifier))

            # On vérifie qu'un des identifiants n'existe pas en base
            with connection.cursor() as cursor:
                sql_verify = sql.SQL(
                    """
                    select 
                        "third_party_num",
                        "identifier"
                    from (
                    select 
                        "third_party_num" ,
                        unnest(
                            string_to_array("centers_suppliers_indentifier", '|')
                        ) as "identifier"
                        from {table} bs
                        where "third_party_num" != %(third_party_num)s
                    ) req
                    where "identifier" = ANY(%(identifiers)s) 
                    """
                ).format(
                    table=sql.Identifier(Society._meta.db_table),
                )
                cursor.execute(
                    sql_verify,
                    {
                        "identifiers": list(set_identifier),
                        "third_party_num": cleaned_data.get("third_party_num"),
                    },
                )
                errors_dict = {key: value for key, value in cursor.fetchall()}

                if errors_dict:
                    text_error = "Doublons décelés dans Identifiant Centrale :"

                    for tiers, identifiant in errors_dict.items():
                        text_error += (
                            f"\n\t{'''- l'identifiant : '''}'{identifiant}', "
                            f"existe dèjà pour le Tiers : {tiers}"
                        )

                    raise ValidationError(f"{text_error}")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["in_use"] = forms.BooleanField(
            required=False,
            widget=forms.CheckboxInput,
        )
        self.fields["is_multi_billing"] = forms.BooleanField(
            required=False,
            widget=forms.CheckboxInput,
        )
        self.fields["integrable"] = forms.BooleanField(
            required=False,
            widget=forms.CheckboxInput,
        )
        self.fields["chargeable"] = forms.BooleanField(
            required=False,
            widget=forms.CheckboxInput,
        )
        self.fields["od_ana"] = forms.BooleanField(
            required=False,
            widget=forms.CheckboxInput,
        )
        self.fields["default_axe_pro"].required = False
        self.fields["stat_name"].required = False

        self.fields["address_code"].required = False
        self.fields["immeuble"].required = False
        self.fields["adresse"].required = False
        self.fields["code_postal"].required = False
        self.fields["ville"].required = False
        self.fields["pays"].required = False
        self.fields["email_01"].required = False
        self.fields["email_02"].required = False
        self.fields["email_03"].required = False
        self.fields["email_04"].required = False
        self.fields["email_05"].required = False
        self.fields["phone_number_01"].required = False
        self.fields["mobile_number"].required = False
        self.fields["invoice_entete"].required = False

    class Meta:
        model = Society
        fields = [
            "third_party_num",
            "name",
            "short_name",
            "corporate_name",
            "siret_number",
            "vat_cee_number",
            "vat_number",
            "client_category",
            "supplier_category",
            "naf_code",
            "currency",
            "country",
            "language",
            "budget_code",
            "reviser",
            "vat_sheme_supplier",
            "account_supplier_code",
            "vat_sheme_client",
            "account_client_code",
            "is_client",
            "is_agent",
            "is_prospect",
            "is_supplier",
            "is_various",
            "is_service_provider",
            "is_transporter",
            "is_contractor",
            "is_physical_person",
            "centers_suppliers_indentifier",
            "address_code",
            "immeuble",
            "adresse",
            "code_postal",
            "ville",
            "pays",
            "telephone",
            "mobile",
            "rfa_frequence",
            "rfa_remise",
            "integrable",
            "chargeable",
            "od_ana",
            "default_axe_pro",
            "in_use",
            "big_category_default",
            "stat_name",
            "is_multi_billing",
            "email_01",
            "email_02",
            "email_03",
            "email_04",
            "email_05",
            "phone_number_01",
            "mobile_number",
            "invoice_entete"
        ]

        widgets = {
            "rfa_frequence": forms.Select(attrs=SELECT_FLUIDE_DICT),
            "rfa_remise": forms.Select(attrs=SELECT_FLUIDE_DICT),
            "default_axe_pro": forms.Select(attrs=SELECT_FLUIDE_DICT),
            "big_category_default": forms.Select(attrs=SELECT_FLUIDE_DICT),
            "stat_name": forms.Select(attrs=SELECT_FLUIDE_DICT),
        }


class SupplierCctForm(forms.ModelForm):
    class Meta:
        model = SupplierCct
        fields = [
            "id",
            "cct_identifier",
        ]


class SupplierCctUnitForm(forms.ModelForm):
    class Meta:
        model = SupplierCct
        fields = [
            "id",
            "cct_identifier",
        ]
