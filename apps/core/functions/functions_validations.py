"""Module pour validation des données à inserrer, avec des instances de
    - forms.Form et forms.ModelForm de Django
    - serializers.Serializer et serializers.ModelSerializer de DRF
    - BaseModel de Pydantic
    - ModelSchema de Djantic

Commentaire:

created at: 2021-10-30
created by: Paulo ALVES

modified at: 2021-10-30
modified by: Paulo ALVES
"""
from pydantic import BaseModel, EmailStr


class CheckEmail(BaseModel):
    """Check un email par pydantic"""
    email: EmailStr


class Validation:
    """
    Validation des modèles de données à intégrer en base
    """
