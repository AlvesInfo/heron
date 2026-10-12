"""Module pour changement sur validation des champs d'un serializer.

Commentaire:

created at: 2022-11-13
created by: Paulo ALVES

modified at: 2021-02-14
modified by: Paulo ALVES
"""

from decimal import Decimal, InvalidOperation

from rest_framework import serializers


class NullBooleanField(serializers.BooleanField):
    """Surcharge de la class serializers.BooleanField, qui retourne le booléen d'une value arrivée.

    par le sérializer, on surcharge la methode to_internal_value de la donnée du sérializer
        :return: valeur corrigée.
    """

    TRUE_VALUES = serializers.BooleanField.TRUE_VALUES | {"oui", "o", 1.0, "x"}
    FALSE_VALUES = serializers.BooleanField.FALSE_VALUES | {"non", "n", "-"}
    NULL_VALUES = serializers.BooleanField.NULL_VALUES | {"nul", "nulle"}

    def to_internal_value(self, data):
        """Remplace les valeurs estimées par défaut en true, false ou NULL drf."""
        try:
            int_data = int(Decimal(data))
        except (InvalidOperation, TypeError, ValueError):
            pass
        else:
            # négatif ou nul -> False, strictement positif -> True
            return int_data > 0

        try:
            if str(data) == "":
                return None

            if str(data).lower() in self.TRUE_VALUES:
                return True

            if str(data).lower() in self.FALSE_VALUES:
                return False

            if data in self.NULL_VALUES and self.allow_null:
                return None

        except TypeError:
            pass

        raise serializers.ValidationError(
            self.error_messages["invalid"].format(input=data), code="invalid"
        )


class MaxLenghtCharField(serializers.CharField):
    """Surcharge de la class serializers.BooleanField, qui tronque la value arrivée par le.

    sérializer à la valeur de max_lenght field, on surcharge la methode to_internal_value de
    la donnée du sérializer
        :return: valeur corrigée.
    """

    def to_internal_value(self, data):
        """Tronque les valeur par le max_length drf."""
        if isinstance(data, bool) or not isinstance(data, (str, int, float)):
            self.fail("invalid")

        value = str(data).strip()
        return value[: self.max_length]
