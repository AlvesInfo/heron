# pylint: disable=E0401,R0903
"""
Forms des Parameters
"""
from ckeditor.widgets import CKEditorWidget
from django import forms

from apps.parameters.forms.forms_django.const_forms import SELECT_FLUIDE_DICT
from apps.parameters.models import Email


class EmailForm(forms.ModelForm):
    """Form pour les Emails"""

    email_body = forms.CharField(widget=CKEditorWidget())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email_body"].widget.attrs["is"] = "textarea-autogrow"

    class Meta:
        """class Meta"""

        model = Email
        fields = (
            "description",
            "subject",
            "email_body",
        )
        widgets = {"name": forms.Select(attrs=SELECT_FLUIDE_DICT)}
