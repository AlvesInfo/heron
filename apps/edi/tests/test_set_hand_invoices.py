"""
Tests de la création des factures saisies manuellement (chaîne réelle jusqu'à edi_ediimport)
"""
import datetime
from decimal import Decimal

import pytest

from apps.data_flux.models import Trace
from apps.edi.bin.set_hand_invoices import set_hand_invoice
from apps.edi.forms import CreateFormationInvoiceForm, CreateMarchandiseInvoiceForm
from apps.edi.models import EdiImport
from apps.edi.tests.helpers_saisie import entete, ligne, make_vat_rate


@pytest.fixture
def axes(make_section):
    """Les cinq axes Sage obligatoires sur les lignes saisies"""
    return {
        "axe_bu": make_section("BU", "CAHA"),
        "axe_prj": make_section("PRJ", "NAF"),
        "axe_pro": make_section("PRO", "OPT"),
        "axe_pys": make_section("PYS", "FR"),
        "axe_rfa": make_section("RFA", "NAF"),
    }


@pytest.fixture
def saisie(
    make_society, make_vat, make_maison, make_unit, make_icon_origin, make_article, make_user, make_counter, axes
):
    """Référentiel complet d'une saisie : tiers, TVA, maisons, unité, origine, article, utilisateur"""
    society = make_society("FOUR001", is_client=False, name="Fournisseur Un", short_name="FOURN1")
    make_vat_rate(make_vat, "001", "20")
    make_vat_rate(make_vat, "002", "5.5")
    make_unit(1, "U")
    make_icon_origin(4)
    make_counter("invoices_manual_entries_nums", num=7, lpad_num=5, separateur="-")
    maison = make_maison("AF0001")
    article = make_article(reference="REF-1", society=society, libelle="Monture acétate", **axes)
    return {
        "axes": axes,
        "society": society,
        "maison": maison,
        "maison_2": make_maison("AF0002"),
        "article": article,
        "user": make_user(),
    }


def test_single_line_success(saisie):
    error, message = set_hand_invoice(
        "marchandises",
        CreateMarchandiseInvoiceForm,
        entete(),
        [ligne(saisie["maison"], saisie["article"])],
        saisie["user"],
    )

    assert error is False
    assert message == "La Facture N°FA-001, pour le Fournisseur FOUR001, a bien été crée"
    line = EdiImport.objects.get()
    assert line.reference_article == "REF-1"
    assert line.libelle == "Monture acétate"
    assert line.qty == Decimal("2")
    assert line.net_amount == Decimal("20")
    assert line.vat_rate == Decimal("0.2")
    assert line.vat_amount == Decimal("4")
    assert line.amount_with_vat == Decimal("24")
    assert line.vat_regime == "FRA"
    assert (line.invoice_amount_without_tax, line.invoice_amount_tax, line.invoice_amount_with_tax) == (
        Decimal("20"), Decimal("4"), Decimal("24"),
    )
    assert line.purchase_invoice is True
    assert line.sale_invoice is True
    assert line.code_maison == "AF0001"
    assert line.code_fournisseur == "AF0001"
    assert line.maison == saisie["maison"].intitule
    assert line.supplier == "FOURN1"
    assert line.supplier_name == "Fournisseur Un"
    assert line.supplier_ident == "FOUR001"
    assert line.valid is True
    assert line.saisie is True
    assert line.manual_entry is True
    assert line.is_multi_store is False
    assert line.origin_id == 4
    assert line.created_by == saisie["user"]
    assert line.saisie_by == saisie["user"]
    assert line.invoice_month == datetime.date(2026, 1, 1)
    assert line.invoice_year == 2026
    assert line.unit_weight.unity == "U"
    assert line.axe_pro == saisie["axes"]["axe_pro"]
    assert line.axe_bu == saisie["axes"]["axe_bu"]
    # centrale/enseigne posées après création
    assert line.code_center == "ACF"
    assert line.code_signboard == "ACF"
    trace = Trace.objects.get()
    assert trace.errors is False
    assert trace.created_numbers_records == 1


def test_multi_store_and_counter_number(saisie):
    lines = [
        ligne(saisie["maison"], saisie["article"], num=1),
        ligne(saisie["maison_2"], saisie["article"], num=2, qty="1", net_unit_price="5.5", vat="002"),
    ]

    error, message = set_hand_invoice(
        "marchandises", CreateMarchandiseInvoiceForm, entete(invoice_number=""), lines, saisie["user"]
    )

    assert error is False
    assert message == "Les 2 lignes, de la Facture N°FOUR001-00007, pour le Fournisseur FOUR001, ont bien été crées"
    rows = list(EdiImport.objects.order_by("net_amount"))
    assert [row.is_multi_store for row in rows] == [True, True]
    assert {row.invoice_number for row in rows} == {"FOUR001-00007"}
    assert len({row.uuid_identification for row in rows}) == 1
    assert rows[0].vat_rate == Decimal("0.055")
    assert rows[0].vat_amount == Decimal("0.30")
    assert rows[1].invoice_amount_without_tax == Decimal("25.5")
    assert rows[1].invoice_amount_with_tax == Decimal("29.80")


def test_credit_note_inverts_quantity(saisie):
    error, _ = set_hand_invoice(
        "marchandises",
        CreateMarchandiseInvoiceForm,
        entete(invoice_type="381"),
        [ligne(saisie["maison"], saisie["article"], qty="3", net_unit_price="10")],
        saisie["user"],
    )

    assert error is False
    line = EdiImport.objects.get()
    assert line.qty == Decimal("-3")
    assert line.net_amount == Decimal("-30")
    assert line.vat_amount == Decimal("-6")
    assert line.amount_with_vat == Decimal("-36")
    assert line.invoice_amount_with_tax == Decimal("-36")


def test_given_vat_and_total_amounts_are_kept(saisie):
    error, _ = set_hand_invoice(
        "marchandises",
        CreateMarchandiseInvoiceForm,
        entete(),
        [ligne(saisie["maison"], saisie["article"], vat_amount="3,5", amount_with_vat="23,50")],
        saisie["user"],
    )

    assert error is False
    line = EdiImport.objects.get()
    assert line.vat_amount == Decimal("3.5")
    assert line.amount_with_vat == Decimal("23.5")
    assert line.invoice_amount_tax == Decimal("3.5")


def test_line_without_cct_reuses_previous_one(saisie):
    lines = [
        ligne(saisie["maison"], saisie["article"], num=1),
        ligne(saisie["maison"], saisie["article"], num=2, cct_uuid_identification=""),
    ]

    error, _ = set_hand_invoice("marchandises", CreateMarchandiseInvoiceForm, entete(), lines, saisie["user"])

    assert error is False
    assert list(EdiImport.objects.values_list("cct_uuid_identification", flat=True)) == [
        saisie["maison"].uuid_identification
    ] * 2


def test_article_unit_is_kept(saisie, make_unit, make_article):
    """L'unité de l'article (ici 9) n'est plus écrasée par l'unité U par défaut"""
    hours = make_unit(9, "H")
    article = make_article(reference="FORM-1", society=saisie["society"], unit_weight=hours, **saisie["axes"])

    error, _ = set_hand_invoice(
        "formation",
        CreateFormationInvoiceForm,
        entete(sens="1"),
        [
            ligne(
                saisie["maison"],
                article,
                qty="1",
                unit_weight="9",
                initial_date="2026-01-05",
                final_date="2026-01-06",
                last_name="Durand",
                first_name="Léa",
                heures_formation="7",
                formation_month="2026-01-01",
            )
        ],
        saisie["user"],
    )

    assert error is False
    line = EdiImport.objects.get()
    assert line.unit_weight.num == 9
    assert line.purchase_invoice is False
    assert line.sale_invoice is True


def test_invalid_line_returns_error_and_traces_it(saisie):
    """Une ligne invalide remonte l'erreur (plus écrasée par un return dans finally)"""
    error, message = set_hand_invoice(
        "marchandises",
        CreateMarchandiseInvoiceForm,
        entete(),
        [ligne(saisie["maison"], saisie["article"], cct_uuid_identification="00000000-0000-0000-0000-000000000000")],
        saisie["user"],
    )

    assert error is True
    assert message.startswith("cct_uuid_identification : ")
    assert EdiImport.objects.count() == 0
    trace = Trace.objects.get()
    assert trace.errors is True


def test_general_exception_is_caught(saisie, caplog):
    """Tiers inconnu : Society.DoesNotExist après validation des lignes"""
    error, message = set_hand_invoice(
        "marchandises",
        CreateMarchandiseInvoiceForm,
        entete(third_party_num="INCONNU"),
        [ligne(saisie["maison"], saisie["article"])],
        saisie["user"],
    )

    assert error is True
    assert message == "Une erreur c'est produite, veuillez consulter les logs"
    assert "Erreur : set_hand_invoice" in caplog.text
    assert Trace.objects.get().errors is True


def test_article_without_unit_gets_default_unit(saisie, make_article):
    """Article sans unité : la ligne reçoit l'unité U par défaut"""
    article = make_article(reference="SANS-UNITE", society=saisie["society"], unit_weight=None, **saisie["axes"])

    error, _ = set_hand_invoice(
        "marchandises",
        CreateMarchandiseInvoiceForm,
        entete(),
        [ligne(saisie["maison"], article, unit_weight="")],
        saisie["user"],
    )

    assert error is False
    assert EdiImport.objects.get().unit_weight.unity == "U"


def test_quantite_nulle_avec_tva_saisie(saisie):
    """Quantité à zéro et montant de TVA saisi : plus de division par zéro, la TVA saisie est gardée"""
    error, message = set_hand_invoice(
        "marchandises",
        CreateMarchandiseInvoiceForm,
        entete(),
        [ligne(saisie["maison"], saisie["article"], qty="0", vat_amount="3,5", amount_with_vat="3,5")],
        saisie["user"],
    )

    assert error is False, message
    line = EdiImport.objects.get()
    assert line.net_amount == Decimal("0")
    assert line.vat_amount == Decimal("3.5")
    assert line.amount_with_vat == Decimal("3.5")
