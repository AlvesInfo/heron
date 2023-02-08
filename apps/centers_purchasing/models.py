# pylint: disable=E0401,R0903
"""
FR : Module de la centrale d'achat
EN : Central purchasing module

Commentaire:

created at: 2021-11-07
created by: Paulo ALVES

modified at: 2021-11-07
modified by: Paulo ALVES
"""
import uuid

from django.db import models
from django.shortcuts import reverse
from django.utils.translation import gettext_lazy as _

from heron.models import FlagsTable
from apps.accountancy.models import (
    AccountSage,
    VatSage,
    SectionSage,
)
from apps.parameters.models import SalePriceCategory, Category, SubCategory


class Action(FlagsTable):
    """
    Table des Actions. Elle permettra d'avoir une liste centralisée,
    des actions à réaliser en fonction de la centrale d'achat, ou pour des validations
    ou modifications de valeurs à la volée.
    FR : Actions
    EN : Actions
    """

    ...


class PrincipalCenterPurchase(FlagsTable):
    """
    Table de la centrale mère. Elle est isolée des centrales filles
    pour des diagrammes ultérieurs ou différents
    FR : Centrale Mère
    EN : Principal Center Purchase
    """

    code = models.CharField(unique=True, max_length=15, verbose_name="code")
    name = models.CharField(max_length=80, verbose_name="Nom")
    generic_coefficient = models.DecimalField(
        max_digits=20, decimal_places=5, default=1, verbose_name="Coef. Centrale Mère"
    )
    comment = models.TextField(null=True, blank=True, verbose_name="Commentaire")

    def __str__(self):
        """Texte renvoyé dans les selects et à l'affichage de l'objet"""
        return f"{self.code} - {self.name}"

    @staticmethod
    def get_absolute_url():
        """Url de retour après create ou Update"""
        return reverse("centers_purchasing:meres_list")

    class Meta:
        """class Meta du modèle django"""

        ordering = ["name"]


class ChildCenterPurchase(FlagsTable):
    """
    Table des centrales filles. Elle est isolée de la Centrale Mère
    pour des diagrammes ultérieurs ou différents.
    FR : Centrale Fille
    EN : Child Center Purchase
    """

    code = models.CharField(unique=True, max_length=15, verbose_name="code")
    base_center = models.ForeignKey(
        PrincipalCenterPurchase,
        on_delete=models.PROTECT,
        to_field="code",
        verbose_name="centrale mère",
        db_column="base_center",
    )
    name = models.CharField(max_length=80, verbose_name="Nom")
    generic_coefficient = models.DecimalField(
        max_digits=20, decimal_places=5, default=1, verbose_name="Coef. Centrale Fille"
    )
    site_fcy_x3 = models.CharField(max_length=5, verbose_name="Site X3")
    comment = models.TextField(null=True, blank=True, verbose_name="Commentaire")
    legal_notice = models.TextField(null=True, blank=True, verbose_name="mentions légales")
    iban = models.CharField(null=True, blank=True, max_length=50)
    code_swift = models.CharField(null=True, blank=True, max_length=27)
    # email d'où sont envoyés les documents, ou bien qui reçoivent les mails
    sending_email = models.EmailField(null=True, blank=True, verbose_name="email d'envoi")

    def __str__(self):
        """Texte renvoyé dans les selects et à l'affichage de l'objet"""
        return f"{self.code} - {self.name}"

    @staticmethod
    def get_absolute_url():
        """Url de retour après create ou Update"""
        return reverse("centers_purchasing:filles_list")

    class Meta:
        """class Meta du modèle django"""

        ordering = ["base_center", "name"]
        unique_together = (("code", "base_center"),)


class Signboard(FlagsTable):
    """
    Enseigne, qui va refacturer. Elle porte le logo, le facing de la facture et les textes et mails.
    L'enseigne est relié et dépendante d'une centrale fille.
    FR : Enseigne
    EN : Signboard
    """

    code = models.CharField(unique=True, max_length=15, verbose_name="code")
    sale_price_category = models.ForeignKey(
        SalePriceCategory,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        to_field="uuid_identification",
        verbose_name="categorie de prix",
        related_name="enseigne_sale_price_category",
        db_column="uuid_sale_price_category",
    )
    name = models.CharField(unique=True, max_length=80, verbose_name="Nom")
    logo = models.ImageField(null=True, blank=True, upload_to="logos/", verbose_name="logo")
    generic_coefficient = models.DecimalField(
        max_digits=20, decimal_places=5, default=1, verbose_name="Coef. générique"
    )
    comment = models.TextField(null=True, blank=True, verbose_name="Commentaire")
    child_center = models.ForeignKey(
        ChildCenterPurchase,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        to_field="code",
        verbose_name="centrale fille",
        related_name="enseigne_centrale_fille",
        db_column="child_center",
    )

    def __str__(self):
        """Texte renvoyé dans les selects et à l'affichage de l'objet"""
        return f"{self.code} - {self.name}"

    @staticmethod
    def get_absolute_url():
        """Url de retour après create ou Update"""
        return reverse("centers_purchasing:enseignes_list")

    class Meta:
        """class Meta du modèle django"""

        ordering = ["name"]


class SignboardModel(FlagsTable):
    """
    Tous les modèles (email, textes, pieds de page, ....), que l'enseigne va utiliser.
    FR : Modèles pour les Enseignes
    EN : Templates for Signs
    """

    sign_board = models.ForeignKey(
        Signboard,
        on_delete=models.PROTECT,
        to_field="code",
        db_column="sign_board",
        verbose_name="Enseigne",
    )
    name = models.CharField(unique=True, max_length=80, verbose_name="Nom")
    short_name = models.CharField(null=True, blank=True, max_length=20, verbose_name="Intitulé")
    action = models.CharField(null=True, blank=True, max_length=80, verbose_name="action")
    comment = models.TextField(null=True, blank=True, verbose_name="commentaire")

    def __str__(self):
        """Texte renvoyé dans les selects et à l'affichage de l'objet"""
        return f"{self.sign_board} - {self.name}"

    @staticmethod
    def get_absolute_url():
        """Url de retour après create ou Update"""
        return reverse("centers_purchasing:models_enseigne_list")

    class Meta:
        """class Meta du modèle django"""

        ordering = ["sign_board", "name"]
        unique_together = (("sign_board", "name"),)


class Translation(FlagsTable):
    """
    Table des traductions des modéles pour les enseignes
    FR : Traductions
    EN : Translations
    """

    name = models.CharField(unique=True, max_length=80, verbose_name="nom")
    short_name = models.CharField(null=True, blank=True, max_length=20, verbose_name="intitulé")
    french_text = models.TextField(verbose_name="français")
    german_text = models.TextField(null=True, blank=True, verbose_name="allemand")
    italian_text = models.TextField(null=True, blank=True, verbose_name="italien")
    spanih_text = models.TextField(null=True, blank=True, verbose_name="espagnol")
    polish_text = models.TextField(null=True, blank=True, verbose_name="polonais")
    romanian_text = models.TextField(null=True, blank=True, verbose_name="rounmain")
    dutch_text = models.TextField(null=True, blank=True, verbose_name="hollandais")
    flemish_text = models.TextField(null=True, blank=True, verbose_name="flamand")
    greek_text = models.TextField(null=True, blank=True, verbose_name="grèque")
    hungarian_text = models.TextField(null=True, blank=True, verbose_name="hongrois")
    portuguese_text = models.TextField(null=True, blank=True, verbose_name="portugais")
    czech_text = models.TextField(null=True, blank=True, verbose_name="tchèque")
    swedish_text = models.TextField(null=True, blank=True, verbose_name="suèdois")
    bulgarian_text = models.TextField(null=True, blank=True, verbose_name="bulgare")
    english_text = models.TextField(null=True, blank=True, verbose_name="anglais")
    slovak_text = models.TextField(null=True, blank=True, verbose_name="slovaque")
    danish_text = models.TextField(null=True, blank=True, verbose_name="danois")
    norwegian_text = models.TextField(null=True, blank=True, verbose_name="norvégien")
    finnish_text = models.TextField(null=True, blank=True, verbose_name="finlandais")
    lithuanian_text = models.TextField(null=True, blank=True, verbose_name="lithuanien")
    croatian_text = models.TextField(null=True, blank=True, verbose_name="croate")
    slovene_text = models.TextField(null=True, blank=True, verbose_name="slovène")
    estonian_text = models.TextField(null=True, blank=True, verbose_name="estonien")
    irish_text = models.TextField(null=True, blank=True, verbose_name="irlandais")
    latvian_text = models.TextField(null=True, blank=True, verbose_name="letton")
    maltese_text = models.TextField(null=True, blank=True, verbose_name="malte")

    def __str__(self):
        """Texte renvoyé dans les selects et à l'affichage de l'objet"""
        return f"{self.name}"

    @staticmethod
    def get_absolute_url():
        """Url de retour après create ou Update"""
        return reverse("centers_purchasing:translate_list")

    class Meta:
        """class Meta du modèle django"""

        ordering = ["name"]


class SignboardModelTranslate(FlagsTable):
    """
    Table many to many pour les Modèles des Enseignes / Traductions
    FR : Modèles des Enseignes / Traductions
    EN : Sign Templates / Translations
    """

    sign_board_model = models.ForeignKey(
        SignboardModel,
        on_delete=models.PROTECT,
        to_field="name",
        related_name="sign_board_translate",
        db_column="sign_board_model",
        verbose_name="modèle",
    )
    translation = models.ForeignKey(
        Translation,
        on_delete=models.PROTECT,
        to_field="name",
        related_name="translation_translate",
        db_column="translation",
        verbose_name="traduction",
    )

    # Identification
    uuid_identification = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)

    def __str__(self):
        """Texte renvoyé dans les selects et à l'affichage de l'objet"""
        return f"{self.sign_board_model} - {self.translation}"

    @staticmethod
    def get_absolute_url():
        """Url de retour après create ou Update"""
        return reverse("centers_purchasing:translates_enseigne_list")

    class Meta:
        """class Meta du modèle django"""

        ordering = ["sign_board_model", "translation"]
        unique_together = (("sign_board_model", "translation"),)


class TranslationParamaters(FlagsTable):
    """
    Table de toutes les variables à interpoler dans les modèles
    FR : Interpolations
    EN : Interpolations
    """

    code = models.CharField(unique=True, max_length=80, verbose_name="code")
    translation = models.ForeignKey(
        SignboardModelTranslate,
        on_delete=models.PROTECT,
        to_field="uuid_identification",
        related_name="parameter_model_translate",
        db_column="translation",
        verbose_name="traduction",
    )
    prefix_suffix = models.CharField(max_length=1, default="$", verbose_name="prefix")
    field = models.CharField(max_length=80, verbose_name="champ")

    def __str__(self):
        """Texte renvoyé dans les selects et à l'affichage de l'objet"""
        return f"{self.code} - {self.translation}"

    @staticmethod
    def get_absolute_url():
        """Url de retour après create ou Update"""
        return reverse("centers_purchasing:translate_parameters_list")

    class Meta:
        """class Meta du modèle django"""

        ordering = ["translation", "code"]
        unique_together = (("code", "translation"),)


class GroupingGoods(FlagsTable):
    """Table des regroupements de refacturation de marchandises"""

    ranking = models.IntegerField()
    base = models.CharField(max_length=35, verbose_name="base refac")
    grouping_goods = models.CharField(unique=True, max_length=35, verbose_name="regroupement")

    # Identification
    uuid_identification = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)

    def __str__(self):
        """Texte renvoyé dans les selects et à l'affichage de l'objet"""
        return f"{self.ranking} - {self.base} - {self.grouping_goods}"

    class Meta:
        """class Meta du modèle django"""

        ordering = ["ranking"]
        unique_together = (("base", "grouping_goods"),)
        indexes = [
            models.Index(fields=["base"]),
            models.Index(fields=["grouping_goods"]),
            models.Index(fields=["uuid_identification"]),
            models.Index(fields=["base", "grouping_goods"]),
            models.Index(fields=["uuid_identification", "base", "grouping_goods"]),
        ]


class AxeProGroupingGoods(FlagsTable):
    """Table associative Axe PRO/Regroupement de facturation"""

    axe_pro = models.OneToOneField(
        SectionSage,
        unique=True,
        on_delete=models.PROTECT,
        to_field="uuid_identification",
        limit_choices_to={"axe": "PRO"},
        related_name="axe_pro_grouping",
        db_column="axe_pro",
        verbose_name="axe pro",
    )
    grouping_goods = models.ForeignKey(
        GroupingGoods,
        on_delete=models.PROTECT,
        to_field="uuid_identification",
        related_name="axe_grouping_goods",
        db_column="grouping_goods",
        verbose_name="regroupement",
    )

    class Meta:
        """class Meta du modèle django"""

        ordering = ["axe_pro"]
        indexes = [
            models.Index(fields=["axe_pro"]),
            models.Index(fields=["grouping_goods"]),
            models.Index(fields=["axe_pro", "grouping_goods"]),
        ]


class AxeProFamilleAcuitis(FlagsTable):
    """Table des axes par défaut pour les familles de produits Acuitis"""

    class Unit(models.TextChoices):
        """Unit choices"""

        GR = "Grammes", _("Grammes")
        KG = "Kilo", _("Kilo")
        U = "Unité", _("Unité")
        BOITE = "Boite", _("Boite")
        ML = "Mètre", _("Mètre")

    code_famille_acuitis = models.CharField(max_length=35)
    code_rayon_acuitis = models.CharField(max_length=35)
    axe_pro = models.ForeignKey(
        SectionSage,
        on_delete=models.PROTECT,
        to_field="uuid_identification",
        limit_choices_to={"axe": "PRO"},
        related_name="default_acuitis_pro_section",
        db_column="axe_pro",
        verbose_name="axe pro",
    )
    comment = models.TextField(null=True, blank=True)
    big_category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        to_field="uuid_identification",
        related_name="acuitis_family_big_category",
        db_column="uuid_big_category",
        null=True,
    )
    sub_category = models.ForeignKey(
        SubCategory,
        on_delete=models.PROTECT,
        to_field="uuid_identification",
        related_name="acuitis_family_sub_category",
        db_column="uuid_sub_big_category",
        null=True,
    )
    item_weight = models.DecimalField(max_digits=20, decimal_places=5, default=0)
    unit_weight = models.CharField(
        null=True, blank=True, max_length=20, choices=Unit.choices, default=Unit.GR
    )
    customs_code = models.CharField(null=True, blank=True, max_length=35)

    # Identification
    uuid_identification = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)

    class Meta:
        """class Meta du modèle django"""

        ordering = ["code_famille_acuitis", "code_rayon_acuitis"]
        unique_together = (("code_famille_acuitis", "code_rayon_acuitis"),)
        indexes = [
            models.Index(fields=["code_famille_acuitis"]),
            models.Index(fields=["code_rayon_acuitis"]),
            models.Index(fields=["axe_pro"]),
            models.Index(
                fields=["code_famille_acuitis", "code_rayon_acuitis", "axe_pro"]
            ),
        ]


class AxeProFamilleCosium(FlagsTable):
    """Table des axes por par défaut pour les familles de produits Cosium"""

    class Unit(models.TextChoices):
        """Unit choices"""

        GR = "Grammes", _("Grammes")
        KG = "Kilo", _("Kilo")
        U = "Unité", _("Unité")
        BOITE = "Boite", _("Boite")
        ML = "Mètre", _("Mètre")

    code_famille_cosium = models.CharField(unique=True, max_length=35)
    axe_pro = models.ForeignKey(
        SectionSage,
        on_delete=models.PROTECT,
        to_field="uuid_identification",
        limit_choices_to={"axe": "PRO"},
        related_name="default_cosium_pro_section",
        db_column="axe_pro",
        verbose_name="axe pro",
    )
    comment = models.TextField(null=True, blank=True)
    big_category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        to_field="uuid_identification",
        related_name="cosium_family_big_category",
        db_column="uuid_big_category",
        null=True,
    )
    sub_category = models.ForeignKey(
        SubCategory,
        on_delete=models.PROTECT,
        to_field="uuid_identification",
        related_name="cosium_family_sub_category",
        db_column="uuid_sub_big_category",
        null=True,
    )
    item_weight = models.DecimalField(max_digits=20, decimal_places=5, default=0)
    unit_weight = models.CharField(
        null=True, blank=True, max_length=20, choices=Unit.choices, default=Unit.GR
    )
    customs_code = models.CharField(null=True, blank=True, max_length=35)

    # Identification
    uuid_identification = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)

    class Meta:
        """class Meta du modèle django"""

        ordering = ["code_famille_cosium"]
        indexes = [
            models.Index(fields=["code_famille_cosium"]),
            models.Index(fields=["axe_pro"]),
            models.Index(fields=["code_famille_cosium", "axe_pro"]),
        ]


class AccountsAxeProCategory(FlagsTable):
    """Tables des comptes comptables par defaut
    en fonction de la centrale fille, la catégrorie, l'axe_pro et le taux de tva

    """

    child_center = models.ForeignKey(
        ChildCenterPurchase,
        on_delete=models.PROTECT,
        to_field="code",
        verbose_name="centrale fille",
        related_name="account_centrale_fille",
        db_column="child_center",
    )
    big_category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        null=True,
        to_field="uuid_identification",
        related_name="account_big_category",
        db_column="uuid_big_category",
    )
    axe_pro = models.ForeignKey(
        SectionSage,
        on_delete=models.PROTECT,
        to_field="uuid_identification",
        limit_choices_to={"axe": "PRO"},
        related_name="account_axe_pro",
        db_column="axe_pro",
        verbose_name="axe pro",
    )
    vat = models.ForeignKey(
        VatSage,
        on_delete=models.PROTECT,
        to_field="vat",
        related_name="account_vat",
        verbose_name="tva X3",
        db_column="vat",
    )
    purchase_account = models.ForeignKey(
        AccountSage,
        on_delete=models.PROTECT,
        to_field="uuid_identification",
        related_name="account_purchase",
        db_column="purchase_account_uuid",
        verbose_name="compte d'achat",
    )
    sale_account = models.ForeignKey(
        AccountSage,
        on_delete=models.PROTECT,
        to_field="uuid_identification",
        related_name="account_sale",
        db_column="sale_account_uuid",
        verbose_name="compte de vente",
    )

    # Identification
    uuid_identification = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)

    class Meta:
        """class Meta du modèle django"""

        unique_together = (("child_center", "big_category", "axe_pro", "vat"),)
        indexes = [
            models.Index(fields=["child_center"]),
            models.Index(fields=["big_category"]),
            models.Index(fields=["axe_pro"]),
            models.Index(fields=["vat"]),
            models.Index(
                fields=[
                    "child_center",
                    "big_category",
                    "axe_pro",
                    "vat",
                ]
            ),
        ]
