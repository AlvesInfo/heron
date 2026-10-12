"""
Tests des post-traitements par fournisseur (edi_post_processing_pool.*_post_insert) : chaque
fonction exécute réellement ses requêtes sql_files puis post_general sur la base de test.

created at: 2026-10-10
created by: Paulo ALVES
"""
import datetime
from decimal import Decimal

import pytest

from apps.articles.models import Article
from apps.edi.bin import edi_post_processing_pool as pool
from apps.edi.models import EdiImport, StarkeyDepot
from apps.edi.tests.helpers_post import refresh

pytestmark = pytest.mark.django_db

COMMON = {"invoice_type": "FA", "gross_amount": Decimal("20"), "net_amount": Decimal("10"), "qty": Decimal("2")}


@pytest.fixture
def refs(icon_origins, make_vat_rat):  # pylint: disable=W0613
    """Référentiels requis par post_general (origines, TVA 001 à 20 %)"""
    make_vat_rat("001", "20")


# COSIUM ===========================================================================================


@pytest.mark.parametrize(
    ("function", "sale"),
    [(pool.cosium_post_insert, True), (pool.cosium_achats_post_insert, False)],
    ids=["ventes", "achats"],
)
@pytest.mark.usefixtures('refs')
def test_cosium_post_insert(edi_batch, function, sale):
    uuid_identification, rows = edi_batch(
        [
            {"invoice_number": "C1", "net_amount": Decimal("-10"), "gross_amount": Decimal("10"), "qty": Decimal("1"),
             "amount_with_vat": Decimal("-12"), "famille": None, "libelle": "Verre -  - progressif"},
            {"invoice_number": "C2", "net_amount": Decimal("10"), "gross_amount": Decimal("10"), "qty": Decimal("-1"),
             "amount_with_vat": Decimal("0"), "net_unit_price": Decimal("10"), "famille": "MONT"},
        ],
        flow_name="Cosium",
    )

    function(uuid_identification)

    credit, zero = refresh(*rows)
    assert (credit.invoice_type, credit.gross_amount, credit.qty, credit.libelle) == ("381", Decimal("-10"), Decimal("-1"), "Verre progressif")
    assert (credit.famille, credit.origin_id, credit.unit_weight_id) == ("ART-1", 1, 11)
    assert (credit.purchase_invoice, credit.sale_invoice) == (True, sale)
    # ligne à TTC zéro : montants annulés, remise = quantité x prix
    assert (zero.net_amount, zero.gross_amount, zero.discount_price_01) == (Decimal("0"), Decimal("0"), Decimal("-10"))
    assert zero.famille == "MONT"
    assert credit.valid is True


@pytest.mark.usefixtures('refs', 'make_big_category')
def test_transferts_cosium_post_insert(edi_batch, make_maison, make_article, make_society, make_section, make_default_axes, make_supplier_family_axes):
    make_maison("AF0001", reference_cosium="COS01")
    make_default_axes()
    transfert = make_society("ZTRANSFERT", is_client=False)
    bbgr = make_society("BBGR002", is_client=False)
    pro = make_section("PRO", "OPT")
    make_article("ART-T", transfert, axe_pro=pro, axe_bu=make_section("BU", "CAHA"))
    make_article("ART-B", bbgr, axe_pro=make_section("PRO", "AUD"))
    family = make_supplier_family_axes("LUNETTES", "COSI001", axe_pro=make_section("PRO", "FAM"))
    uuid_identification, rows = edi_batch(
        [
            {"reference_article": "ART-T", "code_fournisseur": "COS01", "qty": Decimal("2"), "net_unit_price": Decimal("10"),
             "vat_rate": Decimal("0.2")},
            {"reference_article": "ART-B", "code_fournisseur": "AUTRE", "qty": Decimal("1"), "net_unit_price": Decimal("5"),
             "vat_rate": Decimal("0.2")},
            {"reference_article": "ART-N", "famille": "LUNETTES", "qty": Decimal("1"), "net_unit_price": Decimal("5"),
             "vat_rate": Decimal("0.2")},
        ],
        flow_name="Transfert",
        third_party_num="ZTRANSFERT",
    )

    pool.tansferts_cosium_post_insert(uuid_identification)

    first, second, third = refresh(*rows)
    assert (first.code_fournisseur, first.code_maison) == ("AF0001", "AF0001")
    assert (first.net_amount, first.vat_amount, first.amount_with_vat) == (Decimal("20"), Decimal("4"), Decimal("24"))
    assert (first.purchase_invoice, first.sale_invoice, first.supplier_ident) == (False, True, "ZTRANSFERT")
    assert first.axe_pro == pro
    assert second.axe_pro.section == "AUD"
    assert (third.axe_pro, third.big_category) == (family.axe_pro, family.big_category)
    assert third.axe_bu.section == "CAHA"


# EDI OPTO 33 ======================================================================================


@pytest.mark.usefixtures('refs')
def test_edi_post_insert(edi_batch):
    uuid_identification, rows = edi_batch(
        [
            {"siret_payeur": "433193067", "vat_rate": Decimal("20"), "acuitis_order_number": "UNKNOWN",
             "invoice_type": "380", "qty": Decimal("2"), "net_amount": Decimal("-10"), "reference_article": "",
             "ean_code": "123", "invoice_amount_without_tax": Decimal("-10"), "invoice_amount_with_tax": Decimal("-12")},
            {"third_party_num": "PREC001", "vat_rate": Decimal("5.5"), "invoice_type": "381", "qty": Decimal("2"),
             "net_amount": Decimal("10"), "gross_amount": Decimal("10"), "invoice_number": "P1",
             "invoice_amount_without_tax": Decimal("10"), "invoice_amount_with_tax": Decimal("12")},
            {"vat_rate": Decimal("7"), "invoice_type": "381", "qty": Decimal("-1"), "net_amount": Decimal("10"),
             "invoice_number": "A1", "invoice_amount_without_tax": Decimal("10"), "invoice_amount_with_tax": Decimal("12")},
        ],
        flow_name="Edi",
    )

    pool.edi_post_insert(uuid_identification)

    essilor, precilens, credit = refresh(*rows)
    assert essilor.supplier_ident == "col_opticlibre"
    assert (essilor.vat_rate, essilor.acuitis_order_number, essilor.origin_id) == (Decimal("0.2"), "", 1)
    assert (essilor.net_amount, essilor.reference_article) == (Decimal("10"), "123")
    assert (essilor.invoice_amount_without_tax, essilor.invoice_amount_with_tax, essilor.invoice_amount_tax) == (
        Decimal("10"), Decimal("12"), Decimal("2"),
    )
    assert (essilor.purchase_invoice, essilor.sale_invoice) == (True, True)
    # Precilens : avoir inversé puis signe recalculé
    assert (precilens.vat_rate, precilens.qty, precilens.gross_amount, precilens.net_amount) == (
        Decimal("0.055"), Decimal("-2"), Decimal("-10"), Decimal("10"),
    )
    assert (precilens.invoice_amount_without_tax, precilens.invoice_amount_tax) == (Decimal("-10"), Decimal("-2"))
    assert (credit.vat_rate, credit.net_amount) == (Decimal("0.07"), Decimal("10"))


# BBGR B.I =========================================================================================


@pytest.mark.parametrize(
    ("function", "flow"),
    [(pool.bbgr_statment_post_insert, "BbgrStatment"), (pool.bbgr_monthly_post_insert, "BbgrMonthly")],
    ids=["statment", "monthly"],
)
@pytest.mark.usefixtures('refs')
def test_bbgr_statment_monthly_post_insert(edi_batch, function, flow):
    uuid_identification, rows = edi_batch(
        [{"vat_rate": Decimal("20"), "famille": None}, {"vat_rate": Decimal("5.5"), "famille": "MONT", "invoice_number": "F2"}],
        flow_name=flow,
    )

    function(uuid_identification)

    first, second = refresh(*rows)
    assert (first.vat_rate, first.origin_id, first.famille) == (Decimal("0.2"), 3, "ART-1")
    assert (second.vat_rate, second.famille) == (Decimal("0.055"), "MONT")


@pytest.mark.parametrize(
    "function", [pool.bbgr_retours_post_insert, pool.bbgr_reception_post_insert], ids=["retours", "receptions"]
)
@pytest.mark.usefixtures('refs')
def test_bbgr_retours_receptions_post_insert(edi_batch, function):
    uuid_identification, rows = edi_batch(
        [
            {"invoice_number": "R1", "vat_rate": Decimal("20"), "net_amount": Decimal("10"), "invoice_type": "380"},
            {"invoice_number": "R1", "vat_rate": Decimal("20"), "net_amount": Decimal("5"), "invoice_type": "380"},
            {"invoice_number": "A1", "vat_rate": Decimal("20"), "net_amount": Decimal("-10"), "invoice_type": "381"},
        ],
        flow_name="BbgrRetours",
    )

    function(uuid_identification)

    first, _, credit = refresh(*rows)
    assert (first.vat_rate, first.vat_amount, first.amount_with_vat, first.origin_id) == (Decimal("0.2"), Decimal("2"), Decimal("12"), 3)
    assert (first.invoice_amount_without_tax, first.invoice_amount_tax, first.invoice_amount_with_tax) == (
        Decimal("15"), Decimal("3"), Decimal("18"),
    )
    assert (credit.invoice_amount_without_tax, credit.invoice_amount_with_tax) == (Decimal("-10"), Decimal("-12"))


# FOURNISSEURS À FICHIER ===========================================================================


@pytest.mark.usefixtures('refs')
def test_eye_confort_post_insert(edi_batch):
    uuid_identification, rows = edi_batch(
        [
            {**COMMON, "famille": None, "qty": Decimal("-2"), "gross_amount": Decimal("-20")},
            {**COMMON, "invoice_type": "AV", "net_amount": Decimal("-10"), "gross_amount": Decimal("20"), "qty": Decimal("2"),
             "invoice_number": "A1", "famille": "X"},
            {**COMMON, "net_amount": Decimal("0"), "gross_amount": Decimal("5"), "invoice_number": "Z1"},
        ],
        flow_name="EyeConfort",
    )

    pool.eye_confort_post_insert(uuid_identification)

    first, credit, zero = refresh(*rows)
    assert (first.invoice_type, first.gross_unit_price, first.net_unit_price) == ("380", Decimal("10"), Decimal("5"))
    assert (first.vat_rate, first.vat_amount, first.amount_with_vat, first.famille) == (Decimal("0"), Decimal("0"), Decimal("10"), "ART-1")
    assert (first.qty, first.gross_amount) == (Decimal("2"), Decimal("20"))
    assert (credit.invoice_type, credit.qty, credit.gross_amount) == ("381", Decimal("-2"), Decimal("-20"))
    assert (zero.qty, zero.gross_amount) == (Decimal("2"), Decimal("0"))


@pytest.mark.usefixtures('refs')
def test_generique_post_insert(edi_batch, make_trace, make_vat_rat):
    make_vat_rat("002", "5.5")
    uuid_identification, rows = edi_batch(
        [
            {**COMMON, "vat_rate": Decimal("0.2"), "vat": None},
            {**COMMON, "third_party_num": "MGDE001", "invoice_type": "AV", "qty": Decimal("-1"), "net_amount": Decimal("10"),
             "reference_article": "PORT COLIS", "vat_rate": Decimal("0.055"), "vat": None, "invoice_number": "M1"},
            {**COMMON, "third_party_num": "MGDE001", "invoice_type": "FA", "qty": Decimal("-1"), "net_amount": Decimal("10"),
             "vat_rate": Decimal("0.2"), "vat": None, "invoice_number": "M2"},
        ],
        flow_name="Generique",
        supplier="FOURNISSEUR",
    )
    trace = make_trace(uuid_identification=uuid_identification, trace_name="Import Génerique - tiers : ")

    pool.generique_post_insert(uuid_identification)

    first, mgdev, mgdev_neg = refresh(*rows)
    assert (first.invoice_type, first.origin_id, first.vat_id, first.vat_regime) == ("380", 1, "001", "FRA")
    assert (mgdev.invoice_type, mgdev.net_amount, mgdev.famille, mgdev.vat_id) == ("381", Decimal("10"), "PORT", "002")
    assert mgdev_neg.net_amount == Decimal("-10")
    assert refresh(trace).trace_name == "Import Génerique - tiers : FOURNISSEUR"
    assert first.valid is True


@pytest.mark.usefixtures('refs')
def test_generique_post_insert_sans_post_general(edi_batch):
    uuid_identification, rows = edi_batch([{**COMMON}], flow_name="Generique")

    pool.generique_post_insert(uuid_identification, post=False)

    row = refresh(rows[0])
    assert (row.invoice_type, row.valid) == ("380", False)


@pytest.mark.usefixtures('refs')
def test_generique_post_insert_internal(edi_batch, make_section):
    refac = make_section("BU", "REFAC0")
    uuid_identification, rows = edi_batch(
        [{**COMMON, "third_party_num": "ZREFAC0", "vat_rate": Decimal("0.2"), "vat": None, "purchase_invoice": True}],
        flow_name="Generique_internal",
    )

    pool.generique_post_insert_internal(uuid_identification)

    row = refresh(rows[0])
    assert (row.purchase_invoice, row.sale_invoice, row.vat_id, row.axe_bu) == (False, True, "001", refac)


@pytest.mark.usefixtures('refs')
def test_hearing_post_insert(edi_batch):
    uuid_identification, rows = edi_batch([{**COMMON, "net_amount": Decimal("10.456")}], flow_name="Hearing")

    pool.hearing_post_insert(uuid_identification)

    row = refresh(rows[0])
    assert (row.invoice_type, row.gross_unit_price, row.net_unit_price, row.net_amount) == (
        "380", Decimal("10"), Decimal("5.228"), Decimal("10.46"),
    )


@pytest.mark.usefixtures('refs', 'pg_is_date')
def test_interson_post_insert(edi_batch):
    uuid_identification, rows = edi_batch(
        [
            {**COMMON, "gross_unit_price": Decimal("6"), "net_unit_price": Decimal("5"), "reference_article": "",
             "libelle": "Chronopost livraison express", "famille": "", "delivery_number": "BL12 du 15/01/2026"},
            {**COMMON, "gross_unit_price": Decimal("6"), "net_unit_price": Decimal("5"), "reference_article": "REF",
             "famille": "AUDIO", "delivery_number": "BL13 du hier", "invoice_number": "I2"},
        ],
        flow_name="Interson",
    )

    pool.interson_post_insert(uuid_identification)

    first, second = refresh(*rows)
    assert (first.gross_amount, first.net_amount, first.reference_article) == (Decimal("12"), Decimal("10"), "Chronopost livraison express")
    assert (first.famille, first.unit_weight_id, first.origin_id) == ("PORT", 4, 1)
    assert (first.delivery_number, first.delivery_date) == ("BL12", datetime.date(2026, 1, 15))
    # sans date valide, pas de date de BL ; post_general garde le premier mot du n° de BL
    assert (second.famille, second.delivery_number, second.delivery_date) == ("AUDIO", "BL13", None)


@pytest.mark.usefixtures('refs')
def test_johnson_post_insert(edi_batch):
    uuid_identification, rows = edi_batch(
        [
            {"invoice_number": "J1.0", "qty": Decimal("2"), "net_amount": Decimal("10"), "amount_with_vat": Decimal("12"),
             "reference_article": "123.0"},
            {"invoice_number": "J2", "qty": Decimal("-2"), "net_amount": Decimal("-10"), "amount_with_vat": Decimal("-10.55"),
             "reference_article": "456"},
            {"invoice_number": "J3", "qty": Decimal("1"), "net_amount": Decimal("0"), "amount_with_vat": Decimal("0"),
             "reference_article": "789"},
        ],
        flow_name="Johnson",
    )

    pool.johnson_post_insert(uuid_identification)

    first, credit, zero = refresh(*rows)
    assert (first.invoice_number, first.invoice_type, first.reference_article) == ("J1", "380", "123")
    assert (first.gross_unit_price, first.net_unit_price, first.gross_amount, first.vat_rate) == (
        Decimal("5"), Decimal("5"), Decimal("10"), Decimal("0.2"),
    )
    assert (credit.invoice_type, credit.vat_rate, credit.qty, credit.gross_amount) == ("381", Decimal("0.055"), Decimal("-2"), Decimal("-10"))
    assert (zero.vat_rate, zero.gross_amount, zero.qty) == (Decimal("0"), Decimal("0"), Decimal("1"))


@pytest.mark.usefixtures('refs')
def test_lmc_post_insert(edi_batch):
    uuid_identification, rows = edi_batch([{**COMMON, "gross_unit_price": Decimal("7")}], flow_name="Lmc")

    pool.lmc_post_insert(uuid_identification)

    row = refresh(rows[0])
    assert (row.invoice_type, row.gross_amount, row.origin_id) == ("380", Decimal("14"), 1)


@pytest.mark.usefixtures('refs')
def test_newson_post_insert(edi_batch):
    uuid_identification, rows = edi_batch(
        [
            {**COMMON, "net_amount": Decimal("10.456"), "amount_with_vat": Decimal("10.456"), "vat_rate": Decimal("0.2"),
             "reference_article": "NEW-1"},
            {**COMMON, "invoice_type": "AV", "qty": Decimal("2"), "net_amount": Decimal("10"), "vat_rate": Decimal("0.2"),
             "invoice_number": "N2"},
        ],
        flow_name="Newson",
    )

    pool.newson_post_insert(uuid_identification)

    first, credit = refresh(*rows)
    assert (first.invoice_type, first.gross_unit_price, first.net_unit_price, first.famille) == ("380", Decimal("10"), Decimal("5.228"), "NEW-1")
    assert first.net_amount == Decimal("10.46")
    assert credit.net_amount == Decimal("-10")


@pytest.mark.parametrize(
    ("function", "flow"), [(pool.phonak_post_insert, "Phonak"), (pool.unitron_post_insert, "Unitron")], ids=["phonak", "unitron"]
)
@pytest.mark.usefixtures('refs')
def test_phonak_unitron_post_insert(edi_batch, function, flow):
    """Date de facture ramenée en fin de mois pour toutes les lignes d'une même facture"""
    uuid_identification, rows = edi_batch(
        [
            {**COMMON, "invoice_number": "P1", "invoice_date": datetime.date(2026, 1, 3), "discount_price_01": Decimal("2000")},
            {**COMMON, "invoice_number": "P1", "invoice_date": datetime.date(2026, 1, 20), "discount_price_01": Decimal("10000"),
             "qty": Decimal("-1"), "net_amount": Decimal("5")},
        ],
        flow_name=flow,
    )

    function(uuid_identification)

    first, second = refresh(*rows)
    assert first.invoice_date == second.invoice_date == datetime.date(2026, 1, 31)
    assert (first.invoice_type, first.gross_unit_price, first.net_unit_price) == ("380", Decimal("10"), Decimal("5"))

    if flow == "Phonak":
        # remise exprimée en dix-millièmes ; remise totale -> prix et montant à zéro
        assert first.discount_price_01 == Decimal("0.2")
        assert (second.discount_price_01, second.net_unit_price, second.net_amount) == (Decimal("1"), Decimal("0"), Decimal("0"))


@pytest.mark.usefixtures('refs')
def test_phonak_signe_du_net(edi_batch):
    uuid_identification, rows = edi_batch(
        [{**COMMON, "qty": Decimal("-2"), "net_amount": Decimal("10"), "discount_price_01": Decimal("0")}], flow_name="Phonak"
    )

    pool.phonak_post_insert(uuid_identification)

    assert refresh(rows[0]).net_amount == Decimal("-10")


@pytest.mark.usefixtures('refs')
def test_prodition_post_insert(edi_batch):
    uuid_identification, rows = edi_batch(
        [
            {**COMMON, "qty": Decimal("0"), "libelle": "", "famille": "SOLAIRE", "reference_article": ""},
            {**COMMON, "invoice_type": "AV", "libelle": "Monture", "reference_article": "REF", "invoice_number": "P2"},
        ],
        flow_name="Prodition",
    )

    pool.prodition_post_insert(uuid_identification)

    first, second = refresh(*rows)
    assert (first.qty, first.libelle, first.reference_article, first.invoice_type) == (Decimal("1"), "SOLAIRE", "SOLAIRE", "380")
    assert (first.gross_unit_price, first.net_unit_price) == (Decimal("20"), Decimal("10"))
    assert (second.invoice_type, second.libelle) == ("381", "Monture")


@pytest.mark.usefixtures('refs')
def test_signia_post_insert(edi_batch):
    uuid_identification, rows = edi_batch(
        [
            {**COMMON, "invoice_type": "301", "qty": Decimal("0"), "libelle": "DELIVERY CHARGE", "famille": "X",
             "delivery_number": "BL-9", "invoice_number": "S1"},
            {**COMMON, "invoice_type": "302", "libelle": "WARRANTY plus", "delivery_number": "", "invoice_number": "S1",
             "net_amount": Decimal("-10"), "gross_amount": Decimal("10")},
            {**COMMON, "invoice_type": "400", "libelle": "DISCOUNT INSTANT", "invoice_number": "S2", "net_amount": Decimal("0")},
            {**COMMON, "invoice_type": "999", "libelle": "FREIGHT SEA", "invoice_number": "S3"},
        ],
        flow_name="Signia",
    )

    pool.signia_post_insert(uuid_identification)

    first, second, third, fourth = refresh(*rows)
    assert [row.invoice_type for row in (first, second, third, fourth)] == ["380", "381", "381", "380"]
    assert [row.famille for row in (first, second, third, fourth)] == ["PORT", "WARRANTY", "RFA", "PORT"]
    assert (first.qty, first.delivery_number, second.delivery_number) == (Decimal("1"), "BL-9", "BL-9")
    assert (second.qty, second.gross_amount, third.gross_amount) == (Decimal("-2"), Decimal("-10"), Decimal("0"))


@pytest.mark.usefixtures('refs')
def test_starkey_post_insert(edi_batch):
    uuid_identification, rows = edi_batch(
        [
            {**COMMON, "gross_unit_price": Decimal("6"), "import_uuid_identification": None},
            {**COMMON, "comment": "ENVOI_DEPOT", "invoice_number": "D1", "net_amount": Decimal("-10"), "gross_unit_price": Decimal("6")},
            {**COMMON, "net_amount": Decimal("0"), "invoice_number": "Z1"},
        ],
        flow_name="Starkey",
    )

    pool.starkey_post_insert(uuid_identification)

    first = refresh(rows[0])
    assert (first.invoice_type, first.net_unit_price, first.import_uuid_identification is not None) == ("380", Decimal("5"), True)
    assert (first.qty, first.gross_amount) == (Decimal("2"), Decimal("12"))
    # les envois en dépôt sont copiés dans edi_starkeydepot puis retirés de l'import
    assert not EdiImport.objects.filter(pk=rows[1].pk).exists()
    depot = StarkeyDepot.objects.get()
    # la copie précède la normalisation des quantités : valeurs d'origine
    assert (depot.invoice_number, depot.comment, depot.qty, depot.gross_amount) == ("D1", "ENVOI_DEPOT", Decimal("2"), Decimal("20"))
    assert refresh(rows[2]).gross_amount == Decimal("0")


@pytest.mark.usefixtures('refs')
def test_technidis_post_insert(edi_batch):
    uuid_identification, rows = edi_batch(
        [
            {**COMMON, "invoice_number": "T1", "net_amount": Decimal("-10"), "gross_unit_price": Decimal("6"), "famille": "",
             "reference_article": "LUN-123"},
            {**COMMON, "invoice_number": "T2", "net_amount": Decimal("10"), "gross_unit_price": Decimal("6"), "famille": "X"},
            {**COMMON, "invoice_number": "T3", "net_amount": Decimal("0"), "gross_unit_price": Decimal("6")},
        ],
        flow_name="Technidis",
    )

    pool.technidis_post_insert(uuid_identification)

    credit, debit, zero = refresh(*rows)
    assert (credit.invoice_type, credit.qty, credit.gross_amount, credit.famille) == ("381", Decimal("-2"), Decimal("-12"), "LUN")
    assert (credit.net_unit_price, credit.item_weight, credit.origin_id) == (Decimal("5"), Decimal("0"), 1)
    assert (debit.invoice_type, debit.gross_amount, debit.famille) == ("380", Decimal("12"), "X")
    assert zero.gross_amount == Decimal("0")


@pytest.mark.parametrize("function", [pool.widex_post_insert, pool.widexga_post_insert], ids=["widex", "widex_ga"])
@pytest.mark.usefixtures('refs')
def test_widex_post_insert(edi_batch, make_article, make_society, function):
    wsau = make_society("WSAU003", is_client=False)
    other = make_society("AUTR001", is_client=False)
    blank = make_article("W-1", wsau, libelle_heron="Libellé héron")
    kept = make_article("W-2", other, libelle_heron=None)
    uuid_identification, rows = edi_batch(
        [
            {**COMMON, "invoice_number": "W1", "famille": "", "gross_amount": Decimal("0"), "supplier_ident": "WIDE",
             "libelle": "Appareil", "amount_with_vat": Decimal("12")},
            {**COMMON, "invoice_number": "W1", "invoice_type": "AV", "net_amount": Decimal("-10"), "gross_amount": Decimal("20"),
             "supplier_ident": "WIDE", "amount_with_vat": Decimal("-12")},
            {**COMMON, "invoice_number": "W2", "net_amount": Decimal("0"), "supplier_ident": "WIDE"},
        ],
        flow_name="Widex",
    )

    function(uuid_identification)

    first, credit, zero = refresh(*rows)
    assert (first.invoice_type, first.famille, first.gross_amount, first.gross_unit_price, first.net_unit_price) == (
        "380", "ART-1", Decimal("10"), Decimal("5"), Decimal("5"),
    )
    assert first.libelle == "WIDE - Appareil"
    assert (credit.invoice_type, credit.qty, credit.gross_amount) == ("381", Decimal("-2"), Decimal("-20"))
    assert (first.invoice_amount_without_tax, first.invoice_amount_tax, first.invoice_amount_with_tax) == (
        Decimal("0"), Decimal("0"), Decimal("0"),
    )
    assert zero.gross_amount == Decimal("0")
    # Régression : le libellé héron n'est vidé que pour les articles WSAU003
    assert refresh(blank).libelle_heron == ""
    assert refresh(kept).libelle_heron is None
    assert Article.objects.count() == 2


@pytest.mark.usefixtures('refs')
def test_z_bu_refac_post_insert(edi_batch, make_society, make_vat_rat):
    make_society("ZREFAC0", is_client=False, short_name="REFAC")
    make_vat_rat("002", "5.5")
    uuid_identification, rows = edi_batch(
        [
            {"invoice_number": "Z1", "qty": Decimal("2"), "net_unit_price": Decimal("10"), "vat_id": "001", "vat_regime": "FRA",
             "devise": None, "invoice_date": datetime.date(2026, 2, 1)},
            {"invoice_number": "Z2", "qty": Decimal("-1"), "net_unit_price": Decimal("10"), "vat_id": "002", "vat_regime": "FRA",
             "invoice_date": datetime.date(2026, 2, 1)},
        ],
        flow_name="Zburefac",
        third_party_num="ZREFAC0",
    )

    pool.z_bu_refac_post_insert(uuid_identification)

    first, credit = refresh(*rows)
    assert (first.devise, first.gross_amount, first.net_amount, first.famille, first.origin_id) == (
        "EUR", Decimal("20"), Decimal("20"), "ART-1", 2,
    )
    assert (first.sale_invoice, first.purchase_invoice, first.manual_entry) == (True, False, False)
    assert (first.invoice_type, credit.invoice_type) == ("380", "381")
    assert (first.supplier, first.supplier_ident, first.supplier_name) == ("REFAC", "ZREFAC0", "REFAC")
    assert (first.vat_rate, credit.vat_rate) == (Decimal("0.2"), Decimal("0.055"))
