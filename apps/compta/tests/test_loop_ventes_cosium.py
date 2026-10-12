"""Tests de la boucle d'import journalier des ventes Cosium"""
import importlib
import platform
import sys
import types

import pendulum
import pytest

from apps.compta.loops import loop_ventes_cosium
from apps.data_flux.models import Trace
from conftest import patched_attrs, raising_once

pytestmark = pytest.mark.django_db


@pytest.fixture
def calls(monkeypatch):
    """Remplace les deux imports SQL par des enregistreurs"""
    recorded = []
    with patched_attrs(
        monkeypatch,
        loop_ventes_cosium,
        insert_ventes_cosium=lambda: recorded.append("insert"),
        mise_a_jour_ventes_cosium=lambda: recorded.append("maj"),
    ):
        yield recorded


def fake_now(day):
    return lambda *args, **kwargs: pendulum.datetime(2026, 1, day, 10, 0)


def test_process_hors_debut_de_mois(calls, monkeypatch):
    with patched_attrs(monkeypatch, pendulum, now=fake_now(15)):
        loop_ventes_cosium.process()

    assert calls == ["insert"]
    trace = Trace.objects.get()
    assert trace.errors is False
    assert trace.flow_name == "VentesCosium"
    assert trace.final_at is not None
    assert trace.time_to_process is not None


def test_process_debut_de_mois_lance_la_mise_a_jour(calls, monkeypatch):
    with patched_attrs(monkeypatch, pendulum, now=fake_now(3)):
        loop_ventes_cosium.process()

    assert calls == ["insert", "maj"]


@pytest.mark.parametrize("exception", [TypeError("type"), RuntimeError("boom")])
def test_process_erreurs(monkeypatch, exception, caplog):
    with raising_once(exception) as boom, patched_attrs(
        monkeypatch, loop_ventes_cosium, insert_ventes_cosium=boom
    ), caplog.at_level("ERROR", logger="import"):
        loop_ventes_cosium.process()

    trace = Trace.objects.get()
    assert trace.errors is True
    assert "Une erreur c'est produite" in trace.comment
    assert type(exception).__name__ in caplog.text or "Exception Générale" in caplog.text


@pytest.mark.parametrize(("node", "expected"), [("MSI", "/"), ("serveur", "/home/paulo/heron")])
def test_base_dir_selon_la_machine(monkeypatch, node, expected):
    monkeypatch.setattr(sys, "path", list(sys.path))

    try:
        with patched_attrs(monkeypatch, platform, uname=lambda: types.SimpleNamespace(node=node)):
            assert expected == importlib.reload(loop_ventes_cosium).BASE_DIR
    finally:
        importlib.reload(loop_ventes_cosium)
