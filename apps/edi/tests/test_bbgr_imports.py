"""
Tests des insertions depuis les tables B.I BBGR (statment, monthly, retours, réceptions) dans
edi_ediimport : bornes d'identifiants historiques, transformation des colonnes, absence de lignes.

created at: 2026-10-10
created by: Paulo ALVES
"""
import datetime
import logging
from decimal import Decimal
from uuid import uuid4

import pytest

from apps.edi.bin import bbgr_002_statment, bbgr_003_monthly, bbgr_004_retours, bbgr_005_receptions
from apps.edi.models import EdiImport

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def _units(units):  # pylint: disable=W0613
    """Unités référencées par les insertions (1 et 11)"""

STATMENT = "heron_bi_factures_billstatement"
MONTHLY = "heron_bi_factures_monthlydelivery"
RECEPTIONS = "heron_bi_receptions_bbgr"


def rows_of(uuid_identification):
    return list(EdiImport.objects.filter(uuid_identification=uuid_identification).order_by("bi_id"))


def test_insert_bbgr_statment(bi_tables, make_society):
    make_society("BBGR001", is_client=False)
    base = bbgr_002_statment.HISTORIC_STATMENT_ID
    bi_tables(STATMENT, id=base - 5)  # historique : ignoré
    bi_tables(STATMENT, id=base + 1, article_facturation="12345678901234Verre unifocal", famille="", livraison="0",
              type_transaction="INV")
    bi_tables(STATMENT, id=base + 2, article_facturation="Monture", famille="MONTURES", type_transaction="CRN",
              qte_facturee=Decimal("-1"), montant_ht=Decimal("-10"))
    uuid_identification = uuid4()

    bbgr_002_statment.insert_bbgr_stament_file(uuid_identification)

    first, second = rows_of(uuid_identification)
    assert (first.flow_name, first.supplier_ident, first.supplier_name, first.siret_payeur) == (
        "BbgrStatment", "BbgrStatment", "BBGR STATMENT", "9524514",
    )
    assert (first.bi_id, first.invoice_type, first.libelle, first.famille, first.delivery_number) == (
        base + 1, "380", "Verre unifocal", "ART-1", "",
    )
    assert (first.code_fournisseur, first.code_maison, first.maison, first.acuitis_order_number) == ("BB001", "AF0001", "Maison test", "CDE1")
    assert (first.invoice_number, first.invoice_date, first.vat_rate, first.unit_weight_id) == ("TR1", datetime.date(2026, 1, 15), Decimal("0.2"), 1)
    assert (first.purchase_invoice, first.sale_invoice) == (True, False)
    assert (second.invoice_type, second.libelle, second.famille, second.delivery_number) == ("381", "Monture", "MONTURES", "BL1")


def test_insert_bbgr_statment_reprend_apres_le_dernier_import(bi_tables, edi_batch):
    base = bbgr_002_statment.HISTORIC_STATMENT_ID
    edi_batch([{"flow_name": "BbgrStatment", "bi_id": base + 10}])
    bi_tables(STATMENT, id=base + 5)
    bi_tables(STATMENT, id=base + 11)
    uuid_identification = uuid4()

    bbgr_002_statment.insert_bbgr_stament_file(uuid_identification)

    assert [row.bi_id for row in rows_of(uuid_identification)] == [base + 11]


def test_insert_bbgr_statment_sans_lignes(bi_tables, caplog):
    bi_tables(STATMENT, id=1)

    with caplog.at_level(logging.INFO, logger="edi"):
        bbgr_002_statment.insert_bbgr_stament_file(uuid4())

    assert EdiImport.objects.count() == 0
    assert "vérification BBGR statment" in caplog.text
    assert "intégration" not in caplog.text


def test_insert_bbgr_monthly(bi_tables, make_society):
    make_society("BBGR001", is_client=False)
    base = bbgr_003_monthly.HISTORIC_MONTHLY_ID
    bi_tables(MONTHLY, id=base + 1, livraison="", no_facture_acuitis="", famille=None, qte_expediee=Decimal("-2"))
    bi_tables(MONTHLY, id=base + 2, livraison="0", no_facture_acuitis="FA2")
    bi_tables(MONTHLY, id=base + 3, type_article="DECOTE")  # retours : ignorés ici
    uuid_identification = uuid4()

    bbgr_003_monthly.insert_bbgr_monthly_file(uuid_identification)

    first, second = rows_of(uuid_identification)
    assert (first.flow_name, first.supplier_name, first.invoice_number, first.invoice_type, first.famille) == (
        "BbgrMonthly", "BBGR MONTHLY", str(base + 1), "381", "ART-1",
    )
    assert (first.purchase_invoice, first.sale_invoice, first.acuitis_order_number, first.libelle) == (False, True, "PO1", "Monture")
    # livraison '0' : seul le n° de BL est vidé, le n° de facture reprend la livraison telle quelle
    assert (second.invoice_number, second.delivery_number, second.invoice_type) == ("0", "", "380")


@pytest.mark.usefixtures('bi_tables')
def test_insert_bbgr_monthly_sans_lignes():
    bbgr_003_monthly.insert_bbgr_monthly_file(uuid4())

    assert EdiImport.objects.count() == 0


def test_insert_bbgr_retours(bi_tables):
    base = bbgr_004_retours.HISTORIC_RETOURS_ID
    common = {"type_article": "FRAIS_RETOUR", "livraison": "BL7", "no_facture_acuitis": "", "famille": "RET", "prix_unitaire": Decimal("4")}
    bi_tables(MONTHLY, id=base + 1, qte_expediee=Decimal("1"), montant_ht=Decimal("4"), **common)
    bi_tables(MONTHLY, id=base + 2, qte_expediee=Decimal("2"), montant_ht=Decimal("8"), **common)
    bi_tables(MONTHLY, id=base + 3, type_article="DECOTE", description="Décote de 10%", article="ART-D", qte_expediee=Decimal("-1"))
    bi_tables(MONTHLY, id=base + 4, type_article="DECOTE", description="Décote de 25%", article="ART-D", livraison="")
    bi_tables(MONTHLY, id=base + 5, type_article="DECOTE", description="Décote de 50%", article="ART-D", livraison="", no_facture_acuitis="")
    bi_tables(MONTHLY, id=base + 6, type_article="MONTURE")  # monthly : ignoré
    uuid_identification = uuid4()

    bbgr_004_retours.insert_bbgr_retours_file(uuid_identification)

    rows = rows_of(uuid_identification)
    assert [row.reference_article for row in rows] == ["FRAIS_RETOUR", "D1-ART-D", "D2-ART-D", "D3-ART-D"]
    frais = rows[0]
    assert (frais.bi_id, frais.qty, frais.net_amount, frais.invoice_type, frais.libelle, frais.famille) == (
        base + 2, Decimal("3"), Decimal("12"), "380", "Frais de retour", "FRAIS_RETOUR",
    )
    assert (frais.invoice_number, frais.flow_name, frais.supplier_name, frais.vat_amount) == ("BL7", "BbgrRetours", "BBGR RETOURS", Decimal("0"))
    assert (rows[1].invoice_type, rows[1].invoice_number) == ("381", "BL1")
    assert (rows[2].invoice_number, rows[3].invoice_number) == ("FA1", str(base + 5))


@pytest.mark.usefixtures('bi_tables')
def test_insert_bbgr_retours_sans_lignes():
    bbgr_004_retours.insert_bbgr_retours_file(uuid4())

    assert EdiImport.objects.count() == 0


def test_insert_bbgr_receptions(bi_tables, make_vat_rat):
    make_vat_rat("001", "19.6", datetime.date(2000, 1, 1))
    make_vat_rat("001", "20", datetime.date(2014, 1, 1))
    base = bbgr_005_receptions.HISTORIC_RECEPTIONS_ID
    bi_tables(RECEPTIONS, id=base + 1, entered_date=datetime.date(2026, 1, 3), entered_valorise=Decimal("100"))
    bi_tables(RECEPTIONS, id=base + 2, entered_date=datetime.date(2026, 1, 20), entered_valorise=Decimal("50"))
    bi_tables(RECEPTIONS, id=base + 3, entered_date=datetime.date(2026, 2, 1), entered_valorise=Decimal("-30"), famille="MONT",
              type_article="MONTURE")
    uuid_identification = uuid4()

    bbgr_005_receptions.insert_bbgr_receptions_file(uuid_identification)

    january, february = rows_of(uuid_identification)
    assert (january.bi_id, january.invoice_number, january.delivery_number, january.invoice_date) == (
        base + 2, str(base + 2), f"BL-{base + 2}", datetime.date(2026, 1, 1),
    )
    assert (january.reference_article, january.libelle, january.famille, january.qty) == ("VERRE-VERRES", "VERRE-VERRES", "VERRES", Decimal("1"))
    assert (january.net_amount, january.vat_rate, january.vat_amount, january.amount_with_vat) == (
        Decimal("150"), Decimal("20"), Decimal("30"), Decimal("180"),
    )
    assert (january.invoice_type, january.unit_weight_id, january.supplier, january.code_maison) == ("380", 11, "BBGR RECEPTIONS", "BBGR001")
    assert (february.invoice_type, february.net_amount, february.axe_pro_supplier) == ("381", Decimal("-30"), "MONTURE")


@pytest.mark.usefixtures('bi_tables')
def test_insert_bbgr_receptions_sans_lignes():
    bbgr_005_receptions.insert_bbgr_receptions_file(uuid4())

    assert EdiImport.objects.count() == 0
