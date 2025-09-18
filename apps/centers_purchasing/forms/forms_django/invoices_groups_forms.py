# pylint: disable=E0401,R0903
"""
Forms des regroupements de facturation
"""
from django import forms

from apps.centers_purchasing.models import GroupingGoods


class GroupingGoodsForm(forms.ModelForm):
    """Formulaires de la liste des Regroupements de facturation"""

    class Meta:
        """class Meta du form django"""
        model = GroupingGoods
        fields = [
            "ranking",
            "base",
            "grouping_goods",
        ]


class GroupingGoodsDeleteForm(forms.ModelForm):
    """Formulaires de la liste des Regroupements de facturation"""

    class Meta:
        """class Meta du form django"""
        model = GroupingGoods
        fields = [
            "id",
        ]
