# pylint: disable=E0401,W0621,C0415
"""FR : Fabriques et fixtures propres aux tests de l'app compta (ventes Cosium, CA, abonnements)


EN : Fixtures for compta app tests

created at: 2026-10-10
created by: Paulo ALVES
"""

import datetime
import types
from collections.abc import Callable
from decimal import Decimal
from typing import Any

import pytest
from django.db import connection

from conftest import next_code, patched_attrs

# Table B.I des ventes Cosium (FDW en production), créée en DDL dans la transaction de test
BI_VENTES_COLUMNS = {
    "id": "integer",
    "id_vente": "text",
    "code_ean": "text",
    "code_maison": "text",
    "code_cosium": "text",
    "famille_cosium": "text",
    "rayon_cosium": "text",
    "date_vente": "date",
    "qte_vente": "numeric",
    "remise": "numeric",
    "taux_tva": "numeric",
    "tva_x3": "text",
    "tva": "numeric",
    "total_ttc": "numeric",
    "pv_brut_unitaire": "numeric",
    "pv_net_unitaire": "numeric",
    "px_vente_ttc_devise": "numeric",
    "px_vente_ttc_devise_apres_remise": "numeric",
    "ca_ht_avt_remise": "numeric",
    "ca_ht_ap_remise": "numeric",
    "taux_change": "numeric",
    "pv_brut_unitaire_eur": "numeric",
    "pv_net_unitaire_eur": "numeric",
    "px_vente_ttc_eur": "numeric",
    "px_vente_ttc_eur_apres_remise": "numeric",
    "ca_ht_avt_remise_eur": "numeric",
    "ca_ht_ap_remise_eur": "numeric",
    "px_achat_global": "numeric",
    "px_achat_unitaire": "numeric",
    "solde": "numeric",
    "maj_stock": "numeric",
    "age_client": "integer",
    "centre_de_gestion": "text",
    "centre_payeur": "text",
    "code_barre_2": "text",
    "code_marketing_1": "text",
    "date_age_client": "date",
    "date_creation": "date",
    "date_encaissement": "date",
    "date_ordo": "date",
    "designation": "text",
    "filtre_pack": "text",
    "fournisseur": "text",
    "indentification_equip": "integer",
    "indice": "numeric",
    "lentilles": "text",
    "marque": "text",
    "nom_mutuelle": "text",
    "num_client": "text",
    "num_devis_avoir": "text",
    "num_facture": "text",
    "pays": "text",
    "photochromique": "integer",
    "prescripteur_na": "text",
    "prescripteurs": "text",
}

SALE_DATE = datetime.date(2026, 1, 15)
SALE_MONTH = SALE_DATE.replace(day=1)


@pytest.fixture
def bi_ventes_table(db) -> Callable[..., int]:  # pylint: disable=W0613
    """Crée heron_bi_ventes_cosium et renvoie `insert_bi(**colonnes) -> id` (id > HISTORIC par défaut)"""
    from apps.compta.imports.import_ventes_cosium import HISTORIC_VENTES_ID

    ddl = ", ".join(f'"{name}" {kind}' for name, kind in BI_VENTES_COLUMNS.items())

    with connection.cursor() as cursor:
        cursor.execute(f'create table if not exists "heron_bi_ventes_cosium" ({ddl})')

    counter = {"id": HISTORIC_VENTES_ID}

    def _insert(**values: Any) -> int:
        counter["id"] += 1
        row: dict[str, Any] = {
            "id": counter["id"],
            "id_vente": f"V{counter['id']}",
            "code_ean": "3660000000001",
            "code_maison": "AF0001",
            "code_cosium": "COS1",
            "famille_cosium": "LUNETTES",
            "rayon_cosium": "OPTIQUE",
            "date_vente": SALE_DATE,
            "qte_vente": Decimal(1),
            "ca_ht_avt_remise": Decimal(110),
            "ca_ht_ap_remise": Decimal(100),
            "pv_brut_unitaire": Decimal(110),
            "pv_net_unitaire": Decimal(100),
            "px_vente_ttc_devise": Decimal(120),
            "px_vente_ttc_devise_apres_remise": Decimal(120),
            "taux_change": Decimal(1),
            "maj_stock": Decimal(0),
        }
        row.update(values)
        columns = ", ".join(f'"{name}"' for name in row)
        placeholders = ", ".join(f"%({name})s" for name in row)

        with connection.cursor() as cursor:
            cursor.execute(
                f'insert into "heron_bi_ventes_cosium" ({columns}) values ({placeholders})', row
            )

        return int(row["id"])

    return _insert


@pytest.fixture
def make_vente(db) -> Callable[..., Any]:  # pylint: disable=W0613
    """Fabrique de compta.VentesCosium"""
    from apps.compta.models import VentesCosium

    counter = {"id_bi": 1}

    def _factory(**kwargs: Any):
        counter["id_bi"] += 1
        defaults = {
            "id_bi": counter["id_bi"],
            "id_vente": f"V{counter['id_bi']}",
            "code_ean": "3660000000001",
            "code_maison": "AF0001",
            "code_cosium": "COS1",
            "famille_cosium": "LUNETTES",
            "rayon_cosium": "OPTIQUE",
            "date_vente": SALE_DATE,
            "sale_month": SALE_DATE.replace(day=1),
            "qte_vente": Decimal(1),
            "pv_net_unitaire": Decimal(100),
            "pv_brut_unitaire": Decimal(110),
            "ca_ht_avt_remise": Decimal(110),
            "ca_ht_ap_remise": Decimal(100),
            "ca_ht_ap_remise_eur": Decimal(100),
            "ca_ht_avt_remise_eur": Decimal(110),
            "px_vente_ttc_devise": Decimal(120),
            "px_vente_ttc_devise_apres_remise": Decimal(120),
            "maj_stock": Decimal(0),
        }
        defaults.update(kwargs)
        return VentesCosium.objects.create(**defaults)

    return _factory


@pytest.fixture
def make_ca_client(make_maison, make_section) -> Callable[..., Any]:
    """Fabrique de compta.CaClients (CA par maison et axe pro)"""
    from apps.compta.models import CaClients

    def _factory(maison=None, axe_pro=None, **kwargs: Any):
        defaults = {
            "date_ca": datetime.date(2026, 1, 31),
            "cct_uuid_identification": maison or make_maison(),
            "axe_pro": axe_pro or make_section("PRO", "OPT"),
            "famille_cosium": "LUNETTES",
            "ca_ht_eur": Decimal(100),
            "ca_ht_devise": Decimal(100),
        }
        defaults.update(kwargs)
        defaults.setdefault("code_maison", defaults["cct_uuid_identification"].cct.cct)
        defaults.setdefault("code_cosium", "COS1")
        return CaClients.objects.create(**defaults)

    return _factory


@pytest.fixture
def make_exchange_rate(make_country_currency) -> Callable[..., Any]:
    """Fabrique de parameters.ExchangeRate (taux mensuel d'une devise vers l'euro)"""
    from apps.parameters.models import ExchangeRate

    def _factory(currency: str = "CHF", rate_month: datetime.date = SALE_MONTH, rate=Decimal(2)):
        return ExchangeRate.objects.create(
            currency_change=make_country_currency(currency), rate_month=rate_month, rate=rate
        )

    return _factory


@pytest.fixture
def cosium_familly_axes(make_supplier_family_axes, make_section) -> Callable[..., Any]:
    """Traduction famille Cosium -> axe pro dans la stat COSI001 (book.SupplierFamilyAxes)"""

    def _factory(famille: str = "LUNETTES", section: str = "OPT"):
        return make_supplier_family_axes(
            regex_match=famille, stat_name="COSI001", axe_pro=make_section("PRO", section)
        )

    return _factory


@pytest.fixture
def month_period() -> types.SimpleNamespace:
    """Période valide du MonthForm (mois précédent) : value "dte_d_dte_f", dte_d, dte_f"""
    from apps.periods.forms.forms_django.periodes_forms import get_month_choices

    value = get_month_choices()["initial"][0]
    dte_d, dte_f = value.split("_")
    return types.SimpleNamespace(value=value, dte_d=dte_d, dte_f=dte_f)


@pytest.fixture
def thread_recorder(monkeypatch) -> Callable[[types.ModuleType], list]:
    """Remplace threading.Thread d'un module de vues : enregistre (target, args) sans lancer"""

    def _patch(module) -> list:
        started = []

        class _Thread:
            def __init__(self, target, args, daemon):
                self.target, self.args, self.daemon = target, args, daemon

            def start(self):
                started.append((self.target, self.args, self.daemon))

        monkeypatch.setattr(module, "threading", types.SimpleNamespace(Thread=_Thread))
        return started

    return _patch


@pytest.fixture
def subscription_checks(monkeypatch):
    """Remplace les contrôles externes des vues d'abonnements par des valeurs pilotables :

    checks.subscription, checks.in_action, checks.not_finalize, checks.missing, checks.have_subs
    """
    from apps.compta.views import subscriptions_views

    checks = types.SimpleNamespace(
        subscription=True, in_action=False, not_finalize=False, missing="", have_subs=False
    )
    with patched_attrs(
        monkeypatch,
        subscriptions_views,
        have_subscription=lambda subscription_name: checks.subscription,
        have_action_in_progress=lambda: checks.in_action,
        have_send_email_without_finalize=lambda: checks.not_finalize,
        get_missing_cosium_familly=lambda dte_d, dte_f: checks.missing,
        get_have_subscriptions=lambda flow_name, dte_d, dte_f: checks.have_subs,
    ):
        yield checks


@pytest.fixture
def make_invoice_with_detail(make_society) -> Callable[..., Any]:
    """Fabrique d'une facture définitive (invoices.Invoice + InvoiceDetail) pour un flux"""
    from apps.invoices.models import Invoice, InvoiceDetail

    def _factory(
        flow_name: str = "ROYALTIES", invoice_date: datetime.date = SALE_DATE, **kwargs: Any
    ):
        invoice = Invoice.objects.create(
            third_party_num=make_society("ZROYAL"),
            invoice_sage_number=next_code("SAGE"),
            invoice_date=invoice_date,
            **kwargs,
        )
        detail = InvoiceDetail.objects.create(
            uuid_invoice=invoice,
            import_uuid_identification=__import__("uuid").uuid4(),
            axe_bu="BU",
            axe_prj="PRJ",
            axe_pro="PRO",
            axe_rfa="RFA",
            axe_pys="PYS",
            vat="001",
            vat_rate=Decimal("0.2"),
            vat_regime="FRA",
            big_category="Abonnements",
            account="706000",
            flow_name=flow_name,
        )
        return invoice, detail

    return _factory
