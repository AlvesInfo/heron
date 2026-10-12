"""Tests des vues d'import des factures EDI et de la jauge de test (apps/edi/views)

created at: 2026-10-10
created by: Paulo ALVES
"""

import types

import pytest
from django.urls import reverse

from apps.core.models import SSEProgress
from apps.edi.views import views_imports, views_jauges
from conftest import patched_attrs

CHECKS = (True, False, True, False, [("f", "b", "WIDEX")], True)


@pytest.fixture
def checks(monkeypatch):
    """Remplace les contrôles de la vue : aucune action en cours, facturation finalisée, fichiers"""
    state = {"in_action": False, "not_finalize": False, "checks": CHECKS}

    async def _all_checks():
        return state["checks"]

    with patched_attrs(
        monkeypatch,
        views_imports,
        have_action_in_progress=lambda: state["in_action"],
        have_send_email_without_finalize=lambda: state["not_finalize"],
        get_all_import_checks_async=_all_checks,
    ):
        yield state


@pytest.fixture
def thread_recorder(monkeypatch):
    """Remplace threading.Thread : enregistre la cible et les arguments sans rien lancer"""
    started = []

    class _Thread:
        def __init__(self, target, args, daemon):
            self.target, self.args, self.daemon = target, args, daemon

        def start(self):
            started.append((self.target, self.args, self.daemon))

    # un espace de noms dédié : patcher le module threading casserait async_to_sync
    with patched_attrs(monkeypatch, views_imports, threading=types.SimpleNamespace(Thread=_Thread)):
        yield started


@pytest.mark.usefixtures("checks")
def test_import_edi_invoices_get(logged_client):
    response = logged_client.get(reverse("edi:import_edi_invoices"))

    assert response.status_code == 200
    assert response.context["have_statment"] is True
    assert response.context["have_monthly"] is False
    assert response.context["files_celery"] == [("f", "b", "WIDEX")]
    assert response.context["retours_valid"] is True
    assert response.context["titre_table"] == "Import des factures founisseurs EDI"
    assert "not_finalize" not in response.context


def test_import_edi_invoices_action_en_cours(logged_client, checks):
    checks["in_action"] = True

    response = logged_client.get(reverse("edi:import_edi_invoices"))

    assert response.status_code == 200
    assert "have_statment" not in response.context
    assert [str(message) for message in response.context["messages"]] == [
        "Il y a des intégrations en cours, réessayez plus tard !"
    ]


def test_import_edi_invoices_facturation_non_finalisee(logged_client, checks):
    checks["not_finalize"] = True

    response = logged_client.get(reverse("edi:import_edi_invoices"))

    assert response.status_code == 200
    assert response.context["not_finalize"] is True
    assert "non finalisée" in str(next(iter(response.context["messages"])))


@pytest.mark.parametrize(
    ("post_key", "task_type", "total", "title", "target_name"),
    [
        ("bbgr_statment", "bbgr_import", 2, "Import BBGR Statment", "import_launch_bbgr"),
        ("bbgr_monthly", "bbgr_import", 2, "Import BBGR Monthly", "import_launch_bbgr"),
        ("bbgr_retours", "bbgr_import", 2, "Import BBGR Retours", "import_launch_bbgr"),
        ("bbgr_receptions", "bbgr_import", 2, "Import BBGR Receptions", "import_launch_bbgr"),
        ("edi", "edi_import", 2, "Import des factures EDI", "celery_import_launch"),
    ],
)
@pytest.mark.usefixtures("checks")
def test_import_edi_invoices_post_lance_le_thread(
    logged_client, thread_recorder, post_key, task_type, total, title, target_name
):
    """Chaque bouton crée la jauge adaptée et lance l'import dans un thread démon"""
    response = logged_client.post(reverse("edi:import_edi_invoices"), {post_key: "1"})

    payload = response.json()
    assert payload["success"] is True
    progress = SSEProgress.objects.get(job_id=payload["job_id"])
    assert (progress.task_type, progress.total_items, progress.custom_title) == (
        task_type,
        total,
        title,
    )
    assert progress.status == "in_progress"
    assert progress.user == logged_client.user
    target, args, daemon = thread_recorder[0]
    assert target is getattr(views_imports, target_name)
    assert daemon is True

    if target_name == "import_launch_bbgr":
        assert args == (post_key, logged_client.user.id, payload["job_id"])
    else:
        assert args == (logged_client.user.id, payload["job_id"])


def test_import_edi_invoices_post_sans_fichiers(logged_client, checks, thread_recorder):
    checks["checks"] = (False, False, False, False, [], True)

    response = logged_client.post(reverse("edi:import_edi_invoices"), {"edi": "1"})

    assert response.json() == {
        "success": False,
        "error": "Il n'y a aucuns fichiers EDI à traiter !",
    }
    assert thread_recorder == []
    assert SSEProgress.objects.count() == 0


def test_import_jauge_get(logged_client):
    response = logged_client.get(reverse("edi:import_jauge"))

    assert response.status_code == 200
    assert response.templates[0].name == "edi/edi_jauge_import.html"


def test_import_jauge_post_lance_la_tache(logged_client, monkeypatch):
    delayed = []

    with patched_attrs(
        monkeypatch,
        views_jauges.task_test_import_jauge,
        delay=lambda job_id, user_id: delayed.append((job_id, user_id)),
    ):
        response = logged_client.post(reverse("edi:import_jauge"))

    payload = response.json()
    assert payload["success"] is True
    assert delayed == [(payload["job_id"], logged_client.user.id)]
