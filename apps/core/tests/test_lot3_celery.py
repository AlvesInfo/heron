# pylint: disable=E0401,W0621
"""FR : Tests des utilitaires de surveillance Celery et de la commande check_celery (broker simulé)


EN : Tests for Celery monitoring utilities and the check_celery command (mocked broker)

created at: 2026-10-11
created by: Paulo ALVES
"""

import io
import types

import pytest
from django.core.management import call_command

from apps.core.utils import celery_utils
from apps.core.utils.celery_utils import (
    get_active_tasks_list,
    get_celery_tasks_status,
    get_celery_workers_stats,
    has_active_celery_tasks,
    is_celery_available,
    wait_for_celery_idle,
)
from conftest import patched_attrs

TASK = {"id": "t1", "name": "apps.edi.tasks.launch", "args": [], "kwargs": {}, "time_start": 1.0}


@pytest.fixture
def inspector(monkeypatch):
    """Remplace app.control.inspect() par un inspecteur simulé, configurable par test"""
    state = {"active": None, "scheduled": None, "reserved": None, "stats": None}

    class _Inspect:
        def active(self):
            return state["active"]

        def scheduled(self):
            return state["scheduled"]

        def reserved(self):
            return state["reserved"]

        def stats(self):
            return state["stats"]

    monkeypatch.setattr(celery_utils.app.control, "inspect", lambda: _Inspect())
    return state


def test_statut_sans_worker(inspector):
    status = get_celery_tasks_status()

    assert status == {
        "has_tasks": False,
        "total": 0,
        "active": 0,
        "scheduled": 0,
        "reserved": 0,
        "workers": [],
        "details": {"active": {}, "scheduled": {}, "reserved": {}},
    }
    assert has_active_celery_tasks() is False
    assert is_celery_available() is False


def test_statut_avec_taches(inspector):
    inspector.update(
        {
            "active": {"w1": [TASK], "w2": []},
            "scheduled": {"w1": [TASK, TASK]},
            "reserved": {"w3": None},
            "stats": {"w1": {}},
        }
    )

    status = get_celery_tasks_status()

    assert (
        status["has_tasks"],
        status["total"],
        status["active"],
        status["scheduled"],
        status["reserved"],
    ) == (True, 3, 1, 2, 0)
    assert sorted(status["workers"]) == ["w1", "w2", "w3"]
    assert has_active_celery_tasks() is True
    assert is_celery_available() is True


def test_liste_des_taches_actives(inspector):
    inspector["active"] = {"w1": [TASK], "w2": None}

    assert get_active_tasks_list() == [
        {
            "worker": "w1",
            "task_id": "t1",
            "task_name": "apps.edi.tasks.launch",
            "args": [],
            "kwargs": {},
            "time_start": 1.0,
        }
    ]
    inspector["active"] = None
    assert get_active_tasks_list() == []


def test_attente_de_fin_des_taches(inspector, monkeypatch):
    """Retour immédiat sans tâche, sinon attente jusqu'au délai avec le nombre restant"""
    sleeps = []
    monkeypatch.setattr(celery_utils.time, "sleep", sleeps.append) if hasattr(
        celery_utils, "time"
    ) else None
    import time  # pylint: disable=C0415

    monkeypatch.setattr(time, "sleep", sleeps.append)

    assert wait_for_celery_idle(timeout=10) == (True, 0)

    inspector["active"] = {"w1": [TASK]}
    assert wait_for_celery_idle(timeout=4, check_interval=2) == (False, 1)
    assert sleeps == [2, 2]


def test_statistiques_des_workers(inspector):
    inspector["stats"] = {
        "w1": {"pool": {"implementation": "prefork", "max-concurrency": 8}, "total": {"t": 3}},
        "w2": {},
    }

    assert get_celery_workers_stats() == {
        "w1": {"pool": "prefork", "max_concurrency": 8, "total_tasks": {"t": 3}},
        "w2": {"pool": None, "max_concurrency": None, "total_tasks": {}},
    }
    inspector["stats"] = None
    assert get_celery_workers_stats() == {}


# COMMANDE =========================================================================================


def _run(*args):
    out = io.StringIO()
    call_command("check_celery", *args, stdout=out)
    return out.getvalue()


def test_commande_sans_worker(inspector):
    assert "Aucun worker Celery disponible" in _run()


def test_commande_sans_tache(inspector):
    inspector["stats"] = {"w1": {}}

    output = _run()

    assert "Aucune tâche en cours" in output
    assert "Workers actifs: 0" in output


def test_commande_avec_taches_et_details(inspector):
    inspector.update(
        {
            "stats": {"w1": {}},
            "active": {"w1": [TASK, {**TASK, "id": "t2", "time_start": None}]},
            "scheduled": {"w1": [TASK]},
        }
    )

    output = _run("--details")

    assert "3 tâche(s) en cours" in output
    assert "- Actives: 2" in output
    assert "- Planifiées: 1" in output
    assert "- Réservées: 0" in output
    assert output.count("Worker: w1") == 2
    assert output.count("Démarrée: 1.0") == 1


def test_commande_details_sans_tache_active(inspector):
    inspector.update({"stats": {"w1": {}}, "scheduled": {"w1": [TASK]}})

    output = _run("--details")

    assert "1 tâche(s) en cours" in output
    assert "Détails" not in output


def test_commande_attente(inspector, monkeypatch):
    import time  # pylint: disable=C0415

    inspector["stats"] = {"w1": {}}
    monkeypatch.setattr(time, "sleep", lambda _s: None)

    assert "Toutes les tâches sont terminées" in _run("--wait")

    inspector["active"] = {"w1": [TASK]}
    assert "Timeout atteint: 1 tâche(s) encore en cours" in _run("--wait", "--timeout", "2")


def test_module_celery_utils_expose_l_application():
    assert isinstance(celery_utils.app, types.ModuleType) is False
    assert celery_utils.app.main == "heron"
    assert patched_attrs is not None


def test_commande_avec_taches_sans_details(inspector):
    inspector.update({"stats": {"w1": {}}, "active": {"w1": [TASK]}})

    output = _run()

    assert "1 tâche(s) en cours" in output
    assert "Détails" not in output
