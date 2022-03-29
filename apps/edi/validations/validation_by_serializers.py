
from apps.core.functions.functions_setups import settings
from apps.core.functions.functions_serializers import (
    StrictBooleanField,
    NullBooleanField,
    MaxLenghtCharField,
    ZeroIntegerField,
    ChoicesIntField,
    ChoicesCharField,
)
from rest_framework import serializers
from django import forms

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
    print(s.is_valid())
    print(s.errors)
    print(s.initial_data)
    print(s.data)


if __name__ == '__main__':
    main()
    print(
        "Ser, is instance serializer : ",
        isinstance(Seria, (type(serializers.Serializer), type(serializers.ModelSerializer)))
    )
    print(
        "SeriaModel, is instance serializer : ",
        isinstance(SeriaModel, (type(serializers.Serializer), type(serializers.ModelSerializer)))
    )
    print(
        "DjangoForm, is instance forms : ",
        isinstance(DjangoForm, (type(forms.Form), type(forms.ModelForm)))
    )
    print(
        "DjangoModelForm, is instance forms : ",
        isinstance(DjangoModelForm, (type(forms.Form), type(forms.ModelForm)))
    )
