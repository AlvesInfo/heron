# pylint: disable=E0401,R0903
"""
Forms des Maisons
"""
from ckeditor.widgets import CKEditorWidget
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
from apps.parameters.forms.forms_django.const_forms import SELECT_FLUIDE_DICT


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

    legal_notice = forms.CharField(widget=CKEditorWidget())
    footer = forms.CharField(widget=CKEditorWidget())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["legal_notice"].widget.attrs["is"] = "textarea-autogrow"
        self.fields["footer"].widget.attrs["is"] = "textarea-autogrow"
        self.fields['comment'].required = False
        self.fields['legal_notice'].required = False
        self.fields['footer'].required = False

    class Meta:
        model = ChildCenterPurchase
        fields = [
            "code",
            "base_center",
            "name",
            "generic_coefficient",
            "comment",
            "legal_notice",
            "footer",
            "iban",
            "code_swift",
            "sending_email",
            "societe_cpy_x3",
            "site_fcy_x3",
            "member_num",
            "code_plan_sage",
        ]


class SignboardForm(forms.ModelForm):
    img_delete = forms.CheckboxInput()

    message = forms.CharField(widget=CKEditorWidget())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["message"].widget.attrs["is"] = "textarea-autogrow"
        self.fields['comment'].required = False
        self.fields['message'].required = False

    class Meta:
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
            # "email_contact",
            # "email_object",
            # "email_template",
            # "email_corp",
        ]
        widgets = {
            "child_center": forms.Select(attrs=SELECT_FLUIDE_DICT),
            "sale_price_category": forms.Select(attrs=SELECT_FLUIDE_DICT),
        }


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
