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


class Ser(serializers.Serializer):
    text = MaxLenghtCharField(max_length=10)


def main():
    data = [{"text": "ceci est un texte très très long"}, {"text":" a"}]
    s = Ser(data=data, many=True)
    print(s.is_valid())
    print(s.initial_data)
    print(s.data)


if __name__ == '__main__':
    main()
