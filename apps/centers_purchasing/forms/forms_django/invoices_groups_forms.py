"""
Forms des regroupements de facturation
"""
from django import forms

from apps.centers_purchasing.models import GroupingGoods


class GroupingGoodsForm(forms.ModelForm):
    """Formulaires de la liste des Regroupements de facturation"""

    use_required_attribute = False

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

    # Le champ id (AutoField) n\'est pas généré par le ModelForm : déclaré pour valider l\'existence
    id = forms.ModelChoiceField(queryset=GroupingGoods.objects.all())

    class Meta:
        """class Meta du form django"""
        model = GroupingGoods
        fields = [
            "id",
        ]
