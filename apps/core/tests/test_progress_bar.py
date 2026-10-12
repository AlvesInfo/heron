"""Tests de la mise à jour de progression SSE en transaction séparée (apps.core.utils.progress_bar)"""
import logging
import uuid

import pytest

from apps.core.models import SSEProgress
from apps.core.utils.progress_bar import update_progress_threaded

pytestmark = pytest.mark.django_db


@pytest.fixture
def progress(make_user):
    return SSEProgress.objects.create(job_id=str(uuid.uuid4()), user=make_user(), task_type="test", total_items=2)


def test_update_progress(progress):
    update_progress_threaded(progress.job_id, processed=1, message="un")

    progress.refresh_from_db()
    assert progress.processed_items == 1
    assert progress.current_message == "un"


def test_mark_as_completed(progress):
    update_progress_threaded(progress.job_id, mark_as_completed=True)

    progress.refresh_from_db()
    assert progress.status == "completed"


def test_mark_as_failed(progress):
    update_progress_threaded(progress.job_id, mark_as_failed=True)

    progress.refresh_from_db()
    assert progress.status == "failed"
    assert "consulter les logs" in progress.error_message


def test_arguments_invalides_journalises(progress, caplog):
    with caplog.at_level(logging.ERROR, logger="django"):
        update_progress_threaded(progress.job_id, inconnu=1)

    assert "arguments invalides" in caplog.text


def test_job_inconnu():
    with pytest.raises(SSEProgress.DoesNotExist):
        update_progress_threaded("absent")
