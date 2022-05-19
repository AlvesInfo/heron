# pylint: disable=E0401,R0903
"""
FR : Module des models des articles
EN : Article models module

Commentaire:

created at: 2021-11-07
created by: Paulo ALVES

modified at: 2021-11-07
modified by: Paulo ALVES
"""
import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _

from heron.models import DatesTable, FlagsTable
from apps.accountancy.models import TabDivSage, SectionSage
from apps.countries.models import Country
from apps.parameters.models import SubFamilly, Category, SalePriceCategory
from apps.book.models import Society


class Article(FlagsTable):
    """
    Table des Articles, catalogue des tous les fournisseurs
    FR : Articles
    EN : Items
    """

    class Unit(models.TextChoices):
        """Unit choices"""

        GR = "Grammes", _("Grammes")
        KG = "Kilo", _("Kilo")
        U = "Unité", _("Unité")
        BOITE = "Boite", _("Boite")

    supplier = models.ForeignKey(
        Society,
        on_delete=models.PROTECT,
        to_field="third_party_num",
        related_name="supplier_society",
        db_column="supplier",
    )
    reference = models.CharField(max_length=35)
    ean_code = models.CharField(null=True, blank=True, max_length=35)
    libelle = models.CharField(null=True, blank=True, max_length=150)
    libelle_heron = models.CharField(null=True, blank=True, max_length=150)
    brand = models.CharField(null=True, blank=True, max_length=80)
    manufacturer = models.CharField(null=True, blank=True, max_length=80)
    big_category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        null=True,
        to_field="name",
        related_name="big_category_category",
        db_column="big_category",
    )
    sub_familly = models.ForeignKey(
        SubFamilly,
        on_delete=models.PROTECT,
        null=True,
        to_field="name",
        related_name="sub_fmaily_subfamilly",
        db_column="sub_familly",
    )
    budget_code = models.ForeignKey(
        TabDivSage,
        null=True,
        on_delete=models.PROTECT,
        limit_choices_to={"num_table": "6100"},
        related_name="budget_code_tab_div",
        verbose_name="code budget",
        db_column="budget_code",
    )
    axe_pro_supplier = models.CharField(null=True, blank=True, max_length=10)
    axe_bu = models.ForeignKey(
        SectionSage,
        null=True,
        on_delete=models.PROTECT,
        to_field="uuid_identification",
        limit_choices_to={"axe": "BU"},
        related_name="bu_section",
        db_column="axe_bu",
    )
    axe_cct = models.ForeignKey(
        SectionSage,
        null=True,
        on_delete=models.PROTECT,
        to_field="uuid_identification",
        limit_choices_to={"axe": "CCT"},
        related_name="cct_section",
        db_column="axe_cct",
    )
    axe_prj = models.ForeignKey(
        SectionSage,
        null=True,
        on_delete=models.PROTECT,
        to_field="uuid_identification",
        limit_choices_to={"axe": "PRJ"},
        related_name="prj_section",
        db_column="axe_prj",
    )
    axe_pro = models.ForeignKey(
        SectionSage,
        null=True,
        on_delete=models.PROTECT,
        to_field="uuid_identification",
        limit_choices_to={"axe": "PRO"},
        related_name="pro_section",
        db_column="axe_pro",
    )
    axe_pys = models.ForeignKey(
        SectionSage,
        null=True,
        on_delete=models.PROTECT,
        to_field="uuid_identification",
        limit_choices_to={"axe": "PYS"},
        related_name="pys_section",
        db_column="axe_pys",
    )
    axe_rfa = models.ForeignKey(
        SectionSage,
        null=True,
        on_delete=models.PROTECT,
        to_field="uuid_identification",
        limit_choices_to={"axe": "RFA"},
        related_name="rfa_section",
        db_column="axe_rfa",
    )
    made_in = models.ForeignKey(
        Country,
        on_delete=models.PROTECT,
        to_field="country",
        related_name="made_in_country",
        null=True,
        db_column="made_in",
    )
    item_weight = models.DecimalField(max_digits=20, decimal_places=5, default=0)
    unit_weight = models.CharField(
        null=True, blank=True, max_length=20, choices=Unit.choices, default=Unit.GR
    )
    packaging_qty = models.DecimalField(max_digits=20, decimal_places=5, default=1)
    customs_code = models.CharField(null=True, blank=True, max_length=35)
    catalog_price = models.CharField(null=True, blank=True, max_length=35)
    comment = models.TextField(null=True, blank=True)
    new_article = models.BooleanField(null=True, default=False)

    # Identification
    uuid_identification = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)

    def __str__(self):
        """Texte renvoyé dans les selects et à l'affichage de l'objet"""
        return f"{self.supplier} - {self.reference} - {self.libelle_heron}"

    class Meta:
        """class Meta du modèle django"""

        ordering = ["reference", "ean_code"]
        unique_together = (("supplier", "reference", "ean_code"),)


class SellingPrice(FlagsTable):
    """
    Table des prix d'un article par catégorie de prix, par exemple pour une enseigne en particulier,
    ou lorqu'on veut redéfinir un prix par devises et donc par pays
    FR : Prix de Vente
    EN : Sale Price
    """

    sale_price_category = models.ForeignKey(
        SalePriceCategory,
        on_delete=models.PROTECT,
        to_field="name",
        related_name="sale_price_sale_price_category",
        db_column="sale_price_category",
    )
    article = models.ForeignKey(
        Article,
        on_delete=models.PROTECT,
        to_field="uuid_identification",
        related_name="sale_price_article",
        db_column="article",
    )
    currency = models.CharField(max_length=3, default="EUR")
    sale_price = models.DecimalField(max_digits=20, decimal_places=5)
    comment = models.TextField(null=True, blank=True)

    # Identification
    uuid_identification = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)

    def __str__(self):
        """Texte renvoyé dans les selects et à l'affichage de l'objet"""
        return f"{self.sale_price_category} - {self.article}"

    class Meta:
        """class Meta du modèle django"""

        ordering = ["sale_price_category", "article", "currency"]
        unique_together = (("sale_price_category", "article", "currency"),)


class SalePriceHistory(DatesTable):
    """
    Table des prix de vente d'un article historisé
    FR : Prix de vente
    EN : Sale Price
    """

    sale_price_category = models.ForeignKey(
        SalePriceCategory,
        on_delete=models.PROTECT,
        to_field="name",
        related_name="history_sale_price_category",
        db_column="sale_price_category",
    )
    article = models.ForeignKey(
        Article,
        on_delete=models.PROTECT,
        to_field="uuid_identification",
        related_name="history_sale_price_article",
        db_column="article",
    )
    currency = models.CharField(max_length=3, default="EUR")
    sale_price = models.DecimalField(max_digits=20, decimal_places=5)
    start_date = models.DecimalField(max_digits=20, decimal_places=5)
    end_date = models.DecimalField(max_digits=20, decimal_places=5)

    def __str__(self):
        """Texte renvoyé dans les selects et à l'affichage de l'objet"""
        return f"{self.sale_price_category} - {self.article}"

    class Meta:
        """class Meta du modèle django"""

        ordering = ["sale_price_category", "article"]
        unique_together = (("sale_price_category", "article", "currency", "start_date"),)


class Subscription(FlagsTable):
    """
    Table des abbonements. Les abonnements vont servir à refacturer sur la période
    tous les articles abbonés
    FR : Abonnement
    EN : Subscription
    """

    name = models.CharField(unique=True, max_length=80)

    def __str__(self):
        """Texte renvoyé dans les selects et à l'affichage de l'objet"""
        return self.name

    class Meta:
        """class Meta du modèle django"""

        ordering = ["name"]


class SubscriptionArtcile(FlagsTable):
    """
    Table des articles pour un abbonement donné, avec une relation Many to Many
    FR : Article / Abonnement
    EN : Item / Subscription
    """

    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.PROTECT,
        to_field="name",
        related_name="subscription_subscription_article",
        db_column="subscription",
    )
    selling_price = models.ForeignKey(
        SellingPrice,
        on_delete=models.PROTECT,
        to_field="uuid_identification",
        related_name="selling_price_selling_price",
        db_column="selling_price",
    )
    qty = models.DecimalField(decimal_places=5, default=1, max_digits=20, verbose_name="quantité")

    def __str__(self):
        """Texte renvoyé dans les selects et à l'affichage de l'objet"""
        return f"{self.subscription} - {self.selling_price}"

    class Meta:
        """class Meta du modèle django"""

        ordering = ["subscription", "selling_price"]
        unique_together = (("subscription", "selling_price"),)


class SupplierArticleAxePro(FlagsTable):
    """
    Nommage des familles à appliquer pour les fournisseurs
    """
    name = models.CharField(unique=True, max_length=80)

    # Identification
    uuid_identification = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)


class FamilleAxePro(FlagsTable):
    """
    Table des statistiques liées à l'axe pro
    """

    name = models.ForeignKey(
        SupplierArticleAxePro,
        on_delete=models.PROTECT,
        to_field="name",
        related_name="famille_axe_pro_section",
        db_column="name",
    )
    familly_type = models.CharField(null=True, blank=True, max_length=80)
    supplier_axe = models.CharField(null=True, blank=True, max_length=80)
    supplier_familly = models.CharField(max_length=80)
    axe_pro = models.ForeignKey(
        SectionSage,
        on_delete=models.PROTECT,
        to_field="uuid_identification",
        limit_choices_to={"axe": "PRO"},
        related_name="famille_axe_pro_section",
        db_column="axe_pro",
    )
    comment = models.CharField(null=True, blank=True, max_length=150)
    regex = models.CharField(null=True, blank=True, max_length=150)

    # Identification
    uuid_identification = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)

    def __str__(self):
        """Texte renvoyé dans les selects et à l'affichage de l'objet"""
        return f"{self.name} - {self.supplier_familly} - {self.axe_pro}"

    class Meta:
        """class Meta du modèle django"""

        unique_together = (("name", "supplier_familly"),)
