# pylint: disable=C0103, R1710
"""Module pour changement sur validation des champs d'un serializer

Commentaire:

created at: 2022-11-13
created by: Paulo ALVES

modified at: 2021-02-14
modified by: Paulo ALVES
"""
from decimal import Decimal, InvalidOperation

from rest_framework import serializers
from rest_framework.serializers import ModelSerializer
from rest_framework.exceptions import ValidationError


class StrictBooleanField(serializers.BooleanField):
    """Surcharge de la class serializers.BooleanField, qui retourne le booléen d'une value arrivée
    par le sérializer, on surcharge la methode to_internal_value de la donnée du sérializer
        :return: valeur corrigée
    """

    def to_internal_value(self, data):
        """remplace les valeur estimées par défaut en true ou false drf"""
        self.TRUE_VALUES = self.TRUE_VALUES | {"oui", "o", 1.0, "x"}
        self.FALSE_VALUES = self.FALSE_VALUES | {"non", "n", "-"}
        self.NULL_VALUES = self.FALSE_VALUES | {"nul", "nulle"}

        try:
            int_data = int(Decimal(data))

            if int_data < 0:
                return False

            return int_data != 0

        except InvalidOperation:
            pass

        try:
            if str(data) == "":
                return False

            if str(data).lower() in self.TRUE_VALUES:
                return True

            if str(data).lower() in self.FALSE_VALUES:
                return False

            if data in self.NULL_VALUES and self.allow_null:
                return False

        except TypeError:
            pass

        self.fail("invalid", input=data)


class NullBooleanField(serializers.BooleanField):
    """Surcharge de la class serializers.BooleanField, qui retourne le booléen d'une value arrivée
    par le sérializer, on surcharge la methode to_internal_value de la donnée du sérializer
        :return: valeur corrigée
    """

    def to_internal_value(self, data):
        """remplace les valeurs estimées par défaut en true, false ou NULL drf"""
        self.TRUE_VALUES = self.TRUE_VALUES | {"oui", "o", 1.0, "x"}
        self.FALSE_VALUES = self.FALSE_VALUES | {"non", "n", "-"}
        self.NULL_VALUES = self.NULL_VALUES | {"nul", "nulle"}
        try:
            int_data = int(Decimal(data))

            if int_data < 0:
                return False

            return int_data != 0

        except InvalidOperation:
            pass

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

        self.fail("invalid", input=data)


class MaxLenghtCharField(serializers.CharField):
    """Surcharge de la class serializers.BooleanField, qui tronque la value arrivée par le
    sérializer à la valeur de max_lenght field, on surcharge la methode to_internal_value de
    la donnée du sérializer
        :return: valeur corrigée
    """

    def to_internal_value(self, data):
        """tronque les valeur par le max_length drf"""
        if isinstance(data, bool) or not isinstance(data, (str, int, float)):
            self.fail("invalid")

        value = str(data).strip()
        return value[: self.max_length]


class ZeroIntegerField(serializers.IntegerField):
    """Surcharge de la class serializers.IntegerField,  qui retourne l'entier ou 0 si pas de valeur
    d'une value arrivée par le sérializer, on surcharge la methode to_internal_value de
    la donnée du sérializer
        :return: valeur corrigée
    """

    def to_internal_value(self, data):
        """remplace les valeur estimée par défaut en 0 drf"""
        try:
            test_data = str(data)

            if test_data in {"None", ""}:
                return 0

            if "." in test_data and "," in test_data:
                for letter in test_data:
                    if letter == ",":
                        test_data = test_data.replace(",", "")
                        break
                    if letter == ".":
                        test_data = test_data.replace(".", "")
                        break

            test_data = test_data.replace(",", ".")
            return int(Decimal(test_data))

        except (InvalidOperation, ValueError, TypeError):
            pass

        self.fail("invalid")


class ChoicesIntField(serializers.ChoiceField):
    """Surcharge de la class serializers.ChoiceField, qui retourne la clé int d'une value arrivée
    par le sérializer, on surcharge la methode to_internal_value de la donnée du sérializer
        :return: valeur corrigée
    """

    def to_internal_value(self, data):
        """remplace les valeur estimée par défaut en dictionnaires des Choices drf"""
        dict_criticite = dict(self.choices)
        try:
            valeur = str(data)
            reverse_dict = {str(value).lower(): key for key, value in dict_criticite.items()}

            if valeur.lower() in reverse_dict:
                return reverse_dict.get(valeur.lower())

            if int(valeur) in dict_criticite:
                return int(str(data))

        except ValueError:
            pass

        criticite = (
            str(dict_criticite)
            .replace('"', "'")
            .replace("{", "")
            .replace("}", "")
            .replace(": ", "=")
        )
        raise ValidationError(
            r"la valeur de criticité doit être dans les valeurs suivantes : " rf"{criticite}"
        )


class ChoicesCharField(serializers.ChoiceField):
    """Surcharge de la class serializers.ChoiceField, qui retourne la clé str d'une value arrivée
    par le sérializer, on surcharge la methode to_internal_value de la donnée du sérializer
        :return: valeur corrigée
    """

    def to_internal_value(self, data):
        """remplace les valeur estimée par défaut en dictionnaires des Choices drf"""
        dict_criticite = dict(self.choices)
        try:
            valeur = str(data)
            reverse_dict = {str(value).lower(): key for key, value in dict_criticite.items()}

            if valeur.lower() in reverse_dict:
                return reverse_dict.get(valeur.lower())

            if valeur.lower() in dict_criticite:
                return dict_criticite.get(valeur.lower())

        except (ValueError, AttributeError):
            pass

        raise ValidationError(
            r"la valeur de criticité doit être dans les valeurs suivantes : " rf"{dict_criticite}"
        )
