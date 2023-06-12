from rest_framework import serializers


class SageEmailForm(serializers.Serializer):
    email = serializers.EmailField()
