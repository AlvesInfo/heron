"""Forms des Maisons."""

from ckeditor.widgets import CKEditorWidget
from django import forms

from apps.centers_purchasing.models import (
    ChildCenterPurchase,
    PrincipalCenterPurchase,
    Signboard,
    SignboardModel,
    SignboardModelTranslate,
    Translation,
    TranslationParamaters,
)
from apps.parameters.forms.forms_django.const_forms import SELECT_FLUIDE_DICT


class MeresForm(forms.ModelForm):
    """Formulaire des centrales mères."""

    use_required_attribute = False

    class Meta:
        """Métadonnées Django : modèle et champs du formulaire."""

        model = PrincipalCenterPurchase
        fields = [
            "code",
            "name",
            "generic_coefficient",
            "comment",
        ]


class FillesForm(forms.ModelForm):
    """Formulaire des centrales filles."""

    use_required_attribute = False

    legal_notice = forms.CharField(widget=CKEditorWidget())
    footer = forms.CharField(widget=CKEditorWidget())

    def __init__(self, *args, **kwargs):
        """Ajuste les éditeurs de texte et rend les champs libres facultatifs."""
        super().__init__(*args, **kwargs)
        self.fields["legal_notice"].widget.attrs["is"] = "textarea-autogrow"
        self.fields["footer"].widget.attrs["is"] = "textarea-autogrow"
        self.fields["comment"].required = False
        self.fields["legal_notice"].required = False
        self.fields["footer"].required = False
        self.fields["bank_account_holder"].required = False
        self.fields["adress_holder"].required = False
        self.fields["adress_2_holder"].required = False
        self.fields["postal_code_holder"].required = False
        self.fields["city_holder"].required = False
        self.fields["bank"].required = False
        self.fields["swift_code"].required = False
        self.fields["iban"].required = False
        self.fields["society"].required = False
        self.fields["society"].queryset = self.fields["society"].queryset.order_by(
            "third_party_num"
        )
        self.fields["society"].label_from_instance = lambda society: (
            f"{society.third_party_num} - {society.name or ''}"
        )

    class Meta:
        """Métadonnées Django : modèle et champs du formulaire."""

        model = ChildCenterPurchase
        fields = [
            "code",
            "base_center",
            "name",
            "society",
            "generic_coefficient",
            "comment",
            "legal_notice",
            "footer",
            "sending_email",
            "societe_cpy_x3",
            "site_fcy_x3",
            "member_num",
            "code_plan_sage",
            "bank_account_holder",
            "adress_holder",
            "adress_2_holder",
            "postal_code_holder",
            "city_holder",
            "bank",
            "swift_code",
            "iban",
        ]


class SignboardForm(forms.ModelForm):
    """Formulaire des enseignes."""

    use_required_attribute = False
    img_delete = forms.CheckboxInput()

    message = forms.CharField(widget=CKEditorWidget())

    def __init__(self, *args, **kwargs):
        """Ajuste l'éditeur de message et rend les champs libres facultatifs."""
        super().__init__(*args, **kwargs)
        self.fields["message"].widget.attrs["is"] = "textarea-autogrow"
        self.fields["comment"].required = False
        self.fields["message"].required = False

    class Meta:
        """Métadonnées Django : modèle et champs du formulaire."""

        model = Signboard
        fields = [
            "child_center",
            "code",
            "sale_price_category",
            "name",
            "logo",
            "generic_coefficient",
            "comment",
            "message",
        ]
        widgets = {
            "child_center": forms.Select(attrs=SELECT_FLUIDE_DICT),
            "sale_price_category": forms.Select(attrs=SELECT_FLUIDE_DICT),
        }


class SignboardModelForm(forms.ModelForm):
    """Formulaire des modèles de documents par enseigne."""

    class Meta:
        """Métadonnées Django : modèle et champs du formulaire."""

        model = SignboardModel
        fields = [
            "sign_board",
            "name",
            "short_name",
            "action",
            "comment",
        ]


class TranslationForm(forms.ModelForm):
    """Formulaire des traductions."""

    class Meta:
        """Métadonnées Django : modèle et champs du formulaire."""

        model = Translation
        fields = [
            "name",
            "short_name",
            "french_text",
            "italian_text",
            "spanih_text",
            "portuguese_text",
            "english_text",
        ]


class SignboardModelTranslateForm(forms.ModelForm):
    """Formulaire d'association modèle d'enseigne / traduction."""

    class Meta:
        """Métadonnées Django : modèle et champs du formulaire."""

        model = SignboardModelTranslate
        fields = [
            "sign_board_model",
            "translation",
        ]


class TranslationParamatersForm(forms.ModelForm):
    """Formulaire des paramètres de traduction."""

    class Meta:
        """Métadonnées Django : modèle et champs du formulaire."""

        model = TranslationParamaters
        fields = [
            "code",
            "translation",
            "prefix_suffix",
            "field",
        ]
