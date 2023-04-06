# pylint: disable=E0401,R0903
"""
FR : Module des modèles de factures founisseurs
EN : supplier invoice templates module

Commentaire:

created at: 2021-11-07
created by: Paulo ALVES

modified at: 2021-11-07
modified by: Paulo ALVES
"""
import uuid

from django.db import models

from heron.models import FlagExport
from apps.parameters.models import BaseInvoiceDetailsTable, BaseInvoiceTable, BaseCommonDetailsTable
from apps.accountancy.models import CctSage
from apps.book.models import Society
from apps.edi.models import EdiImportControl


class CentersInvoices(models.Model):
    """Table pour stocker l'historique des éléments centrale pour les factures"""

    created_at = models.DateTimeField(auto_now_add=True)

    # Elements Centrale fille
    code_center = models.CharField(max_length=15)
    comment_center = models.TextField(null=True, blank=True)
    legal_notice_center = models.TextField(null=True, blank=True)
    bank_center = models.CharField(null=True, blank=True, max_length=50)
    iban_center = models.CharField(null=True, blank=True, max_length=50)
    code_swift_center = models.CharField(null=True, blank=True, max_length=27)
    vat_regime_center = models.CharField(null=True, max_length=5)

    # uuid_identification
    uuid_identification = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)

    class Meta:
        """class Meta du modèle django"""

        constraints = [
            models.UniqueConstraint(
                fields=["created_at", "code_center"],
                name="centers_invoices",
            ),
            models.UniqueConstraint(
                fields=[
                    "code_center",
                    "comment_center",
                    "legal_notice_center",
                    "bank_center",
                    "iban_center",
                    "code_swift_center",
                    "vat_regime_center",
                ],
                name="centers_invoices_billing",
            ),
        ]


class SignboardsInvoices(models.Model):
    """Table pour stocker l'historique des éléments enseigne pour les factures"""

    created_at = models.DateTimeField(auto_now_add=True)

    # Elements Enseigne
    code_signboard = models.CharField(max_length=15)
    logo_signboard = models.ImageField(null=True, blank=True, upload_to="logos/")
    message = models.TextField(null=True, blank=True)

    # uuid_identification
    uuid_identification = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)

    class Meta:
        """class Meta du modèle django"""

        constraints = [
            models.UniqueConstraint(
                fields=["created_at", "code_signboard"],
                name="signboard_invoices",
            ),
            models.UniqueConstraint(
                fields=[
                    "code_signboard",
                    "logo_signboard",
                    "message",
                ],
                name="signboard_invoices_billing",
            ),
        ]


class PartiesInvoices(models.Model):
    """Table fixe des adresses du facturé CCT et Tiers"""

    created_at = models.DateTimeField(auto_now_add=True)

    # Client CCT
    cct = models.ForeignKey(
        CctSage,
        on_delete=models.PROTECT,
        to_field="cct",
        related_name="cct_parties",
        verbose_name="cct x3",
        db_column="cct",
    )
    name_cct = models.CharField(null=True, blank=True, max_length=80)
    immeuble_cct = models.CharField(null=True, blank=True, max_length=200)
    adresse_cct = models.CharField(null=True, blank=True, max_length=200)
    code_postal_cct = models.CharField(null=True, blank=True, max_length=15)
    ville_cct = models.CharField(null=True, blank=True, max_length=50)
    pays_cct = models.CharField(null=True, blank=True, max_length=80)

    # Tiers facturé à qui appartient le CCT
    third_party_num = models.ForeignKey(
        Society,
        on_delete=models.PROTECT,
        to_field="third_party_num",
        related_name="society_parties",
        db_column="third_party_num",
    )
    name_third_party = models.CharField(null=True, blank=True, max_length=80)
    immeuble_third_party = models.CharField(null=True, blank=True, max_length=200)
    adresse_third_party = models.CharField(null=True, blank=True, max_length=200)
    code_postal_third_party = models.CharField(null=True, blank=True, max_length=15)
    ville_third_party = models.CharField(null=True, blank=True, max_length=50)
    pays_third_party = models.CharField(null=True, blank=True, max_length=80)

    # uuid_identification
    uuid_identification = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)

    def __str__(self):
        """Texte renvoyé dans les selects et à l'affichage de l'objet"""
        return f"{self.created_at} - {self.cct} - {self.third_party_num}"

    class Meta:
        """class Meta du modèle django"""

        constraints = [
            models.UniqueConstraint(
                fields=["created_at", "cct", "third_party_num"],
                name="parties_invoices",
            ),
            models.UniqueConstraint(
                fields=[
                    "cct",
                    "name_cct",
                    "immeuble_cct",
                    "adresse_cct",
                    "code_postal_cct",
                    "ville_cct",
                    "pays_cct",
                    "third_party_num",
                    "name_third_party",
                    "immeuble_third_party",
                    "adresse_third_party",
                    "code_postal_third_party",
                    "ville_third_party",
                    "pays_third_party",
                ],
                name="parties_adresses_billing",
            ),
        ]


class Invoice(FlagExport, BaseInvoiceTable):
    """
    FR : Factures Fournisseurs
    EN : Suppliers Invoices
    """

    uuid_identification = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    invoice_sage_number = models.CharField(unique=True, max_length=20)

    # Tiers X3 qui a facturé
    third_party_num = models.ForeignKey(
        Society,
        on_delete=models.PROTECT,
        to_field="third_party_num",
        related_name="third_party_num_invoice",
        db_column="third_party_num",
    )
    vat_regime = models.CharField(null=True, max_length=5, verbose_name="régime de taxe")
    uuid_file = models.UUIDField(null=True)
    uuid_control = models.ForeignKey(
        EdiImportControl,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        to_field="uuid_identification",
        related_name="edi_control_invoice",
        db_column="uuid_control",
    )
    comment = models.CharField(null=True, blank=True, max_length=120)
    date_echeance = models.DateField(null=True)
    mode_reglement = models.CharField(null=True, max_length=5)
    type_reglement = models.CharField(null=True, max_length=5, default="1")
    adresse_tiers = models.CharField(null=True, max_length=5, default="1")
    adresse_tiers_paye = models.CharField(null=True, max_length=5, default="1")

    def __str__(self):
        """Texte renvoyé dans les selects et à l'affichage de l'objet"""
        return f"{self.third_party_num} - {self.invoice_number} - {self.invoice_date}"

    class Meta:
        """class Meta du modèle django"""

        constraints = [
            models.UniqueConstraint(
                fields=["third_party_num", "invoice_number", "invoice_year"],
                name="purchase_unique_invoice",
            ),
        ]

        indexes = [
            models.Index(fields=["third_party_num"]),
            models.Index(fields=["invoice_number"]),
            models.Index(fields=["invoice_type"]),
            models.Index(fields=["invoice_year"]),
            models.Index(fields=["invoice_month"]),
            models.Index(
                fields=[
                    "third_party_num",
                    "invoice_number",
                    "invoice_year",
                ]
            ),
            models.Index(
                fields=[
                    "third_party_num",
                    "invoice_type",
                    "invoice_year",
                ]
            ),
            models.Index(
                fields=[
                    "third_party_num",
                    "invoice_type",
                    "invoice_month",
                ]
            ),
        ]


class InvoiceDetail(FlagExport, BaseInvoiceDetailsTable):
    """
    FR : Detail des factures fournisseurs
    EN : Suppliers Invoices detail
    """

    # Identification
    uuid_identification = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    import_uuid_identification = models.UUIDField(unique=True)

    # Tiers X3 qui a facturé
    third_party_num = models.ForeignKey(
        Society,
        on_delete=models.PROTECT,
        to_field="third_party_num",
        related_name="third_party_invoice",
        db_column="third_party_num",
    )
    uuid_invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        to_field="uuid_identification",
        related_name="detail_invoice",
        db_column="uuid_invoice",
    )
    axe_bu = models.CharField(max_length=15)
    axe_prj = models.CharField(max_length=15)
    axe_pro = models.CharField(max_length=15)
    axe_rfa = models.CharField(max_length=15)
    axe_pys = models.CharField(max_length=15)

    vat = models.CharField(max_length=5)
    vat_rate = models.DecimalField(max_digits=20, decimal_places=5)
    vat_regime = models.CharField(max_length=5)
    big_category = models.CharField(max_length=120)
    sub_category = models.CharField(null=True, max_length=80)
    account = models.CharField(max_length=35)

    class Meta:
        """class Meta du modèle django"""

        indexes = [
            models.Index(fields=["uuid_invoice"], name="invoice_idx"),
            models.Index(fields=["axe_bu"], name="invoice_axe_bu"),
            models.Index(fields=["axe_prj"], name="invoice_axe_prj"),
            models.Index(fields=["axe_rfa"], name="invoice_axe_rfa"),
            models.Index(fields=["axe_pro"], name="invoice_axe_pro"),
            models.Index(fields=["axe_pys"], name="invoice_axe_pys"),
        ]


class SaleInvoice(FlagExport, BaseInvoiceTable):
    """
    FR : Factures
    EN : Invoices
    """

    uuid_identification = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    invoice_sage_number = models.CharField(unique=True, max_length=20)

    # Tiers X3 à qui facturer
    third_party_num = models.ForeignKey(
        Society,
        on_delete=models.PROTECT,
        to_field="third_party_num",
        related_name="third_party_num_sale",
        db_column="third_party_num",
    )

    # cct X3 facturé
    cct = models.ForeignKey(
        CctSage,
        on_delete=models.PROTECT,
        to_field="cct",
        related_name="cct_sale",
        verbose_name="cct x3",
        db_column="cct",
    )

    vat_regime = models.CharField(null=True, max_length=5, verbose_name="régime de taxe")
    comment = models.CharField(null=True, blank=True, max_length=120)

    # Centrale
    centers = models.ForeignKey(
        CentersInvoices,
        on_delete=models.PROTECT,
        to_field="uuid_identification",
        related_name="centers_sale",
        verbose_name="centrale fille",
        db_column="centers",
        null=True,
    )

    # Enseigne
    signboard = models.ForeignKey(
        SignboardsInvoices,
        on_delete=models.PROTECT,
        to_field="uuid_identification",
        related_name="signboard_sale",
        verbose_name="enseigne",
        db_column="signboard",
        null=True,
    )

    # Parties
    parties = models.ForeignKey(
        PartiesInvoices,
        on_delete=models.PROTECT,
        to_field="uuid_identification",
        related_name="parties_sale",
        verbose_name="parties prenantes",
        db_column="parties",
        null=True,
    )

    big_category = models.CharField(max_length=120)

    def __str__(self):
        """Texte renvoyé dans les selects et à l'affichage de l'objet"""
        return f"{self.invoice_number} - {self.invoice_number} - {self.invoice_date} - {self.cct}"

    class Meta:
        """class Meta du modèle django"""

        constraints = [
            models.UniqueConstraint(
                fields=["cct", "invoice_number", "invoice_year"],
                name="sale_unique_invoice",
            ),
        ]

        indexes = [
            models.Index(fields=["third_party_num"]),
            models.Index(fields=["invoice_number"]),
            models.Index(fields=["invoice_type"]),
            models.Index(fields=["invoice_year"]),
            models.Index(fields=["invoice_month"]),
            models.Index(fields=["cct"]),
            models.Index(fields=["big_category"]),
            models.Index(
                fields=[
                    "third_party_num",
                    "invoice_number",
                    "invoice_year",
                ]
            ),
            models.Index(
                fields=[
                    "third_party_num",
                    "invoice_type",
                    "invoice_year",
                ]
            ),
            models.Index(
                fields=[
                    "third_party_num",
                    "invoice_year",
                ]
            ),
            models.Index(
                fields=[
                    "third_party_num",
                    "invoice_type",
                    "invoice_month",
                ]
            ),
            models.Index(
                fields=[
                    "third_party_num",
                    "cct",
                ]
            ),
            models.Index(
                fields=[
                    "third_party_num",
                    "cct",
                    "invoice_year",
                ]
            ),
            models.Index(
                fields=[
                    "cct",
                    "invoice_number",
                    "invoice_year",
                ]
            ),
            models.Index(
                fields=[
                    "cct",
                    "invoice_year",
                ]
            ),
            models.Index(
                fields=[
                    "cct",
                    "invoice_number",
                    "invoice_month",
                ]
            ),
            models.Index(
                fields=[
                    "cct",
                    "invoice_type",
                    "invoice_month",
                ]
            ),
            models.Index(
                fields=[
                    "cct",
                    "big_category",
                    "invoice_year",
                ]
            ),
            models.Index(
                fields=[
                    "cct",
                    "big_category",
                    "invoice_month",
                ]
            ),
            models.Index(
                fields=[
                    "cct",
                    "big_category",
                    "invoice_number",
                    "invoice_year",
                ]
            ),
            models.Index(
                fields=[
                    "cct",
                    "invoice_month",
                ]
            ),
        ]


class SaleInvoiceDetail(FlagExport, BaseInvoiceDetailsTable):
    """
    FR : Detail des factures fournisseurs
    EN : Suppliers Invoices detail
    """

    # Identification
    uuid_identification = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    import_uuid_identification = models.UUIDField(unique=True)

    # Tiers X3 qui a facturé
    third_party_num = models.ForeignKey(
        Society,
        on_delete=models.PROTECT,
        to_field="third_party_num",
        related_name="third_party_sale_invoice",
        db_column="third_party_num",
    )

    uuid_invoice = models.ForeignKey(
        SaleInvoice,
        on_delete=models.CASCADE,
        to_field="uuid_identification",
        related_name="detail_sale_invoice",
        db_column="uuid_invoice",
    )
    axe_bu = models.CharField(max_length=15)
    axe_prj = models.CharField(max_length=15)
    axe_pro = models.CharField(max_length=15)
    axe_rfa = models.CharField(max_length=15)
    axe_pys = models.CharField(max_length=15)

    vat = models.CharField(max_length=5)
    vat_rate = models.DecimalField(max_digits=20, decimal_places=5)
    vat_regime = models.CharField(max_length=5)
    big_category = models.CharField(max_length=120)
    sub_category = models.CharField(null=True, max_length=80)

    # Regroupement de facturation
    base = models.CharField(max_length=35)
    grouping_goods = models.CharField(null=True, max_length=35)

    account = models.CharField(max_length=35)

    class Meta:
        """class Meta du modèle django"""

        indexes = [
            models.Index(fields=["uuid_invoice"], name="sale_invoice_idx"),
            models.Index(fields=["axe_bu"], name="sale_invoice_axe_bu"),
            models.Index(fields=["axe_prj"], name="sale_invoice_axe_prj"),
            models.Index(fields=["axe_rfa"], name="sale_invoice_axe_rfa"),
            models.Index(fields=["axe_pro"], name="sale_invoice_axe_pro"),
            models.Index(fields=["axe_pys"], name="sale_invoice_axe_pys"),
        ]


class InvoiceCommonDetails(BaseCommonDetailsTable):
    """
    FR : Detail des n° de série
    EN : Serial numbers detail
    """

    import_uuid_identification = models.UUIDField(unique=True)
    unit_weight = models.CharField(max_length=5)
    uuid_file = models.UUIDField(null=True)

    class Meta:
        """class Meta du modèle django"""

        indexes = [
            models.Index(
                fields=["import_uuid_identification"], name="import_uuid_identification_idx"
            ),
            models.Index(fields=["acuitis_order_number"], name="acuitis_order_number_idx"),
            models.Index(fields=["client_name"], name="client_name_idx"),
            models.Index(fields=["command_reference"], name="command_reference_idx"),
            models.Index(fields=["customs_code"], name="customs_code_idx"),
            models.Index(fields=["delivery_number"], name="delivery_number_idx"),
            models.Index(fields=["first_name"], name="first_name_idx"),
            models.Index(fields=["formation_month"], name="formation_month_idx"),
            models.Index(fields=["initial_date"], name="initial_date_idx"),
            models.Index(fields=["initial_home"], name="initial_home_idx"),
            models.Index(fields=["last_name"], name="last_name_idx"),
            models.Index(fields=["libelle"], name="libelle_idx"),
            models.Index(fields=["personnel_type"], name="personnel_type_idx"),
            models.Index(fields=["reference_article"], name="reference_article_idx"),
            models.Index(fields=["serial_number"], name="serial_number_idx"),
            models.Index(fields=["uuid_file"], name="uuid_file_idx"),
        ]
