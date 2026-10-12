"""Tests des contrôles préalables à la facturation (SQL réelles)"""
import logging

import pytest

from apps.edi.models import EdiImport
from apps.invoices.bin import pre_controls
from conftest import patched_attrs

pytestmark = pytest.mark.django_db


@pytest.fixture
def complete_line(make_edi_import, make_maison, make_section, make_big_category, make_vat, make_article, make_society):
    """Une ligne edi complète : axes, tiers, tva, régime, cct, catégorie, centrale, enseigne"""
    axes = {axe: make_section(axe, code) for axe, code in [("BU", "CAHA"), ("PRJ", "NAF"), ("PRO", "OPT"), ("PYS", "FR"), ("RFA", "NAF")]}
    category = make_big_category("Marchandises")
    article = make_article("ART-1", society=make_society("FOUR001", is_client=False), big_category=category, axe_pro=axes["PRO"],
                           axe_bu=axes["BU"], axe_prj=axes["PRJ"], axe_pys=axes["PYS"], axe_rfa=axes["RFA"], new_article=False)
    maison = make_maison("AF0001")

    def _factory(**kwargs):
        values = {
            "axe_bu": axes["BU"], "axe_prj": axes["PRJ"], "axe_pro": axes["PRO"], "axe_pys": axes["PYS"], "axe_rfa": axes["RFA"],
            "vat": make_vat("001"), "vat_regime": "FRA", "cct_uuid_identification": maison,
            "big_category": category, "code_center": "ACF", "code_signboard": "ACF",
        }
        values.update(kwargs)
        return make_edi_import(**values)

    _factory.axes = axes
    _factory.category = category
    _factory.article = article
    return _factory


CONTROLS = [
    ("control_articles_axes", {"axe_pro": None}, "axes"),
    ("control_tiers", {"third_party_num": ""}, "tiers X3"),
    ("control_vat", {"vat": None}, "TVA X3"),
    ("control_vat_regime", {"vat_regime": ""}, "régimes de TAX"),
    ("control_cct", {"cct_uuid_identification": None}, "CCT X3"),
    ("control_categories", {"big_category": None}, "Grandes Catégories"),
]


@pytest.mark.parametrize(("function", "missing", "message"), CONTROLS)
def test_controles_simples(complete_line, function, missing, message):
    complete_line()

    assert getattr(pre_controls, function)() == ""

    if "third_party_num" in missing:
        EdiImport.objects.update(third_party_num="")
    else:
        complete_line(**missing)

    assert message in getattr(pre_controls, function)()


def test_control_sub_categories(complete_line, make_sub_category):
    complete_line()

    assert pre_controls.control_sub_categories() == ""

    make_sub_category("Rubrique", big_category=complete_line.category)

    assert "Rubriques Presta" in pre_controls.control_sub_categories()


def test_control_groupings(complete_line, make_grouping):
    complete_line()

    assert "regroupement" in pre_controls.control_groupings()

    make_grouping("OPT")

    assert pre_controls.control_groupings() == ""


def test_control_accounts(complete_line, make_accounts_axe_pro_category):
    complete_line()

    assert "Dictionnaire des Comptes" in pre_controls.control_accounts()

    make_accounts_axe_pro_category(axe_pro=complete_line.axes["PRO"], big_category=complete_line.category)

    assert pre_controls.control_accounts() == ""


def test_control_accounts_articles(complete_line, make_article_account):
    complete_line()

    assert "comptes dans les articles" in pre_controls.control_accounts_articles()

    make_article_account(complete_line.article, "ACF", "001")

    assert pre_controls.control_accounts_articles() == ""


def test_control_axe_bu_od_ana(make_maison, make_section):
    make_maison("AF0001", type_x3=2, axe_bu=None)

    assert "axe bu" in pre_controls.control_axe_bu_od_ana()

    from apps.centers_clients.models import Maison

    Maison.objects.update(axe_bu=make_section("BU", "CAHA"))

    assert pre_controls.control_axe_bu_od_ana() == ""


@pytest.mark.usefixtures('sync_controls')
def test_control_alls_missings_tout_manque(make_edi_import, make_edi_validation, make_article):
    """Ligne edi vide de tout paramétrage : les contrôles bloquants et les validations remontent"""
    make_edi_validation()
    make_edi_import(third_party_num="FOUR001", vat=None, vat_regime="", code_center=None, code_signboard=None)
    make_article("ART-1", new_article=True)

    result = pre_controls.control_alls_missings()

    assert set(result) >= {"tva", "regimes", "categories", "center_purchase", "signboard", "articles", "articles_news",
                           "integrations", "cct", "familles", "franchiseur", "clients_new", "abonnements", "rfa",
                           "cct_m", "suppliers_m", "ca_cosium"}
    assert result["articles_news"][1].endswith("/")
    assert result["cct"][0].startswith("Il manque des CCT")


@pytest.mark.usefixtures('sync_controls')
def test_control_alls_missings_complet(complete_line, make_edi_validation, make_grouping, make_accounts_axe_pro_category, make_article_account, make_edi_import_control):
    """Tout est paramétré et validé : aucun manquant"""
    make_edi_validation(integration=True, families=True, franchiseurs=True, clients_news=True, subscriptions=True,
                        rfa=True, refac_cct=True, suppliers=True, validation_ca=True, cct=True,
                        articles_news=True, articles_without_account=True)
    control = make_edi_import_control(valid=True, comment="ok")
    complete_line(uuid_control=control)
    make_grouping("OPT")
    make_accounts_axe_pro_category(axe_pro=complete_line.axes["PRO"], big_category=complete_line.category)
    make_article_account(complete_line.article, "ACF", "001")

    assert pre_controls.control_alls_missings() == {}


@pytest.mark.usefixtures('sync_controls')
def test_control_alls_missings_supprime_les_controles_orphelins(make_edi_import_control, make_edi_validation):
    from apps.edi.models import EdiImportControl

    make_edi_validation()
    orphan = make_edi_import_control(valid=True)

    pre_controls.control_alls_missings()

    assert not EdiImportControl.objects.filter(pk=orphan.pk).exists()


def test_control_insertion(make_sale_invoice):
    assert pre_controls.control_insertion() is False

    make_sale_invoice(send_email=True, final=False)

    assert pre_controls.control_insertion() is True


def test_control_insertion_supprime_les_imports(make_sale_invoice, make_edi_import):
    make_edi_import()
    make_sale_invoice(send_email=True, final=False)

    assert pre_controls.control_insertion() is True
    assert EdiImport.objects.count() == 0


@pytest.mark.usefixtures('make_sale_invoice')
def test_control_insertion_async(monkeypatch):
    """La version asynchrone enchaîne le contrôle et le nettoyage des connexions"""
    calls = []
    with patched_attrs(monkeypatch, pre_controls, close_old_connections=lambda: calls.append("close")):
        assert pre_controls._control_insertion_with_cleanup() is False  # pylint: disable=W0212

    assert calls == ["close"]
    assert pre_controls.control_insertion_async.__wrapped__ is not None or callable(pre_controls.control_insertion_async)


def test_control_emails(make_sale_invoice):
    to_send = make_sale_invoice(printed=True, send_email=False, type_x3=1)
    make_sale_invoice("AF0002", printed=False)
    make_sale_invoice("AF0003", printed=True, send_email=True)

    assert list(pre_controls.control_emails()) == [to_send]


def test_control_validations(make_edi_import_control, make_edi_validation, make_article, caplog):
    make_edi_import_control(valid=False)
    validation = make_edi_validation(integration=True, families=True)
    make_article("ART-1", new_article=True)

    with caplog.at_level(logging.INFO, logger="invoices_flux"):
        controls = pre_controls.control_validations()

    assert controls[0] == "Vous avez des imports non validés"
    assert "La Validation sur Ecran 1.1 Nouveaux Articles" in controls
    assert "La Validation sur Ecran 2.1 Intégrations" not in controls
    assert "La Validation sur Ecran 3.1 Contrôles Familles" not in controls
    validation.refresh_from_db()
    assert validation.articles_news is False
    assert validation.articles_without_account is True
    assert "controls_list" in caplog.text


def test_control_validations_articles_valides(make_edi_validation, make_article, make_section, make_big_category):
    validation = make_edi_validation()
    axes = {axe: make_section(axe, code) for axe, code in [("BU", "CAHA"), ("PRJ", "NAF"), ("PRO", "OPT"), ("PYS", "FR"), ("RFA", "NAF")]}
    make_article("ART-1", big_category=make_big_category("Marchandises"), new_article=False, axe_bu=axes["BU"],
                 axe_prj=axes["PRJ"], axe_pro=axes["PRO"], axe_pys=axes["PYS"], axe_rfa=axes["RFA"])

    pre_controls.control_validations()

    validation.refresh_from_db()
    assert validation.articles_news is True


def test_control_validations_articles_sans_comptes(complete_line, make_edi_validation, make_vat_rat):
    """Un article importé sans compte pour sa TVA invalide l'écran 1.2"""
    validation = make_edi_validation()
    make_vat_rat("001", "20")
    complete_line()

    pre_controls.control_validations()

    validation.refresh_from_db()
    assert validation.articles_without_account is False


def test_articles_are_valid_et_control_all(make_article):
    assert pre_controls.articles_are_valid() is True
    assert pre_controls.control_all() is None

    make_article("ART-1", new_article=True)

    assert pre_controls.articles_are_valid() is False
