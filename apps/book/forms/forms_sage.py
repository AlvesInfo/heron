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
from django import forms

from apps.core.validation.forms_base import SageNullBooleanField
from apps.book.models import (
    Society,
    Address,
    Contact,
    SocietyBank,
)


class BprBookSageForm(forms.ModelForm):
    """Validation de l'import ZBIBPR des Tiers Génériques Sage X3"""

    is_client = SageNullBooleanField()
    is_agent = SageNullBooleanField()
    is_prospect = SageNullBooleanField()
    is_supplier = SageNullBooleanField()
    is_various = SageNullBooleanField()
    is_service_provider = SageNullBooleanField()
    is_transporter = SageNullBooleanField()
    is_contractor = SageNullBooleanField()

    class Meta:
        """class Meta du forms.ModelForm django"""

        model = Society
        fields = [
            "third_party_num",
            "name",
            "short_name",
            "corporate_name",
            "siret_number",
            "vat_cee_number",
            "vat_number",
            "naf_code",
            "currency",
            "country",
            "language",
            "budget_code",
            "reviser",
            "is_client",
            "is_agent",
            "is_prospect",
            "is_supplier",
            "is_various",
            "is_service_provider",
            "is_transporter",
            "is_contractor",
        ]


class BpsBookSageForm(forms.ModelForm):
    """Validation de l'import ZBIBPS des Tiers Fournisseurs Sage X3"""

    class Meta:
        """class Meta du forms.ModelForm django"""

        model = Society
        fields = [
            "third_party_num",
            "payment_condition_supplier",
            "vat_sheme_supplier",
            "account_supplier_code",
        ]


class BpcBookSageForm(forms.ModelForm):
    """Validation de l'import ZBIBPC des Tiers Clients Sage X3"""

    class Meta:
        """class Meta du forms.ModelForm django"""

        model = Society
        fields = [
            "third_party_num",
            "payment_condition_client",
            "vat_sheme_client",
            "account_client_code",
        ]


class BookAdressesSageForm(forms.ModelForm):
    """Validation de l'import ZBIADDR des Adresses des Tiers Sage X3"""

    default_adress = SageNullBooleanField()

    class Meta:
        """class Meta du forms.ModelForm django"""

        model = Address
        fields = [
            "society",
            "default_adress",
            "address_code",
            "address_type",
            "line_01",
            "line_02",
            "line_03",
            "state",
            "postal_code",
            "city",
            "country",
            "phone_number_01",
            "phone_number_02",
            "phone_number_03",
            "phone_number_04",
            "phone_number_05",
            "mobile",
            "email_01",
            "email_02",
            "email_03",
            "email_04",
            "email_05",
            "web_site",
        ]


class CodeContactsSageForm(forms.ModelForm):
    """Validation de l'import ZBICONTACT des Codes Contacts des Tiers Sage X3"""

    class Meta:
        """class Meta du forms.ModelForm django"""

        model = Contact
        fields = [
            "society",
            "code",
            "service",
            "role",
        ]


class BookContactsSageForm(forms.ModelForm):
    """Validation de l'import ZBICONTCRM des Contacts des Tiers Sage X3"""

    class Meta:
        """class Meta du forms.ModelForm django"""

        model = Contact
        fields = [
            "society",
            "civility",
            "first_name",
            "last_name",
            "language",
            "category",
            "line_01",
            "line_02",
            "line_03",
            "state",
            "postal_code",
            "city",
            "country",
            "phone_number",
            "mobile_number",
            "email",
        ]


class BookBanksSageForm(forms.ModelForm):
    """Validation de l'import ZBIBANK des Banques des Tiers Sage X3"""

    is_default = SageNullBooleanField()

    class Meta:
        """class Meta du forms.ModelForm django"""

        model = SocietyBank
        fields = [
            "society",
            "account_number",
            "address",
            "payee",
            "domiciliation_01",
            "domiciliation_02",
            "domiciliation_03",
            "domiciliation_04",
            "iban_prefix",
            "bic_code",
            "country",
            "currency",
            "is_default",
        ]
