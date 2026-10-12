"""Sérialiseurs DRF de l'application book."""

from rest_framework import serializers


class SageEmailForm(serializers.Serializer):
    """Sérialiseur de l'adresse e-mail d'un tiers Sage."""

    email = serializers.EmailField()
