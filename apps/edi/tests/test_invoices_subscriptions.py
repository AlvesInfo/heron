"""
Tests de la génération des factures d'abonnements (royalties, meuleuses, publicité, prestations)
"""
import logging
from decimal import Decimal

import pytest

from apps.data_flux.models import Trace
from apps.edi.bin import invoices_subsricptions
from conftest import patched_attrs

GENERATORS = [
    (invoices_subsricptions.meuleuse, "MEULEUSE", "Génération des redevances meuleuses"),
    (invoices_subsricptions.services, "PRESTATIONS", "Génération des prestations"),
    (invoices_subsricptions.publicity, "PUBLICITE", "Génération des redevances de publicité"),
    (invoices_subsricptions.royalties, "ROYALTIES", "Génération des royalties"),
]


def test_set_invoice_amounts_sums_lines_by_invoice(make_edi_import):
    common = {"third_party_num": "ZROY", "flow_name": "ROYALTIES", "supplier": "Royalties", "invoice_number": "R1"}
    first = make_edi_import(net_amount=10, vat_amount=2, amount_with_vat=12, **common)
    second = make_edi_import(net_amount=20, vat_amount=4, amount_with_vat=24, **common)
    other = make_edi_import(
        net_amount=5, vat_amount=1, amount_with_vat=6, third_party_num="ZROY", flow_name="MEULEUSE",
        supplier="Meuleuse", invoice_number="M1",
    )

    invoices_subsricptions.set_invoice_amounts("ROYALTIES")

    for line in (first, second):
        line.refresh_from_db()
        assert (line.invoice_amount_without_tax, line.invoice_amount_tax, line.invoice_amount_with_tax) == (
            Decimal("30"), Decimal("6"), Decimal("36"),
        )

    other.refresh_from_db()
    assert other.invoice_amount_without_tax == 0


@pytest.mark.usefixtures('db')
def test_set_data_runs_ca_then_subscriptions_query(monkeypatch):
    calls = []

    def _set_ca(dte_d, dte_f, user_uuid):
        calls.append(("set_ca", dte_d, dte_f, user_uuid))

    def _query_execute(cnx, sql_query, params):
        calls.append(("query", sql_query, params))
        return 3

    with patched_attrs(monkeypatch, invoices_subsricptions, set_ca=_set_ca, query_execute=_query_execute):
        rows = invoices_subsricptions.set_data("2026-01-01", "2026-01-31", "uuid-user", "ROYALTIES")

    assert rows == 3
    assert calls[0] == ("set_ca", "2026-01-01", "2026-01-31", "uuid-user")
    assert calls[1][1] is invoices_subsricptions.SQL_SUBSCRIPTIONS
    params = calls[1][2]
    assert (params["dte_d"], params["dte_f"], params["flow_name"], params["created_by"]) == (
        "2026-01-01", "2026-01-31", "ROYALTIES", "uuid-user",
    )
    assert "uuid_identification" in params


@pytest.mark.parametrize(("generator", "flow_name", "label"), GENERATORS)
def test_generators_success(monkeypatch, make_user, generator, flow_name, label):
    user = make_user()
    seen = {}

    def _set_data(dte_d, dte_f, user_uuid, flow):
        seen.update(flow=flow, user=user_uuid)
        return 5

    with patched_attrs(
        monkeypatch, invoices_subsricptions, set_data=_set_data, set_invoice_amounts=lambda flow: seen.update(amounts=flow)
    ):
        trace, to_print = generator("2026-01-01", "2026-01-31", user.uuid_identification)

    assert seen == {"flow": flow_name, "user": user.uuid_identification, "amounts": flow_name}
    assert to_print == f"{label} "
    assert trace.errors is False
    assert trace.flow_name == flow_name
    assert trace.created_by == user
    assert trace.final_at is not None
    assert trace.time_to_process is not None
    assert Trace.objects.get(pk=trace.pk).comment == ""


@pytest.mark.parametrize(("generator", "flow_name", "label"), GENERATORS)
def test_generators_without_subscriptions(monkeypatch, make_user, generator, flow_name, label):
    user = make_user()

    with patched_attrs(
        monkeypatch, invoices_subsricptions, set_data=lambda *_args: 0, set_invoice_amounts=lambda flow: None
    ):
        trace, to_print = generator("2026-01-01", "2026-01-31", user.uuid_identification)

    assert to_print.startswith(f"Erreur {label}")
    assert f"pas d'abonnements '{flow_name}' à générer" in to_print
    assert trace.errors is False


@pytest.mark.parametrize(("generator", "flow_name", "label"), GENERATORS)
def test_generators_exception(monkeypatch, make_user, caplog, generator, flow_name, label):
    user = make_user()

    def _boom(*_args):
        raise RuntimeError("sql cassé")

    with patched_attrs(monkeypatch, invoices_subsricptions, set_data=_boom), caplog.at_level(
        logging.ERROR, logger="edi"
    ):
        trace, to_print = generator("2026-01-01", "2026-01-31", user.uuid_identification)

    assert trace.errors is True
    assert trace.comment == "Une erreur c'est produite veuillez consulter les logs"
    assert to_print.startswith("Erreur")
    assert "sql cassé" in caplog.text


def test_generator_exception_keeps_existing_comment(monkeypatch, make_user, make_trace):
    """Le commentaire existant de la trace est conservé devant le message d'erreur"""
    user = make_user()
    trace = make_trace(comment="déjà là")

    def _boom(*_args):
        raise RuntimeError("x")

    with patched_attrs(monkeypatch, invoices_subsricptions, set_data=_boom, get_trace=lambda *_a: trace):
        result, _ = invoices_subsricptions.royalties("2026-01-01", "2026-01-31", user.uuid_identification)

    assert result.comment == "déjà là. Une erreur c'est produite veuillez consulter les logs"
