# pylint: disable=E0401,R0903
"""
FR : Module de préparation à l'import des factures fournisseurs
EN : Preparation module for importing supplier invoices

Commentaire:

created at: 2024-08-05
created by: Paulo ALVES

modified at: 2024-08-05
modified by: Paulo ALVES
"""
from django.db import models

from heron.models import FlagsTable

from apps.accountancy.models import SectionSage
from apps.book.models.base_sage_models import Society
from apps.centers_clients.models import Maison
from apps.centers_purchasing.models import Signboard


class SignboardExclusion(FlagsTable):
    """
    Table des enseignes à exclure des rfa
    FR : Table des exclusions Rfa par enseignes
    EN : Table of RFA exclusions by brand
    """
    signboard = models.OneToOneField(
        Signboard,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        to_field="code",
        verbose_name="enseigne",
        related_name="signboard_rfa",
        db_column="signboard",
        unique=True
    )

    class Meta:
        """class Meta du modèle django"""

        ordering = ["signboard"]


class ClientExclusion(FlagsTable):
    """
    Table des maisons à exclure des rfa
    FR : Table des maisons à exclure des rfa
    EN : Table of clients to exclude from RFA
    """
    cct = models.OneToOneField(
        Maison,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        to_field="cct",
        verbose_name="cct/maison",
        related_name="cct_rfa",
        db_column="cct",
        unique=True,
        limit_choices_to={'type_x3': (1, 2), "cct__active": True}
    )

    class Meta:
        """class Meta du modèle django"""

        ordering = ["cct"]


class SupplierRate(FlagsTable):
    """
    Table des taux de rfa par fournisseurs
    FR : Table des taux de rfa par fournisseurs
    EN : Table of RFA rates by suppliers
    """
    supplier = models.OneToOneField(
        Society,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        to_field="third_party_num",
        verbose_name="fournisseur",
        related_name="supplier_rfa",
        db_column="supplier",
        unique=True,
        limit_choices_to={'in_use': True}
    )
    rfa_rate = models.DecimalField(max_digits=20, decimal_places=5, default=0)

    class Meta:
        """class Meta du modèle django"""

        ordering = ["supplier"]


class SectionRfa(FlagsTable):
    """
    Table des Rfa à prendre en compte par section rfa Sage
    FR : Table des Rfa par section rfa Sage
    EN : Table of RFA by section RFA Sage
    """
    axe_rfa = models.OneToOneField(
        SectionSage,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        to_field="uuid_identification",
        verbose_name="axe RFA",
        related_name="section_rfa_rfa",
        db_column="axe_rfa",
        unique=True,
        limit_choices_to={'axe': "RFA"}
    )

    class Meta:
        """class Meta du modèle django"""

        ordering = ["axe_rfa"]


class SectionProExclusion(FlagsTable):
    """
    Table des exclusions Rfa par section Pro Sage
    FR : Table des exclusions Rfa par section Pro Sage
    EN : Table of Rfa exclusions by Sage section Pro
    """
    axe_pro = models.OneToOneField(
        SectionSage,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        to_field="uuid_identification",
        verbose_name="section Pro",
        related_name="section_pro_rfa",
        db_column="axe_pro",
        unique=True,
        limit_choices_to={'axe': "PRO"}
    )

    class Meta:
        """class Meta du modèle django"""

        ordering = ["axe_pro"]
