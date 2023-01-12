# pylint: disable=E0401,R0903
"""
Forms des Parameters
"""
from django import forms
from django.forms import inlineformset_factory

from apps.parameters.models import Category, SubCategory


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = [
            "ranking",
            "code",
            "name",
        ]


class SubCategoryForm(forms.ModelForm):

    DELETE = forms.BooleanField()

    class Meta:
        model = SubCategory
        fields = [
            "id",
            "big_category",
            "ranking",
            "code",
            "name",
        ]


InlineCategoryFormmset = inlineformset_factory(
    Category,
    SubCategory,
    form=SubCategoryForm,
    can_delete=True,
    extra=0,
)
