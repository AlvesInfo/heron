from django import forms
from django.forms.widgets import DateInput


class DateInputDate(DateInput):
    template_name = 'heron/date_input_form.html'


class ModalForms(forms.Form):
    titre_modal = forms.CharField()
    html_modal = forms.CharField(required=False)
