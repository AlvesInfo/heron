# pylint: disable=E0401,W0621
"""FR : Tests du suivi de progression : modèle SSEProgress, vues JSON et traqueur d'événements SSE


EN : Tests for progress tracking: SSEProgress model, JSON views and SSE events tracker

created at: 2026-10-11
created by: Paulo ALVES
"""

import datetime
import logging

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.core.bin import sse_progress
from apps.core.bin.sse_progress import SSEProgressTracker, SSETracker
from apps.core.models import SSEProgress
from conftest import patched_attrs

pytestmark = pytest.mark.django_db


@pytest.fixture
def make_progress(make_user):
    """Fabrique de progressions SSE pour un utilisateur"""
    user = make_user()

    def _factory(job_id: str = "job-1", owner=None, **kwargs):
        defaults = {"task_type": "email_sending", "total_items": 10}
        defaults.update(kwargs)
        return SSEProgress.objects.create(job_id=job_id, user=owner or user, **defaults)

    _factory.user = user
    return _factory


# MODÈLE ===========================================================================================


def test_progress_str_et_pourcentages(make_progress):
    progress = make_progress(total_items=0)

    assert str(progress) == "email_sending - job-1 - pending (0/0)"
    assert (progress.progress_percentage, progress.success_rate, progress.success_count) == (
        0,
        0,
        0,
    )

    progress.total_items = 10
    progress.processed_items = 4
    progress.failed_items = 1

    assert (progress.progress_percentage, progress.success_count, progress.success_rate) == (
        40,
        3,
        75,
    )


def test_progress_duree_et_estimations(make_progress):
    """Sans démarrage : durée 0 et aucune estimation ; en cours : estimation sur la moyenne"""
    progress = make_progress(processed_items=4)

    assert progress.duration == 0
    assert progress.estimated_remaining_time is None
    assert progress.items_per_second == 0

    progress.started_at = timezone.now() - datetime.timedelta(seconds=8)
    progress.completed_at = progress.started_at + datetime.timedelta(seconds=8)

    assert progress.duration == 8
    assert progress.estimated_remaining_time == 12
    assert progress.items_per_second == 0.5

    progress.processed_items = 10
    assert progress.estimated_remaining_time == 0

    progress.processed_items = 0
    assert progress.estimated_remaining_time is None
    assert progress.items_per_second == 0

    progress.completed_at = None
    progress.processed_items = 2
    assert progress.duration >= 8


def test_progress_cycle_de_vie(make_progress):
    progress = make_progress()

    progress.mark_as_started()
    assert (progress.status, progress.started_at is not None) == ("in_progress", True)

    progress.mark_as_completed()
    assert (progress.status, progress.completed_at is not None) == ("completed", True)

    failed = make_progress("job-2")
    failed.mark_as_failed()
    assert (failed.status, failed.error_message) == ("failed", None)

    failed.mark_as_failed("plantage")
    assert SSEProgress.objects.get(pk=failed.pk).error_message == "plantage"


def test_progress_update_progress(make_progress):
    """Compteurs cumulés, message courant et listes de succès / erreurs dans les métadonnées"""
    progress = make_progress()

    progress.update_progress(processed=2)
    progress.update_progress(processed=1, message="fichier 3")
    progress.update_progress(processed=1, item_name="ok.pdf")
    progress.update_progress(processed=1, failed=1, message="illisible", item_name="ko.pdf")
    progress.update_progress(failed=1, item_name="sans message")

    progress.refresh_from_db()
    assert (progress.processed_items, progress.failed_items, progress.current_message) == (
        5,
        2,
        "illisible",
    )
    assert progress.metadata == {
        "success": ["ok.pdf"],
        "failed": [
            {"name": "ko.pdf", "error": "illisible"},
            {"name": "sans message", "error": "Erreur inconnue"},
        ],
    }


def test_progress_update_progress_complete_des_metadonnees_partielles(make_progress):
    """Des métadonnées sans la liste attendue sont complétées"""
    success_only = make_progress("job-s", metadata={"success": []})
    failed_only = make_progress("job-f", metadata={"failed": []})

    success_only.update_progress(failed=1, item_name="ko.pdf")
    failed_only.update_progress(processed=1, item_name="ok.pdf")

    assert success_only.metadata == {
        "success": [],
        "failed": [{"name": "ko.pdf", "error": "Erreur inconnue"}],
    }
    assert failed_only.metadata == {"failed": [], "success": ["ok.pdf"]}


def test_progress_to_dict(make_progress):
    progress = make_progress(
        custom_title="Envoi", completion_message="Fini", processed_items=5, failed_items=1
    )
    progress.mark_as_started()

    payload = progress.to_dict()

    assert payload["job_id"] == "job-1"
    assert payload["status_display"] == "En cours"
    assert (payload["processed_items"], payload["failed_items"], payload["success_count"]) == (
        5,
        1,
        4,
    )
    assert (payload["progress_percentage"], payload["success_rate"]) == (50, 80)
    assert (payload["custom_title"], payload["completion_message"], payload["metadata"]) == (
        "Envoi",
        "Fini",
        None,
    )
    assert payload["started_at"] == progress.started_at.isoformat()
    assert payload["completed_at"] is None
    assert payload["duration"] >= 0


# VUES =============================================================================================


def test_vues_sse_exigent_une_authentification(client):
    assert client.get(reverse("core:list_jobs")).status_code == 302


def test_detail_d_un_job(logged_client, make_user):
    SSEProgress.objects.create(
        job_id="mine", user=logged_client.user, task_type="import", total_items=3
    )
    SSEProgress.objects.create(
        job_id="theirs",
        user=make_user(email="autre@heron.local", username="autre"),
        task_type="import",
    )

    response = logged_client.get(reverse("core:job_detail", args=["mine"]))
    forbidden = logged_client.get(reverse("core:job_detail", args=["theirs"]))

    assert response.status_code == 200
    assert response.json()["job_id"] == "mine"
    assert forbidden.status_code == 404
    assert forbidden.json() == {"error": "Job theirs non trouvé"}


def test_liste_des_jobs_de_l_utilisateur(logged_client, make_user):
    user = logged_client.user
    SSEProgress.objects.create(job_id="a", user=user, task_type="import", status="completed")
    SSEProgress.objects.create(job_id="b", user=user, task_type="export", status="pending")
    SSEProgress.objects.create(job_id="c", user=user, task_type="import", status="pending")
    SSEProgress.objects.create(
        job_id="d", user=make_user(email="autre@heron.local", username="autre"), task_type="import"
    )

    everything = logged_client.get(reverse("core:list_jobs"))
    imports = logged_client.get(reverse("core:list_jobs"), {"task_type": "import"})
    pending = logged_client.get(reverse("core:list_jobs"), {"status": "pending", "limit": 1})

    assert everything.json()["count"] == 3
    assert {job["job_id"] for job in imports.json()["jobs"]} == {"a", "c"}
    assert pending.json()["count"] == 1


def test_jobs_actifs(logged_client):
    user = logged_client.user
    SSEProgress.objects.create(job_id="done", user=user, task_type="import", status="completed")
    running = SSEProgress.objects.create(
        job_id="run", user=user, task_type="import", status="in_progress", started_at=timezone.now()
    )
    waiting = SSEProgress.objects.create(
        job_id="wait", user=user, task_type="import", status="pending"
    )

    response = logged_client.get(reverse("core:active_jobs"))

    assert response.json()["count"] == 2
    # jobs en cours (démarrage le plus récent d'abord) puis jobs en attente (sans date de démarrage)
    assert [job["job_id"] for job in response.json()["jobs"]] == [running.job_id, waiting.job_id]


def test_suppression_d_un_job(logged_client):
    user = logged_client.user
    SSEProgress.objects.create(job_id="done", user=user, task_type="import", status="completed")
    SSEProgress.objects.create(job_id="run", user=user, task_type="import", status="in_progress")

    deleted = logged_client.delete(reverse("core:delete_job", args=["done"]))
    refused = logged_client.delete(reverse("core:delete_job", args=["run"]))
    unknown = logged_client.delete(reverse("core:delete_job", args=["absent"]))

    assert deleted.json() == {"success": True, "message": "Job done supprimé"}
    assert not SSEProgress.objects.filter(job_id="done").exists()
    assert refused.status_code == 400
    assert refused.json() == {"error": "Impossible de supprimer un job en cours"}
    assert unknown.status_code == 404
    assert logged_client.post(reverse("core:delete_job", args=["run"])).status_code == 405


# TRAQUEUR SSE =====================================================================================


@pytest.fixture
def sent(monkeypatch):
    """Enregistre les événements envoyés à django_eventstream"""
    events = []
    monkeypatch.setattr(
        sse_progress.django_eventstream,
        "send_event",
        lambda channel, kind, data: events.append((channel, kind, data)),
    )
    return events


def test_tracker_envoie_les_evenements(sent):
    tracker = SSEProgressTracker("job-1")

    tracker.send_start(total=4, title="Envoi")
    tracker.send_progress(current=1, total=4, message="un")
    tracker.send_progress(current=0, total=0)
    tracker.send_complete(total=4)
    tracker.send_complete(total=4, message="Tout est parti")
    tracker.send_error("plantage")
    tracker.send_warning("attention")
    tracker.send_custom("info", {"a": 1})

    assert tracker.channel_name == "progress-job-1"
    assert SSETracker is SSEProgressTracker
    assert [kind for _, kind, _ in sent] == [
        "start",
        "progress",
        "progress",
        "complete",
        "complete",
        "error",
        "warning",
        "info",
    ]
    assert all(channel == "progress-job-1" for channel, _, _ in sent)
    assert sent[0][2] == {
        "status": "started",
        "total": 4,
        "current": 0,
        "percentage": 0,
        "title": "Envoi",
    }
    assert sent[1][2] == {
        "status": "in_progress",
        "current": 1,
        "total": 4,
        "percentage": 25,
        "remaining": 3,
        "message": "un",
    }
    assert sent[2][2]["percentage"] == 0
    assert sent[3][2]["message"] == "Terminé avec succès"
    assert sent[4][2]["message"] == "Tout est parti"
    assert sent[5][2] == {"status": "error", "error": "plantage", "message": "Erreur: plantage"}
    assert sent[6][2] == {
        "status": "warning",
        "warning": "attention",
        "message": "Attention: attention",
    }
    assert sent[7][2] == {"a": 1}


def test_tracker_desactive_n_envoie_rien(sent):
    SSEProgressTracker("job-1", enabled=False).send_start(total=1)

    assert sent == []


def test_tracker_erreur_d_envoi_journalisee(monkeypatch, caplog):
    def _boom(*_args):
        raise RuntimeError("canal fermé")

    monkeypatch.setattr(sse_progress.django_eventstream, "send_event", _boom)

    with caplog.at_level(logging.ERROR, logger="invoices_flux"):
        SSEProgressTracker("job-1").send_start(total=1)

    assert "canal fermé" in caplog.text


def test_tracker_sans_django_eventstream(monkeypatch, caplog, sent):
    """Sans la bibliothèque, un avertissement est journalisé et rien n'est envoyé"""
    with (
        patched_attrs(monkeypatch, sse_progress, SSE_AVAILABLE=False),
        caplog.at_level(logging.WARNING, logger="invoices_flux"),
    ):
        tracker = SSEProgressTracker("job-1")
        tracker.send_start(total=1)
        silent = SSEProgressTracker("job-2", enabled=False)

    assert tracker.enabled is False
    assert silent.enabled is False
    assert "django-eventstream n'est pas installé" in caplog.text
    assert sent == []


def test_module_sans_django_eventstream_installe(monkeypatch):
    """Si l'import de django_eventstream échoue, le module se charge avec SSE_AVAILABLE à False"""
    import importlib  # pylint: disable=C0415
    import sys  # pylint: disable=C0415

    try:
        monkeypatch.setitem(sys.modules, "django_eventstream", None)
        reloaded = importlib.reload(sse_progress)
        assert reloaded.SSE_AVAILABLE is False
    finally:
        monkeypatch.undo()
        importlib.reload(sse_progress)

    assert sse_progress.SSE_AVAILABLE is True
