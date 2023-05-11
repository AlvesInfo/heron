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

from heron.models import DatesTable, FlagsTable
from apps.accountancy.models import TabDivSage, SectionSage, VatSage
from apps.countries.models import Country
from apps.parameters.models import SubFamilly, Category, SubCategory, SalePriceCategory, UnitChoices
from apps.book.models import Society
from apps.centers_purchasing.models import ChildCenterPurchase


class Article(FlagsTable):
    """
    Table des Articles, catalogue de tous les fournisseurs
    FR : Articles
    EN : Items
    """

    third_party_num = models.ForeignKey(
        Society,
        on_delete=models.PROTECT,
        to_field="third_party_num",
        related_name="supplier_society",
        db_column="third_party_num",
    )
    reference = models.CharField(max_length=150)
    ean_code = models.CharField(null=True, blank=True, max_length=35)
    libelle = models.CharField(null=True, blank=True, max_length=150)
    libelle_heron = models.CharField(null=True, blank=True, max_length=150)
    brand = models.CharField(null=True, blank=True, max_length=80)
    manufacturer = models.CharField(null=True, blank=True, max_length=80)
    big_category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        null=True,
        to_field="uuid_identification",
        related_name="big_category_category",
        db_column="uuid_big_category",
    )
    sub_category = models.ForeignKey(
        SubCategory,
        on_delete=models.PROTECT,
        null=True,
        to_field="uuid_identification",
        related_name="sub_category_article",
        db_column="uuid_sub_big_category",
    )
    sub_familly = models.ForeignKey(
        SubFamilly,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        to_field="uuid_identification",
        related_name="sub_fmaily_subfamilly",
        db_column="uuid_sub_familly",
    )
    budget_code = models.ForeignKey(
        TabDivSage,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        limit_choices_to={"num_table": "6100"},
        related_name="budget_code_tab_div",
        verbose_name="code budget",
        db_column="budget_code",
    )
    famille_supplier = models.CharField(null=True, blank=True, max_length=35)
    axe_pro_supplier = models.CharField(null=True, blank=True, max_length=35)
    famille_acuitis = models.CharField(null=True, blank=True, max_length=35)
    axe_pro_acuitis = models.CharField(null=True, blank=True, max_length=35)
    axe_bu = models.ForeignKey(
        SectionSage,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        to_field="uuid_identification",
        limit_choices_to={"axe": "BU"},
        related_name="bu_section",
        db_column="axe_bu",
    )
    axe_prj = models.ForeignKey(
        SectionSage,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        to_field="uuid_identification",
        limit_choices_to={"axe": "PRJ"},
        related_name="prj_section",
        db_column="axe_prj",
    )
    axe_pro = models.ForeignKey(
        SectionSage,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        to_field="uuid_identification",
        limit_choices_to={"axe": "PRO"},
        related_name="pro_section",
        db_column="axe_pro",
    )
    axe_pys = models.ForeignKey(
        SectionSage,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        to_field="uuid_identification",
        limit_choices_to={"axe": "PYS"},
        related_name="pys_section",
        db_column="axe_pys",
    )
    axe_rfa = models.ForeignKey(
        SectionSage,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        to_field="uuid_identification",
        limit_choices_to={"axe": "RFA"},
        related_name="rfa_section",
        db_column="axe_rfa",
    )
    made_in = models.ForeignKey(
        Country,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        to_field="country",
        related_name="made_in_country",
        db_column="made_in",
    )
    item_weight = models.DecimalField(max_digits=20, decimal_places=5, default=0)
    unit_weight = models.ForeignKey(
        UnitChoices,
        on_delete=models.PROTECT,
        to_field="num",
        related_name="+",
        db_column="unit_weight",
        null=True,
    )
    packaging_qty = models.DecimalField(max_digits=20, decimal_places=5, default=1)
    customs_code = models.CharField(null=True, blank=True, max_length=35)
    catalog_price = models.DecimalField(max_digits=20, decimal_places=5, default=0)
    comment = models.TextField(null=True, blank=True)
    new_article = models.BooleanField(null=True, default=False)
    error_sub_category = models.BooleanField(null=True, default=False)

    # Statistique utilisée
    stat_name = models.CharField(
        null=True, blank=True, max_length=35, verbose_name="stat_name used"
    )
    famille = models.CharField(null=True, blank=True, max_length=80)

    # Identification
    uuid_identification = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)

    def save(self, *args, **kwargs):
        """Surcharge de la méthode save pour les axes analytiques"""
        if not self.axe_bu:
            axe = SectionSage.objects.filter(axe="BU", section="CAHA").first()
            self.axe_bu = None if not axe else axe

        if not self.axe_prj:
            axe = SectionSage.objects.filter(axe="PRJ", section="NAF").first()
            self.axe_prj = None if not axe else axe

        if not self.axe_pys:
            axe = SectionSage.objects.filter(axe="PYS", section="FR").first()
            self.axe_pys = None if not axe else axe

        if not self.axe_rfa:
            axe = SectionSage.objects.filter(axe="RFA", section="NAF").first()
            self.axe_pys = None if not axe else axe

        super().save(*args, **kwargs)

    def __str__(self):
        """Texte renvoyé dans les selects et à l'affichage de l'objet"""
        return f"{self.third_party_num} - {self.reference}"

    class Meta:
        """class Meta du modèle django"""

        ordering = ["third_party_num", "reference"]
        unique_together = (("third_party_num", "reference"),)


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
        null=True,
        blank=True,
        to_field="uuid_identification",
        verbose_name="categorie de prix",
        related_name="sale_price_sale_price_category",
        db_column="uuid_sale_price_category",
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

    # @staticmethod
    # def get_absolute_url():
    #     return reverse("book:societies_list")

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
        null=True,
        blank=True,
        to_field="uuid_identification",
        verbose_name="categorie de prix",
        related_name="history_sale_price_category",
        db_column="uuid_sale_price_category",
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


class ArticleAccount(DatesTable):
    """Tables des comptes achat et vente par articles"""

    child_center = models.ForeignKey(
        ChildCenterPurchase,
        on_delete=models.PROTECT,
        to_field="code",
        verbose_name="centrale fille",
        related_name="article_centrale_fille",
        db_column="child_center",
    )
    article = models.ForeignKey(
        Article,
        on_delete=models.PROTECT,
        to_field="uuid_identification",
        related_name="account_article",
        db_column="article",
    )
    vat = models.ForeignKey(
        VatSage,
        on_delete=models.PROTECT,
        to_field="vat",
        related_name="article_vat",
        verbose_name="tva X3",
        db_column="vat",
    )
    purchase_account = models.CharField(max_length=35)
    sale_account = models.CharField(max_length=35)

    class Meta:
        """class Meta du modèle django"""

        ordering = ["child_center", "vat"]
        unique_together = (("child_center", "article", "vat"),)


class Subscription(FlagsTable):
    """
    Table des abonnements. Les abonnements vont servir à refacturer sur la période
    tous les articles abbonés
    FR : Abonnement
    EN : Subscription
    """

    name = models.CharField(unique=True, max_length=80)

    def __str__(self):
        """Texte renvoyé dans les selects et à l'affichage de l'objet"""
        return f"{self.name}"

    class Meta:
        """class Meta du modèle django"""

        ordering = ["name"]


class SubscriptionArticle(FlagsTable):
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


class ArticleUpdate(models.Model):
    """Table des Articles, importés pour update de la table Article"""

    date_facture = models.DateField(null=True, blank=True)
    supplier = models.ForeignKey(
        Society,
        on_delete=models.PROTECT,
        to_field="third_party_num",
        related_name="supplier_society_article_update",
        db_column="supplier",
    )
    reference = models.CharField(max_length=35)
    ean_code = models.CharField(null=True, blank=True, max_length=35)
    libelle = models.CharField(null=True, blank=True, max_length=150)
