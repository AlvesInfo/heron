# pylint: disable=C0330, C0411, C0303, E1101, C0413, I1101
"""Module pour validation par un ModelSerializer rest_framework,
de l'intégration en masse d'utilisateurs

Commentaire:

created at: 2021-10-30
created by: Paulo ALVES

modified at: 2021-10-30
modified by: Paulo ALVES
"""
from rest_framework import serializers

from apps.users.models import User


class UsersSerializer(serializers.ModelSerializer):
    """Serializeur pour validation des données à insèrer"""

    def to_internal_value(self, data):
        """Préparation à la validation des champs du modèle
            :param data: données de type dictionnaire,
                         qui arrive de l'instanciation du sérializeur
            :return : Retourne les valeurs modifiées à la validation de la classe mère
        """
        # Pour les champs que l'on veut tronquer pour ne pas avoir d'erreur,
        # afin d'insérer quand en base la donnée
        truncated_fields = {
            "username",
            "first_name",
            "last_name",
            "fonction",
        }

        for field in truncated_fields:
            if (
                field in self.fields
                and data.get(field)
                and self.fields[field].max_length
            ):
                data[field] = str(data[field])[: self.fields[field].max_length]

        return super().to_internal_value(data)

    class Meta:
        """class Meta du ModelSerializer"""

        model = User
        exclude = ["id", "date_joined"]


class UsersSerializerUsers(serializers.ModelSerializer):
    """Serializeur pour validation des données à insèrer"""

    def to_internal_value(self, data):
        """Préparation à la validation des champs du modèle
            :param data: données de type dictionnaire,
                         qui arrive de l'instanciation du sérializeur
            :return : Retourne les valeurs modifiées à la validation de la classe mère
        """
        # Mise en minuscule pour les emails
        data["email"] = str(data["email"]).lower()

        # Pour les champs que l'on veut tronqué pour ne pas avoir d'erreur,
        # afin d'insérer quand en base les donnée
        truncated_fields = {
            "username",
            "first_name",
            "last_name",
            "fonction",
        }

        for field in truncated_fields:

            if field == "fonction":
                data[field] = data[field] or "Utilisateur"

            if (
                field in self.fields
                and data.get(field)
                and self.fields[field].max_length
            ):
                data[field] = str(data[field])[: self.fields[field].max_length]

        return super().to_internal_value(data)

    class Meta:
        """class Meta du ModelSerializer"""

        model = User
        exclude = ["id", "date_joined"]