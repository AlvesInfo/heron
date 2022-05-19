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

from heron.models import FlagsTable
from apps.countries.models import Country
from apps.parameters.models import SalePriceCategory


class Action(FlagsTable):
    """
    Table des Actions. Elle permettra d'avoir une liste centralisée,
    des actions à réaliser en fonction de la centrale d'achat, ou pour des validation
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

    code = models.CharField(unique=True, max_length=15)
    name = models.CharField(max_length=80)
    generic_coefficient = models.DecimalField(
        max_digits=20, decimal_places=5, default=1, verbose_name="Coefficient niveau Centrale Mère"
    )
    comment = models.TextField(null=True, blank=True)

    def __str__(self):
        """Texte renvoyé dans les selects et à l'affichage de l'objet"""
        return f"{self.code} - {self.name}"

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

    code = models.CharField(unique=True, max_length=15)
    base_center = models.ForeignKey(
        PrincipalCenterPurchase,
        on_delete=models.PROTECT,
        to_field="code",
        verbose_name="centrale mère",
        db_column="base_center",
    )
    name = models.CharField(max_length=80)
    generic_coefficient = models.DecimalField(
        max_digits=20, decimal_places=5, default=1, verbose_name="coefficient niveau Centrale Fille"
    )
    comment = models.TextField(null=True, blank=True)

    def __str__(self):
        """Texte renvoyé dans les selects et à l'affichage de l'objet"""
        return f"{self.code} - {self.name}"

    class Meta:
        """class Meta du modèle django"""

        ordering = ["base_center", "name"]


class Signboard(FlagsTable):
    """
    Enseigne, qui va refacturer. Elle porte le logo, le facing de la facture et les textes et mails.
    L'enseigne est relié et dépendante d'une centrale fille.
    FR : Enseigne
    EN : Signboard
    """

    code = models.CharField(unique=True, max_length=15)
    sale_price_category = models.ForeignKey(
        SalePriceCategory,
        on_delete=models.PROTECT,
        to_field="name",
        verbose_name="Catégorie de prix générique",
        db_column="sale_price_category",
    )
    name = models.CharField(unique=True, max_length=80)
    logo = models.ImageField(null=True, upload_to="logos")
    generic_coefficient = models.DecimalField(max_digits=20, decimal_places=5, default=1)
    language = models.ForeignKey(
        Country,
        on_delete=models.PROTECT,
        to_field="country",
        verbose_name="langue",
        db_column="language",
    )
    comment = models.TextField(null=True, blank=True)

    def __str__(self):
        """Texte renvoyé dans les selects et à l'affichage de l'objet"""
        return f"{self.code} - {self.name}"

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
    )
    name = models.CharField(unique=True, max_length=80)
    short_name = models.CharField(null=True, blank=True, max_length=20)
    action = models.CharField(null=True, blank=True, max_length=80)
    comment = models.TextField(null=True, blank=True)

    def __str__(self):
        """Texte renvoyé dans les selects et à l'affichage de l'objet"""
        return f"{self.sign_board} - {self.name}"

    class Meta:
        """class Meta du modèle django"""

        ordering = ["sign_board", "name"]


class Translation(FlagsTable):
    """
    Table des traductions des modéles pour les enseignes
    FR : Traductions
    EN : Translations
    """

    name = models.CharField(unique=True, max_length=80)
    short_name = models.CharField(null=True, blank=True, max_length=20)
    french_text = models.TextField()
    german_text = models.TextField(null=True, blank=True)
    italian_text = models.TextField(null=True, blank=True)
    spanih_text = models.TextField(null=True, blank=True)
    polish_text = models.TextField(null=True, blank=True)
    romanian_text = models.TextField(null=True, blank=True)
    dutch_text = models.TextField(null=True, blank=True)
    flemish_text = models.TextField(null=True, blank=True)
    greek_text = models.TextField(null=True, blank=True)
    hungarian_text = models.TextField(null=True, blank=True)
    portuguese_text = models.TextField(null=True, blank=True)
    czech_text = models.TextField(null=True, blank=True)
    swedish_text = models.TextField(null=True, blank=True)
    bulgarian_text = models.TextField(null=True, blank=True)
    english_text = models.TextField(null=True, blank=True)
    slovak_text = models.TextField(null=True, blank=True)
    danish_text = models.TextField(null=True, blank=True)
    norwegian_text = models.TextField(null=True, blank=True)
    finnish_text = models.TextField(null=True, blank=True)
    lithuanian_text = models.TextField(null=True, blank=True)
    croatian_text = models.TextField(null=True, blank=True)
    slovene_text = models.TextField(null=True, blank=True)
    estonian_text = models.TextField(null=True, blank=True)
    irish_text = models.TextField(null=True, blank=True)
    latvian_text = models.TextField(null=True, blank=True)
    maltese_text = models.TextField(null=True, blank=True)

    def __str__(self):
        """Texte renvoyé dans les selects et à l'affichage de l'objet"""
        return self.name

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
    )
    translation = models.ForeignKey(
        Translation,
        on_delete=models.PROTECT,
        to_field="name",
        related_name="translation_translate",
        db_column="translation",
    )

    # Identification
    uuid_identification = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)

    def __str__(self):
        """Texte renvoyé dans les selects et à l'affichage de l'objet"""
        return f"{self.sign_board_model} - {self.translation}"

    class Meta:
        """class Meta du modèle django"""

        ordering = ["sign_board_model", "translation"]


class TranslationParamaters(FlagsTable):
    """
    Table des toutes les variables à interpoler dans les modèles
    FR : Interpolations
    EN : Interpolations
    """

    translation = models.ForeignKey(
        SignboardModelTranslate,
        on_delete=models.PROTECT,
        to_field="uuid_identification",
        related_name="parameter_model_translate",
        db_column="translation",
    )
    prefix_suffix = models.CharField(max_length=1, default="$")
    model = models.CharField(max_length=80)
    field = models.CharField(max_length=80)

    def __str__(self):
        """Texte renvoyé dans les selects et à l'affichage de l'objet"""
        return f"{self.translation} - {self.model}"

    class Meta:
        """class Meta du modèle django"""

        ordering = ["translation", "model"]
