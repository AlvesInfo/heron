"""Tests des vues de lancement des abonnements (royalties, meuleuses, publicité, prestations)"""

import pytest
from django.urls import reverse

from apps.compta.views import subscriptions_views
from apps.core.models import SSEProgress

pytestmark = pytest.mark.django_db

VIEWS = [
    ("compta:royalties_launch", "ROYALTIES", "Royalties"),
    ("compta:meuleuse_launch", "MEULEUSE", "Meuleuses"),
    ("compta:publicity_launch", "PUBLICITE", "Publicité"),
    ("compta:services_launch", "PRESTATIONS", "Prestations"),
]


@pytest.mark.parametrize(("url_name", "task_type", "label"), VIEWS)
@pytest.mark.usefixtures("subscription_checks")
def test_get_affiche_le_formulaire(logged_client, url_name, task_type, label):
    response = logged_client.get(reverse(url_name))

    assert response.status_code == 200
    assert response.context["display_button"] is True
    assert response.context["button_name"] == url_name.split(":")[1]
    assert label in response.context["titre_table"]


@pytest.mark.parametrize(("url_name", "task_type", "label"), VIEWS)
@pytest.mark.parametrize(
    ("blocker", "message"),
    [
        ("subscription", "Il n'y pas de Maison avec cet abonnement!"),
        ("in_action", "Il y a des générations en cours"),
        ("not_finalize", "déjà envoyée par mail"),
    ],
)
def test_blocages(logged_client, subscription_checks, url_name, task_type, label, blocker, message):
    setattr(subscription_checks, blocker, blocker != "subscription")
    response = logged_client.get(reverse(url_name))

    assert response.status_code == 200
    assert response.context["display_button"] is False
    assert any(message in str(msg) for msg in response.context["messages"])
    assert response.context.get("not_finalize", False) is (blocker == "not_finalize")


@pytest.mark.parametrize(("url_name", "task_type", "label"), VIEWS)
def test_post_famille_manquante(
    logged_client, subscription_checks, month_period, url_name, task_type, label
):
    subscription_checks.missing = "Il manque des familles Cosium : AUDIO"
    response = logged_client.post(reverse(url_name), {"periode": month_period.value})

    assert response.json() == {"success": False, "error": "Il manque des familles Cosium : AUDIO"}


@pytest.mark.parametrize(("url_name", "task_type", "label"), VIEWS)
def test_post_deja_genere(
    logged_client, subscription_checks, month_period, url_name, task_type, label
):
    subscription_checks.have_subs = True
    response = logged_client.post(reverse(url_name), {"periode": month_period.value})

    payload = response.json()
    assert payload["success"] is False
    assert "déjà été généré" in payload["error"]


@pytest.mark.parametrize(("url_name", "task_type", "label"), VIEWS)
@pytest.mark.usefixtures("subscription_checks")
def test_post_lance_la_generation(
    logged_client, month_period, thread_recorder, url_name, task_type, label
):
    started = thread_recorder(subscriptions_views)
    response = logged_client.post(reverse(url_name), {"periode": month_period.value})

    payload = response.json()
    assert payload["success"] is True
    progress = SSEProgress.objects.get(job_id=payload["job_id"])
    assert progress.task_type == task_type
    assert progress.status == "in_progress"
    assert progress.user == logged_client.user
    assert started == [
        (
            subscriptions_views.import_launch_subscriptions,
            (
                task_type,
                month_period.dte_d,
                month_period.dte_f,
                logged_client.user.uuid_identification,
                payload["job_id"],
            ),
            True,
        )
    ]


@pytest.mark.parametrize(("url_name", "task_type", "label"), VIEWS)
@pytest.mark.usefixtures("subscription_checks")
def test_post_formulaire_invalide(logged_client, url_name, task_type, label, caplog):
    with caplog.at_level("ERROR", logger="edi"):
        response = logged_client.post(reverse(url_name), {"periode": "n_importe_quoi"})

    assert response.json() == {"success": False, "error": "Erreur de validation du formulaire"}
    assert "erreur form" in caplog.text
