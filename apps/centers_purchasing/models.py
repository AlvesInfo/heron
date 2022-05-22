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

from heron.models import FlagsTable
from apps.countries.models import Country
from apps.parameters.models import SalePriceCategory


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
    comment = models.TextField(null=True, blank=True, verbose_name="Commentaire")

    def __str__(self):
        """Texte renvoyé dans les selects et à l'affichage de l'objet"""
        return f"{self.code} - {self.name}"

    @staticmethod
    def get_absolute_url():
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
        to_field="name",
        verbose_name="Catégorie de prix générique",
        db_column="sale_price_category",
    )
    name = models.CharField(unique=True, max_length=80, verbose_name="Nom")
    logo = models.ImageField(null=True, upload_to="logos/", verbose_name="logo")
    generic_coefficient = models.DecimalField(
        max_digits=20, decimal_places=5, default=1, verbose_name="Coef. générique"
    )
    language = models.ForeignKey(
        Country,
        on_delete=models.PROTECT,
        to_field="country",
        verbose_name="langue",
        db_column="language",
    )
    comment = models.TextField(null=True, blank=True, verbose_name="Commentaire")

    def __str__(self):
        """Texte renvoyé dans les selects et à l'affichage de l'objet"""
        return f"{self.code} - {self.name}"

    @staticmethod
    def get_absolute_url():
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
        return self.name

    @staticmethod
    def get_absolute_url():
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
        return reverse("centers_purchasing:translates_enseigne_list")

    class Meta:
        """class Meta du modèle django"""

        ordering = ["sign_board_model", "translation"]
        unique_together = (("sign_board_model", "translation"),)


class TranslationParamaters(FlagsTable):
    """
    Table des toutes les variables à interpoler dans les modèles
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
        return reverse("centers_purchasing:translate_parameters_list")

    class Meta:
        """class Meta du modèle django"""

        ordering = ["translation", "code"]
        unique_together = (("code", "translation"),)
