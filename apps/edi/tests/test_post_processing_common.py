"""
Tests des post-traitements communs à tous les imports fournisseurs (edi_post_processing_pool) :
post_general et ses SQL (sql_common), SQL_QTY / post_all (sql_all), bulk_post_insert.
Les requêtes s'exécutent réellement sur la base de test.

created at: 2026-10-10
created by: Paulo ALVES
"""
import datetime
import types
from decimal import Decimal

import pytest
from django.db import connection

from apps.edi.bin import edi_post_processing_pool as pool
from apps.edi.models import EdiImport
from apps.edi.tests.helpers_post import edi_values, refresh
from apps.users.models import User
from conftest import patched_attrs

pytestmark = pytest.mark.django_db


def run_post_general(uuid_identification):
    """Exécute post_general avec un curseur de la connexion par défaut"""
    with connection.cursor() as cursor:
        pool.post_general(uuid_identification, cursor)


# UTILISATEUR AUTOMATE =============================================================================


def test_get_user_automate_cree_puis_reutilise():
    first = pool.get_user_automate()
    second = pool.get_user_automate()

    assert first == second
    assert User.objects.filter(username="automate").count() == 1
    assert User.objects.get(username="automate").function == "automate"


def test_get_user_automate_avec_mot_de_passe_modifie(make_user):
    """Régression : l'utilisateur existant avec un autre mot de passe était recréé (IntegrityError)"""
    user = make_user(email="automate@acuitis.com", username="automate", password="autre")

    assert pool.get_user_automate() == user.uuid_identification


# SUPPRESSION DES IMPORTS SANS ARTICLES ============================================================


def test_suppress_import_without_articles(edi_batch, make_trace):
    uuid_ko, _ = edi_batch([{"reference_article": ""}, {"reference_article": "ART-2"}])
    uuid_ok, _ = edi_batch([{"reference_article": "ART-3"}])
    uuid_sans_trace, _ = edi_batch([{"reference_article": None}])
    trace = make_trace(uuid_identification=uuid_ko, comment="Import")

    pool.suppress_import_without_articles()

    trace.refresh_from_db()
    assert trace.errors is True
    assert "Il manque des références articles" in trace.comment
    assert not EdiImport.objects.filter(uuid_identification=uuid_ko).exists()
    assert EdiImport.objects.filter(uuid_identification=uuid_ok).count() == 1
    # Sans trace, l'import est conservé
    assert EdiImport.objects.filter(uuid_identification=uuid_sans_trace).count() == 1


# POST PROCESSING ALL ==============================================================================


@pytest.mark.usefixtures('icon_origins')
def test_post_processing_all(edi_batch, make_society, make_section, make_default_axes):
    make_default_axes()
    refac = make_section("BU", "REFAC0")
    society = make_society("FOUR001", is_client=False, in_use=False)
    uuid_identification, rows = edi_batch(
        [
            {"item_weight": None},
            {"third_party_num": "ZREFAC0", "reference_article": "RF-1", "item_weight": None},
        ]
    )
    orphan = edi_batch([{"valid": None}])[1][0]

    pool.post_processing_all()

    society.refresh_from_db()
    assert society.in_use is True
    assert not EdiImport.objects.filter(pk=orphan.pk).exists()
    assert set(edi_values(uuid_identification, "item_weight")) == {(Decimal("0"),)}
    assert refresh(rows[1]).axe_bu == refac
    # le nouvel article a reçu les axes par défaut, propagés sur la ligne
    assert refresh(rows[0]).axe_bu.section == "CAHA"


def test_post_vacuum(monkeypatch):
    executed = []

    class _Cursor:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def execute(self, sql):
            executed.append(sql)

    with patched_attrs(monkeypatch, pool, connection=types.SimpleNamespace(cursor=_Cursor)):
        pool.post_vacuum()

    assert executed == ["VACUUM (full)"]


def test_edi_trace_supplier_insert(edi_batch, make_trace):
    uuid_identification, _ = edi_batch(
        [{"flow_name": "Edi", "supplier": "ESSILOR", "third_party_num": "ESSI001"}]
    )
    trace = make_trace(uuid_identification=uuid_identification, trace_name="Import Edi - tiers : ")
    edi_batch([{"flow_name": "Widex"}])

    pool.edi_trace_supplier_insert()

    assert refresh(trace).trace_name == "Import Edi - tiers : ESSILOR - ESSI001"


# POST GENERAL : EFFETS UNITAIRES ==================================================================


@pytest.mark.usefixtures('icon_origins')
def test_post_general_arrondis_codes_et_validation(edi_batch):
    uuid_identification, rows = edi_batch(
        [
            {
                "net_amount": Decimal("10.456"),
                "code_maison": "",
                "code_fournisseur": "MAG01",
                "reference_article": "",
                "libelle": "Verre progressif",
                "acuitis_order_date": datetime.date(1900, 1, 1),
                "delivery_number": "None",
                "delivery_date": datetime.date(1900, 1, 1),
                "unit_weight": None,
                "item_weight": None,
                "gross_unit_price": Decimal("-5"),
                "import_uuid_identification": None,
                "invoice_date": datetime.date(2026, 3, 15),
            },
            {"code_maison": "TEL0102", "code_fournisseur": "", "invoice_number": "AUTRE"},
        ],
        flow_name="Generique",
    )

    run_post_general(uuid_identification)

    first, second = refresh(*rows)
    assert first.net_amount == Decimal("10.46")
    assert first.code_maison == "MAG01"
    assert second.code_maison == ""
    assert first.reference_article == "Verre progressif"
    assert first.acuitis_order_date is None
    assert first.delivery_number is None
    assert first.delivery_date is None
    assert first.import_uuid_identification is not None
    # validation
    assert first.valid is True
    assert first.created_by.username == "automate"
    assert first.invoice_month == datetime.date(2026, 3, 1)
    assert first.invoice_year == 2026
    assert first.unit_weight_id == 1
    assert first.item_weight == Decimal("0")
    assert first.gross_unit_price == Decimal("5")
    assert first.manual_entry is False
    assert first.delete is False
    # une seule maison par facture : pas multi magasins ; centrale par défaut ACF
    assert first.is_multi_store is False
    assert first.code_center == "ACF"


@pytest.mark.usefixtures('icon_origins')
def test_post_general_multi_magasins(edi_batch):
    invoice = "F-MULTI"
    uuid_identification, rows = edi_batch(
        [
            {"invoice_number": invoice, "code_maison": "MAG01"},
            {"invoice_number": invoice, "code_maison": "MAG02"},
            {"invoice_number": "F-MONO", "code_maison": "", "code_fournisseur": "MAG03"},
        ]
    )

    run_post_general(uuid_identification)

    assert [row.is_multi_store for row in refresh(*rows)] == [True, True, False]


@pytest.mark.usefixtures('icon_origins')
def test_post_general_tiers_depuis_identifiant_et_tva(edi_batch, make_society, make_vat_rat):
    """Tiers trouvé par supplier_ident, régime de taxe du tiers, code tva depuis le taux"""
    make_society(
        "WIDE001", is_client=False, name="Widex France SAS", centers_suppliers_indentifier="WID|WIDEX",
        vat_sheme_supplier="",
    )
    make_vat_rat("001", "20", datetime.date(2014, 1, 1))
    make_vat_rat("001", "19.6", datetime.date(2000, 1, 1))
    make_vat_rat("002", "5.5")
    uuid_identification, rows = edi_batch(
        [
            {"third_party_num": None, "supplier_ident": "WIDEX", "supplier": "", "vat_rate": Decimal("0.2"),
             "net_amount": Decimal("100")},
            {"third_party_num": None, "supplier_ident": "WIDEX", "supplier": "Widex", "vat_rate": Decimal("0.055"),
             "net_amount": Decimal("10"), "invoice_number": "F2"},
        ]
    )

    run_post_general(uuid_identification)

    first, second = refresh(*rows)
    assert (first.third_party_num, first.supplier_name, first.supplier) == ("WIDE001", "Widex France SAS", "Widex France SAS")
    assert second.supplier == "Widex"
    assert first.vat_regime == "FRA"
    assert (first.vat_id, second.vat_id) == ("001", "002")
    assert (first.vat_amount, first.amount_with_vat) == (Decimal("20"), Decimal("120"))
    assert (second.vat_amount, second.amount_with_vat) == (Decimal("0.55"), Decimal("10.55"))


@pytest.mark.usefixtures('icon_origins')
def test_post_general_supplier_name_et_tva_cee(edi_batch, make_society, make_vat):
    make_vat("011", "CEE")
    make_society("DEU001", is_client=False, vat_sheme_supplier="CEE")
    uuid_identification, rows = edi_batch(
        [{"third_party_num": "DEU001", "supplier": "Zeiss", "supplier_name": "", "purchase_invoice": True}]
    )

    run_post_general(uuid_identification)

    row = refresh(rows[0])
    assert row.supplier_name == "Zeiss"
    assert (row.vat_regime, row.vat_id) == ("CEE", "011")


@pytest.mark.usefixtures('icon_origins')
def test_post_general_totaux_facture(edi_batch):
    """Totaux recalculés depuis les lignes sauf pour les flux Edi/Widex, négatifs pour les avoirs"""
    uuid_identification, rows = edi_batch(
        [
            {"invoice_number": "F1", "net_amount": Decimal("100"), "vat_rate": Decimal("0.2"), "flow_name": "Generique"},
            {"invoice_number": "F1", "net_amount": Decimal("50"), "vat_rate": Decimal("0.2"), "flow_name": "Generique"},
            {"invoice_number": "A1", "net_amount": Decimal("-30"), "vat_rate": Decimal("0.2"), "flow_name": "Generique",
             "invoice_type": "381"},
            {"invoice_number": "E1", "net_amount": Decimal("10"), "vat_rate": Decimal("0.2"), "flow_name": "Edi",
             "invoice_amount_without_tax": Decimal("999"), "invoice_amount_with_tax": Decimal("999")},
        ]
    )

    run_post_general(uuid_identification)

    first, _, credit, edi = refresh(*rows)
    assert (first.invoice_amount_without_tax, first.invoice_amount_with_tax, first.invoice_amount_tax) == (
        Decimal("150"), Decimal("180"), Decimal("30"),
    )
    assert (credit.invoice_amount_without_tax, credit.invoice_amount_with_tax) == (Decimal("-30"), Decimal("-36"))
    assert (edi.invoice_amount_without_tax, edi.invoice_amount_with_tax) == (Decimal("999"), Decimal("999"))


@pytest.mark.usefixtures('icon_origins')
def test_post_general_delta_tva_arrondi(edi_batch):
    """L'écart d'arrondi entre la TVA par ligne et la TVA facture est reporté sur les premières lignes"""
    uuid_identification, rows = edi_batch(
        [
            {"invoice_number": "F1", "net_amount": Decimal("0.33"), "vat_rate": Decimal("0.2"), "flow_name": "Generique"}
            for _ in range(3)
        ]
    )

    run_post_general(uuid_identification)

    first, second, third = refresh(*rows)
    # facture : 0.99 HT, TVA 0.20 ; lignes : 3 x 0.07 = 0.21 -> une ligne corrigée de -0.01
    assert first.invoice_amount_with_tax == Decimal("1.19")
    assert [row.vat_amount for row in (first, second, third)] == [Decimal("0.06"), Decimal("0.07"), Decimal("0.07")]
    assert first.amount_with_vat + second.amount_with_vat + third.amount_with_vat == Decimal("1.19")


@pytest.mark.usefixtures('icon_origins')
def test_post_general_numero_de_bl_scinde(edi_batch):
    uuid_identification, rows = edi_batch(
        [{"delivery_number": "BL123 du 12/01/2026", "comment": ""}, {"delivery_number": "BL456", "comment": ""}]
    )

    run_post_general(uuid_identification)

    first, second = refresh(*rows)
    assert (first.delivery_number, first.comment) == ("BL123", " 12/01/2026")
    assert (second.delivery_number, second.comment) == ("BL456", "")


@pytest.mark.usefixtures('icon_origins')
def test_post_general_cct_articles_axes_et_avoir(edi_batch, make_maison, make_cct, make_supplier_cct, make_society, make_article, make_section, make_big_category):
    """cct depuis book_suppliercct, axes depuis l'article, signe des avoirs, enseigne et centrale"""
    society = make_society("FOUR001", is_client=False)
    cct = make_cct("AF0001", active=True)
    maison = make_maison("AF0001")
    make_supplier_cct(society, cct, "MAG01|MAG09|")
    axe_pro = make_section("PRO", "OPT")
    article = make_article(
        "ART-1", society, axe_pro=axe_pro, axe_bu=make_section("BU", "CAHA"), big_category=make_big_category("Marchandises"),
        unit_weight_id=1, item_weight=Decimal("2"), customs_code="9003",
    )
    uuid_identification, rows = edi_batch(
        [
            {"code_maison": "MAG01", "reference_article": "ART-1", "invoice_type": "381", "net_amount": Decimal("-10"),
             "qty": Decimal("1"), "gross_amount": Decimal("10")},
            {"code_maison": "MAG01", "reference_article": "ART-1", "invoice_type": "381", "net_amount": Decimal("-10"),
             "third_party_num": "PREC001", "qty": Decimal("1"), "gross_amount": Decimal("10"), "invoice_number": "P1"},
        ]
    )

    run_post_general(uuid_identification)

    first, precilens = refresh(*rows)
    assert first.cct_uuid_identification == maison
    assert (first.code_signboard, first.code_center) == ("ACF", "ACF")
    assert (first.axe_pro, first.axe_bu, first.big_category) == (axe_pro, article.axe_bu, article.big_category)
    assert (first.item_weight, first.customs_code) == (Decimal("2"), "9003")
    assert (first.qty, first.gross_amount) == (Decimal("-1"), Decimal("-10"))
    # Precilens exclu de l'inversion du signe des avoirs
    assert (precilens.qty, precilens.gross_amount) == (Decimal("1"), Decimal("10"))


# BULK BBGR ========================================================================================


@pytest.mark.usefixtures('icon_origins')
def test_bulk_post_insert_cree_les_lignes_de_frais(edi_batch):
    uuid_identification, rows = edi_batch(
        [
            {
                "flow_name": "BbgrBulk", "invoice_number": "B1", "famille": None, "qty": Decimal("0"),
                "packaging_amount": Decimal("3"), "transport_amount": Decimal("7"), "insurance_amount": Decimal("0"),
                "fob_amount": None, "fees_amount": Decimal("1.5"), "net_amount": Decimal("40"), "devise": None,
            }
        ]
    )

    pool.bulk_post_insert(uuid_identification)

    lines = EdiImport.objects.filter(uuid_identification=uuid_identification).order_by("id")
    assert list(lines.values_list("reference_article", flat=True)) == ["ART-1", "EMBALLAGE", "PORT", "FEES"]
    frais = {row.libelle: row.net_amount for row in lines[1:]}
    assert frais == {"EMBALLAGE": Decimal("3"), "PORT": Decimal("7"), "FEES": Decimal("1.5")}
    first = refresh(rows[0])
    assert (first.famille, first.qty, first.devise) == ("VERRES", Decimal("1"), "EUR")
    assert (first.gross_unit_price, first.gross_amount) == (first.net_unit_price, Decimal("40"))
    assert (first.purchase_invoice, first.sale_invoice, first.origin_id) == (True, True, 1)
    assert all(row.valid for row in lines)


@pytest.mark.usefixtures('icon_origins')
def test_bulk_post_insert_sans_frais(edi_batch):
    uuid_identification, _ = edi_batch([{"flow_name": "BbgrBulk", "packaging_amount": Decimal("0")}])

    pool.bulk_post_insert(uuid_identification)

    assert EdiImport.objects.filter(uuid_identification=uuid_identification).count() == 1
