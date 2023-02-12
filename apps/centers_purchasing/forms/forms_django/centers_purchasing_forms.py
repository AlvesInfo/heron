# pylint: disable=E0401,R0903
"""
Forms des Maisons
"""
from django import forms

from apps.centers_purchasing.models import (
    PrincipalCenterPurchase,
    ChildCenterPurchase,
    Signboard,
    SignboardModel,
    Translation,
    SignboardModelTranslate,
    TranslationParamaters,
)


class MeresForm(forms.ModelForm):
    class Meta:
        model = PrincipalCenterPurchase
        fields = [
            "code",
            "name",
            "generic_coefficient",
            "comment",
        ]


class FillesForm(forms.ModelForm):
    class Meta:
        model = ChildCenterPurchase
        fields = [
            "code",
            "base_center",
            "name",
            "generic_coefficient",
            "comment",
            "legal_notice",
            "iban",
            "code_swift",
            "sending_email",
        ]


class SignboardForm(forms.ModelForm):
    img_delete = forms.CheckboxInput()

    class Meta:
        model = Signboard
        fields = [
            "code",
            "sale_price_category",
            "name",
            "logo",
            "generic_coefficient",
            "comment",
            "message",
        ]


class SignboardModelForm(forms.ModelForm):
    class Meta:
        model = SignboardModel
        fields = [
            "sign_board",
            "name",
            "short_name",
            "action",
            "comment",
        ]


class TranslationForm(forms.ModelForm):
    class Meta:
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
    class Meta:
        model = SignboardModelTranslate
        fields = [
            "sign_board_model",
            "translation",
        ]


class TranslationParamatersForm(forms.ModelForm):
    class Meta:
        model = TranslationParamaters
        fields = [
            "code",
            "translation",
            "prefix_suffix",
            "field",
        ]
