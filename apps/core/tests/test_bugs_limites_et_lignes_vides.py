# pylint: disable=E0401,W0621
"""FR : Tests de preuve des corrections : paramètre limit des API JSON, tri des jobs actifs,


     lignes vides ou courtes dans l'itérateur d'import de fichiers
EN : Proof tests for fixes: JSON APIs limit parameter, active jobs ordering, empty or short
     lines in the file import iterator

created at: 2026-10-11
created by: Paulo ALVES
"""

import csv
import datetime
import io

import pytest
from django.test import RequestFactory
from django.urls import reverse
from django.utils import timezone

from apps.core.bin.notifications import create_notification
from apps.core.functions.function_imports import IterFileToInsert
from apps.core.functions.functions_http import get_limit
from apps.core.models import SSEProgress

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    ("value", "expected"),
    [(None, 50), ("3", 3), ("abc", 50), ("", 50), ("0", 50), ("-4", 50), ("2.5", 50)],
)
def test_get_limit(value, expected):
    """Le paramètre limit n'est pris que s'il est un entier strictement positif"""
    data = {} if value is None else {"limit": value}

    assert get_limit(RequestFactory().get("/", data)) == expected


def test_get_limit_defaut_personnalise():
    assert get_limit(RequestFactory().get("/"), default=10) == 10
    assert get_limit(RequestFactory().get("/", {"limit": "x"}), default=10) == 10


def test_limite_non_numerique_sur_les_api_json(logged_client):
    """Un limit invalide ne provoque plus d'erreur 500 : la valeur par défaut est appliquée"""
    user = logged_client.user
    create_notification(user, "Une", "x")
    SSEProgress.objects.create(job_id="job", user=user, task_type="import")

    notifications = logged_client.get(reverse("core:notifications_list"), {"limit": "beaucoup"})
    jobs = logged_client.get(reverse("core:list_jobs"), {"limit": "-1"})

    assert notifications.status_code == 200
    assert len(notifications.json()["notifications"]) == 1
    assert jobs.status_code == 200
    assert jobs.json()["count"] == 1


def test_jobs_actifs_en_cours_avant_en_attente(logged_client):
    """Les jobs en cours, du démarrage le plus récent au plus ancien, puis les jobs en attente"""
    user = logged_client.user
    now = timezone.now()
    SSEProgress.objects.create(
        job_id="old",
        user=user,
        task_type="import",
        status="in_progress",
        started_at=now - datetime.timedelta(hours=1),
    )
    SSEProgress.objects.create(job_id="wait", user=user, task_type="import", status="pending")
    SSEProgress.objects.create(
        job_id="new", user=user, task_type="import", status="in_progress", started_at=now
    )
    SSEProgress.objects.create(
        job_id="done", user=user, task_type="import", status="completed", started_at=now
    )

    response = logged_client.get(reverse("core:active_jobs"))

    assert [job["job_id"] for job in response.json()["jobs"]] == ["new", "old", "wait"]


def _csv(path, rows):
    with path.open("w", encoding="utf8", newline="") as file:
        csv.writer(file, delimiter=";", quotechar='"', lineterminator="\n").writerows(rows)

    return path


def test_iter_lignes_vides_et_courtes_completees(tmp_path):
    """all_lines : une ligne vide donne des champs vides ; une ligne courte est complétée"""
    source = _csv(tmp_path / "fichier.csv", [["code", "name"], ["ACF", "Acuitis"], [], ["GAF"]])
    params = {"exclude_rows_dict": {2: "rien"}}

    with IterFileToInsert(
        source, {"code": None, "name": None}, first_line=2, params_dict=params
    ) as file_iter:
        rows = list(file_iter.chunk_dict(all_lines=True))

    assert rows == [
        {"code": "ACF", "name": "Acuitis"},
        {"code": "", "name": ""},
        {"code": "GAF", "name": ""},
    ]

    with IterFileToInsert(
        source, {"code": None, "name": None}, first_line=2, params_dict=params
    ) as file_iter:
        assert list(file_iter.chunk_dict()) == [
            {"code": "ACF", "name": "Acuitis"},
            {"code": "GAF", "name": ""},
        ]

    buffer = io.StringIO()

    with IterFileToInsert(source, {"name": None, "code": None}, first_line=2) as file_iter:
        file_iter.write_io(buffer, all_lines=True)

    assert buffer.getvalue() == '"ACF";"Acuitis"\r\n"";""\r\n"GAF";""\r\n'


def test_iter_exclusion_sur_une_colonne_absente(tmp_path):
    """Une exclusion sur une colonne au-delà de la ligne ne lève plus d'IndexError"""
    source = _csv(tmp_path / "fichier.csv", [["ACF"], ["GAF"]])

    with IterFileToInsert(
        source, {"code": None}, first_line=1, params_dict={"exclude_rows_dict": {3: "x"}}
    ) as file_iter:
        assert [row["code"] for row in file_iter.chunk_dict()] == ["ACF", "GAF"]
