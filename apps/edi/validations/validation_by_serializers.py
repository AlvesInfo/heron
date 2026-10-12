
from apps.core.functions.functions_serializers import (
    MaxLenghtCharField,
)
from rest_framework import serializers
from django import forms

from heron.loggers import LOGGER_EDI
from apps.edi.models import EdiImport


class DjangoForm(forms.Form):
    test = forms.CharField(max_length=10)


class DjangoModelForm(forms.ModelForm):
    class Meta:
        model = EdiImport
        fields = "__all__"


class Seria(serializers.Serializer):
    text = MaxLenghtCharField(max_length=10)


class SeriaModel(serializers.ModelSerializer):
    class Meta:
        model = EdiImport
        fields = "__all__"


def main():
    data = [{"text": "ceci est un texte très très long"}, {"text": None}]
    s = Seria(data=data, many=True)
    LOGGER_EDI.info("is_valid : %s", s.is_valid())
    LOGGER_EDI.info("errors : %s", s.errors)
    LOGGER_EDI.info("initial_data : %s", s.initial_data)
    LOGGER_EDI.info("data : %s", s.data)
    return s


def classes_kinds():
    """Nature des classes d'essai : sérialiseurs DRF ou formulaires Django"""
    serializer_types = (type(serializers.Serializer), type(serializers.ModelSerializer))
    form_types = (type(forms.Form), type(forms.ModelForm))

    return {
        "Seria": isinstance(Seria, serializer_types),
        "SeriaModel": isinstance(SeriaModel, serializer_types),
        "DjangoForm": isinstance(DjangoForm, form_types),
        "DjangoModelForm": isinstance(DjangoModelForm, form_types),
    }


if __name__ == "__main__":
    main()
    LOGGER_EDI.info("%s", classes_kinds())
