# pylint: disable=E0401,R0903,C0115
"""
FR : Module de validation par djantic des articles sans comptes
EN : Djantic validation module for articles without accounts

Commentaire:

created at: 2024-02-14
created by: Paulo ALVES

modified at: 2024-02-14
modified by: Paulo ALVES
"""
import datetime
import uuid

from django.utils import timezone
from djantic import ModelSchema

from apps.articles.models import ArticleAccount


class ArticleAccountSageSchema(ModelSchema):
    """Schema Djantic pour validation du modèle AccountSage"""

    now = timezone.now()
    created_at: datetime.datetime = now
    modified_at: datetime.datetime = now
    article: uuid.UUID = uuid.uuid4()
    child_center: str
    vat: str

    class Config:
        model = ArticleAccount
        include = list(model.get_columns_import()) + [
            "created_at",
            "modified_at",
        ]
