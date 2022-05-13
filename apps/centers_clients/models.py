# pylint: disable=E0401,R0903
"""
FR : Module du modèle des maisons
EN : Houses model module

Commentaire:

created at: 2022-04-07
created by: Paulo ALVES

modified at: 2022-04-07
modified by: Paulo ALVES
"""
import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _

from heron.models import FlagsTable

from apps.accountancy.models import SectionSage, AccountSage
from apps.book.models import Society
from apps.centers_purchasing.models import Signboard
from apps.parameters.models import SalePriceCategory
from apps.countries.models import Country


class ClientFamilly(FlagsTable):
    """
    Tables des familles des maisons
    FR : Table des Familles
    EN : Families table
    """
    name = models.CharField(unique=True, max_length=80)
    comment = models.CharField(null=True, blank=True, max_length=255)

    def save(self, *args, **kwargs):
        """
        FR : Avant la sauvegarde on clean les données
        EN : Before the backup we clean the data
        """
        self.name = self.name.capitalize()

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        """class Meta du modèle django"""

        ordering = ["name"]


class Maison(FlagsTable):
    """
    Table des maisons
    FR : Table des Maisons
    EN : Shop table
    """
    class Frequence(models.TextChoices):
        """Frequence choices"""

        MENSUEL = 1, _("Mensuel")
        TRIMESTRIEL = 2, _("Trimestriel")
        SEMESTRIEL = 3, _("Semestriel")
        ANNUEL = 4, _("Annuel")

    class Remise(models.TextChoices):
        """Remise choices"""

        TOTAL = 1, _("Fournisseur Total")
        FAMILLE = 2, _("Famille Article")
        ARTICLE = 3, _("Article")

    cct = models.OneToOneField(
        SectionSage,
        on_delete=models.PROTECT,
        limit_choices_to={"axe": "CCT"},
        related_name="maison_cct",
        verbose_name="code maison",
        db_column="cct",
    )
    sign_board = models.ForeignKey(
        Signboard,
        on_delete=models.PROTECT,
        to_field="name",
        related_name="maison_sign_board",
        db_column="sign_board",
    )
    intitule = models.CharField(max_length=30)
    intitule_court = models.CharField(max_length=12)
    client_familly = models.ForeignKey(
        ClientFamilly,
        on_delete=models.PROTECT,
        to_field="name",
        related_name="maison_client_familly",
        db_column="client_familly",
    )

    code_maison = models.CharField(null=True, blank=True, max_length=15, verbose_name="cct")
    code_cosium = models.CharField(null=True, blank=True, max_length=15, verbose_name="code cosium")
    code_bbgr = models.CharField(null=True, blank=True, max_length=15, verbose_name="code BBGR")
    opening_date = models.DateField(null=True, verbose_name="date d'ouveture")
    closing_date = models.DateField(null=True, verbose_name="date de fermeture")
    signature_franchise_date = models.DateField(null=True, verbose_name="date de signature contrat")
    agreement_franchise_end_date = models.DateField(
        null=True, verbose_name="date de signature de fin de contrat"
    )
    agreement_renew_date = models.DateField(null=True, verbose_name="date de renouvelement contrat")
    entry_fee_amount = models.DecimalField(
        max_digits=20, decimal_places=5, null=True, verbose_name="montant de droit d'entrée"
    )
    renew_fee_amoount = models.DecimalField(
        max_digits=20,
        decimal_places=5,
        null=True,
        verbose_name="montant de droit de renouvellement",
    )
    sale_price_category = models.ForeignKey(
        SalePriceCategory,
        on_delete=models.PROTECT,
        null=True,
        to_field="name",
        verbose_name="categorie de prix",
        db_column="sale_price_category",
    )
    generic_coefficient = models.DecimalField(
        null=True,
        max_digits=20,
        decimal_places=5,
        default=1,
        verbose_name="coeficient de vente générique",
    )
    credit_account = models.ForeignKey(
        AccountSage,
        on_delete=models.PROTECT,
        null=True,
        to_field="uuid_identification",
        related_name="credit_account",
        verbose_name="compte X3 par défaut de crédit",
        db_column="credit_account",
    )
    debit_account = models.ForeignKey(
        AccountSage,
        on_delete=models.PROTECT,
        null=True,
        to_field="uuid_identification",
        related_name="debit_account",
        verbose_name="compte X3 par défaut de débit",
        db_column="debit_account",
    )
    prov_account = models.ForeignKey(
        AccountSage,
        on_delete=models.PROTECT,
        null=True,
        to_field="uuid_identification",
        related_name="prov_account",
        verbose_name="compte X3 par défaut de provision",
        db_column="prov_account",
    )
    extourne_account = models.ForeignKey(
        AccountSage,
        on_delete=models.PROTECT,
        null=True,
        to_field="uuid_identification",
        related_name="extourne_account",
        verbose_name="compte X3 par défaut d'extourne",
        db_column="extourne_account",
    )
    sage_vat_by_default = models.CharField(
        null=True, blank=True, max_length=5, verbose_name="tva X3 par défaut"
    )
    sage_plan_code = models.CharField(
        null=True, blank=True, max_length=10, verbose_name="code plan sage"
    )

    # RFA
    rfa_frequence = models.IntegerField(
        null=True,
        choices=Frequence.choices,
        default=Frequence.MENSUEL,
        verbose_name="fréquence des rfa",
    )
    rfa_remise = models.IntegerField(
        null=True,
        choices=Remise.choices,
        default=Remise.TOTAL,
        verbose_name="taux de remboursement rfa",
    )
    invoice_client_name = models.CharField(
        null=True, blank=True, max_length=80, verbose_name="Nom pour l'identifiant Client"
    )

    def save(self, *args, **kwargs):
        """
        FR : Avant la sauvegarde on clean les données
        EN : Before the backup we clean the data
        """

        if not self.code_maison:
            self.code_maison = self.cct
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.code_maison} - {self.intitule}"

    class Meta:
        ordering = ["code_maison"]


class NotExportMaisonSupllier(FlagsTable):
    cct = models.ForeignKey(
        Maison,
        on_delete=models.PROTECT,
        to_field="cct",
        related_name="maison_supplier",
        verbose_name="code maison",
        db_column="cct",
    )
    society = models.ForeignKey(
        Society,
        on_delete=models.CASCADE,
        to_field="third_party_num",
        related_name="supplier_maison",
        verbose_name="Fournisseur",
        db_column="society",
    )

    def __str__(self):
        return f"{self.cct} - {self.society}"

    class Meta:
        ordering = ["cct", "society__name"]
        unique_together = (("cct", "society"),)
