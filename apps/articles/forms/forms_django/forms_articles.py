# pylint: disable=E0401,R0903
"""
Forms des Parameters
"""
from django import forms

from apps.articles.models import (
    Article,
)


class ArticleForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = [
            "supplier",
            "reference",
            "libelle",
        ]
