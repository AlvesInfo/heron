# pylint: disable=E0401,W0621,R0913
"""
FR : Tests des vues des maisons (apps/centers_clients/views/maisons_views.py)
EN : Tests for shops views

created at: 2026-10-10
created by: Paulo ALVES
"""
import json
import logging
import pickle
from pathlib import Path

import pytest
from django.contrib.messages import get_messages
from django.db import IntegrityError, transaction
from django.test import RequestFactory
from django.urls import reverse

from apps.centers_clients.views import maisons_views
from apps.centers_clients.models import Maison
from apps.core.functions.functions_http_response import CONTENT_TYPE_EXCEL
from apps.core.models import ChangesTrace, PicklerFiles
from conftest import patched_attrs

pytestmark = pytest.mark.django_db

LIST_URL = "centers_clients:maisons_list"


def _messages(response):
    return [str(message) for message in get_messages(response.wsgi_request)]


# LISTE / EXPORT / FILTRE ==========================================================================


def test_liste_des_maisons(logged_client, make_maison):
    """La liste est un values() avec les colonnes affichées et le titre"""
    make_maison("AF0002")
    make_maison("AF0001", intitule="Paris")

    response = logged_client.get(reverse(LIST_URL))

    assert response.status_code == 200
    maisons = list(response.context["maisons"])
    assert [row["cct"] for row in maisons] == ["AF0001", "AF0002"]
    assert {"third_party_num", "pays__country_name", "type_x3__name", "cct__active"} <= set(maisons[0])
    assert response.context["titre_table"] == "Clients"
    assert response.context["nb_paging"] == 25


def test_export_liste_des_maisons(logged_client, make_maison):
    """L'export renvoie un xlsx en pièce jointe"""
    make_maison("AF0001")

    response = logged_client.get(reverse("centers_clients:maisons_export_list"))

    assert response.status_code == 200
    assert response["Content-Type"] == CONTENT_TYPE_EXCEL
    assert response["Content-Disposition"].startswith("attachment; filename=LISTING_DES_CLIENTS_")
    assert response.content[:2] == b"PK"


def test_export_liste_des_maisons_en_erreur(logged_client, monkeypatch, caplog):
    """Une erreur de génération est journalisée et redirige vers la liste"""

    def _boom(*_args, **_kwargs):
        raise RuntimeError("xlsx cassé")

    with patched_attrs(monkeypatch, maisons_views, response_file=_boom), caplog.at_level(logging.ERROR, logger="error_views"):
        response = logged_client.get(reverse("centers_clients:maisons_export_list"))

    assert response.status_code == 302
    assert response.url == reverse(LIST_URL)
    assert "view : maisons_export_list" in caplog.text


def test_filtre_api_maisons(logged_client):
    """La vue de filtrage rend son template"""
    response = logged_client.get(reverse("centers_clients:filter_list_maisons_api"))

    assert response.status_code == 200
    assert "centers_clients/maisons_list_to_pick.html" in [t.name for t in response.templates]


def test_acces_anonyme(client):
    """Toutes les vues passent par le LoginMiddleware"""
    response = client.get(reverse(LIST_URL))

    assert response.status_code == 302
    assert response.url == reverse("accounts:login")


# IMPORT B.I =======================================================================================


def test_import_bi_get(logged_client):
    """Le formulaire d'import B.I est affiché"""
    response = logged_client.get(reverse("centers_clients:import_bi"))

    assert response.status_code == 200
    assert response.context["titre_table"] == "Création d'un Client avec import depuis la B.I"
    assert response.context["chevron_retour"] == reverse(LIST_URL)


def test_import_bi_post_invalide(logged_client, caplog):
    """Un formulaire invalide est journalisé et réaffiché"""
    with caplog.at_level(logging.ERROR, logger="error_views"):
        response = logged_client.post(reverse("centers_clients:import_bi"), data={"maison_bi": "ZZ"})

    assert response.status_code == 200
    assert "erreur form" in caplog.text
    assert response.context["form"].errors


def test_import_bi_post_cct_deja_utilise(logged_client, make_maison, make_maison_bi):
    """Un cct déjà rattaché à une maison déclenche un message d'erreur"""
    maison = make_maison("AF0001")
    make_maison_bi("M001")

    response = logged_client.post(
        reverse("centers_clients:import_bi"),
        data={"maison_bi": "M001", "cct": "AF0001", "tiers": maison.third_party_num.third_party_num},
    )

    assert response.status_code == 200
    assert 'Ce "CCT : AF0001, est déjà utilisé!' in _messages(response)
    assert logged_client.session["level"] == 50


def test_import_bi_post_valide(logged_client, picklers_dir, make_maison_bi, make_cct, make_society):
    """Les données B.I sont picklées, enregistrées en PicklerFiles et on redirige vers la création"""
    maison_bi = make_maison_bi("M001", intitule="Maison BI")
    make_cct("AF0001")
    make_society("CLI001")

    response = logged_client.post(
        reverse("centers_clients:import_bi"), data={"maison_bi": "M001", "cct": "AF0001", "tiers": "CLI001"}
    )

    pickler = PicklerFiles.objects.get()
    assert response.status_code == 302
    assert response.url == reverse("centers_clients:maisons_create", kwargs={"initials": str(pickler.uuid_identification)})
    assert (picklers_dir / "import_bi.pick").is_file()

    with open(pickler.pickle_file.path, "rb") as file:
        initials = pickle.load(file)

    assert initials["intitule"] == "Maison BI"
    assert initials["cct"].cct == "AF0001"
    assert initials["third_party_num"].third_party_num == "CLI001"
    assert initials["signature_franchise_date"] == maison_bi.opening_date


# CREATE ===========================================================================================


def test_creation_get_sans_initials(logged_client):
    """L'étoile en paramètre = création vierge"""
    response = logged_client.get(reverse("centers_clients:maisons_create", kwargs={"initials": "*"}))

    assert response.status_code == 200
    assert response.context["create"] is True
    assert response.context["titre_table"] == "Création d'un nouveau Client"
    assert response.context["chevron_retour"] == reverse(LIST_URL)
    assert response.context["form"].initial == {}


@pytest.mark.usefixtures('picklers_dir')
def test_creation_get_initials_inconnu(logged_client):
    """Un uuid de pickler inconnu renvoie 404"""
    response = logged_client.get(
        reverse("centers_clients:maisons_create", kwargs={"initials": "6fa459ea-ee8a-3ca4-894e-db77e160355e"})
    )

    assert response.status_code == 404


@pytest.fixture
def pickled_import(logged_client, picklers_dir, make_maison_bi, make_cct, make_society):
    """Réalise un import B.I et retourne le PicklerFiles créé"""
    make_maison_bi("M001", intitule="Maison BI", intitule_court="MBI")
    make_cct("AF0001")
    make_society("CLI001")
    logged_client.post(
        reverse("centers_clients:import_bi"), data={"maison_bi": "M001", "cct": "AF0001", "tiers": "CLI001"}
    )
    return PicklerFiles.objects.get()


def test_creation_get_depuis_import_bi(logged_client, pickled_import):
    """Le formulaire est pré-rempli avec les données picklées"""
    response = logged_client.get(
        reverse("centers_clients:maisons_create", kwargs={"initials": str(pickled_import.uuid_identification)})
    )

    assert response.status_code == 200
    assert response.context["form"].initial["intitule"] == "Maison BI"
    assert response.context["form"].initial["intitule_court"] == "MBI"


def test_creation_post_valide(logged_client, maison_post_data):
    """Création : utilisateur créateur, centrale ACF, trace de changement, message et redirection"""
    response = logged_client.post(
        reverse("centers_clients:maisons_create", kwargs={"initials": "*"}), data=maison_post_data
    )

    maison = Maison.objects.get()
    assert response.status_code == 302
    assert response.url == reverse(LIST_URL)
    assert maison.created_by == logged_client.user
    assert maison.center_purchase.code == "ACF"
    assert maison.code_maison == "AF0001"
    assert ChangesTrace.objects.filter(model_name="maison", action_type=1).count() == 1
    assert "Le Client AF0001 a été créé avec success" in _messages(response)
    assert logged_client.session["level"] == 20


def test_creation_post_avec_reference_cosium(logged_client, maison_post_data, monkeypatch):
    """Une référence Cosium déclenche la mise à jour des identifiants fournisseur Cosium"""
    received = []

    with patched_attrs(monkeypatch, maisons_views, update_supplier_cct_reference_cosium=received.append):
        response = logged_client.post(
            reverse("centers_clients:maisons_create", kwargs={"initials": "*"}),
            data={**maison_post_data, "reference_cosium": "COS-1"},
        )

    assert response.status_code == 302
    assert received == ["COS-1"]
    assert Maison.objects.get().reference_cosium == "COS-1"


def test_creation_post_depuis_import_bi_nettoie_les_pickles(logged_client, pickled_import, picklers_dir, maison_post_data):
    """À la création, les fichiers pickle et l'enregistrement PicklerFiles sont supprimés"""
    pickle_path = Path(pickled_import.pickle_file.path)

    response = logged_client.post(
        reverse("centers_clients:maisons_create", kwargs={"initials": str(pickled_import.uuid_identification)}),
        data=maison_post_data,
    )

    assert response.status_code == 302
    assert Maison.objects.filter(cct="AF0001").exists()
    assert not pickle_path.exists()
    assert not (picklers_dir / "import_bi.pick").exists()
    assert not PicklerFiles.objects.exists()


def test_creation_post_invalide(logged_client, maison_post_data, caplog):
    """Formulaire invalide : réaffiché, niveau 50, erreur journalisée par le mixin"""
    with caplog.at_level(logging.ERROR, logger="error_views"):
        response = logged_client.post(
            reverse("centers_clients:maisons_create", kwargs={"initials": "*"}),
            data={**maison_post_data, "intitule": ""},
        )

    assert response.status_code == 200
    assert response.context["form"].errors["intitule"]
    assert logged_client.session["level"] == 50
    assert "ChangeTraceMixin error" in caplog.text
    assert not Maison.objects.exists()


def test_creation_post_sans_centrale_acf(logged_client, maison_post_data):
    """Sans centrale ACF, la vue passe la branche DoesNotExist et la sauvegarde échoue"""
    from apps.centers_purchasing.models import ChildCenterPurchase  # pylint: disable=C0415

    ChildCenterPurchase.objects.filter(code="ACF").delete()
    url = reverse("centers_clients:maisons_create", kwargs={"initials": "*"})

    with transaction.atomic(), pytest.raises(IntegrityError):
        logged_client.post(url, data=maison_post_data)


# UPDATE ===========================================================================================


def test_modification_get(logged_client, make_maison, make_address):
    """Contexte : titre, adresse principale Sage du tiers et activité du cct"""
    maison = make_maison("AF0001", intitule="Paris")
    address = make_address(maison.third_party_num, "1", email_01="paris@heron.local")
    make_address(maison.third_party_num, "2")

    response = logged_client.get(reverse("centers_clients:maisons_update", kwargs={"pk": maison.pk}))

    assert response.status_code == 200
    assert response.context["titre_table"] == "Mise à jour du Client : AF0001 - Paris"
    assert response.context["adresse_principale_sage"] == address
    assert response.context["cct__active"] is False
    assert response.context["chevron_retour"] == reverse(LIST_URL)


def test_modification_post_valide(logged_client, make_maison, maison_post_data):
    """Modification : utilisateur modificateur, trace, message"""
    maison = make_maison("AF0001")

    response = logged_client.post(
        reverse("centers_clients:maisons_update", kwargs={"pk": maison.pk}),
        data={**maison_post_data, "intitule": "Nouveau nom"},
    )

    maison.refresh_from_db()
    assert response.status_code == 302
    assert response.url == reverse(LIST_URL)
    assert maison.intitule == "Nouveau nom"
    assert maison.modified_by == logged_client.user
    assert ChangesTrace.objects.filter(model_name="maison", action_type=2).count() == 1
    assert "Le Client AF0001 a été modifiée avec success" in _messages(response)


def test_modification_post_od_ana(logged_client, make_maison, maison_post_data, make_section):
    """En OD ANA l'axe BU saisi est conservé, hors OD ANA il est effacé"""
    maison = make_maison("AF0001")
    axe_bu = make_section("BU", "BU01")
    url = reverse("centers_clients:maisons_update", kwargs={"pk": maison.pk})

    logged_client.post(url, data={**maison_post_data, "type_x3": "2", "axe_bu": str(axe_bu.uuid_identification)})
    maison.refresh_from_db()
    assert maison.axe_bu == axe_bu

    logged_client.post(url, data={**maison_post_data, "type_x3": "0", "axe_bu": str(axe_bu.uuid_identification)})
    maison.refresh_from_db()
    assert maison.axe_bu is None


def test_modification_post_reference_cosium(logged_client, make_maison, maison_post_data, monkeypatch):
    """La référence Cosium déclenche la mise à jour des identifiants fournisseur"""
    maison = make_maison("AF0001")
    received = []

    with patched_attrs(monkeypatch, maisons_views, update_supplier_cct_reference_cosium=received.append):
        logged_client.post(
            reverse("centers_clients:maisons_update", kwargs={"pk": maison.pk}),
            data={**maison_post_data, "reference_cosium": "COS-9"},
        )

    assert received == ["COS-9"]


def test_modification_post_sans_centrale_acf(logged_client, make_maison, maison_post_data, monkeypatch):
    """Sans centrale ACF en base, la centrale existante de la maison est conservée"""
    from apps.centers_purchasing.models import ChildCenterPurchase  # pylint: disable=C0415

    maison = make_maison("AF0001")

    class _NoCenter:
        DoesNotExist = ChildCenterPurchase.DoesNotExist

        class Objects:  # pylint: disable=R0903
            @staticmethod
            def get(**_kwargs):
                raise ChildCenterPurchase.DoesNotExist

        objects = Objects

    with patched_attrs(monkeypatch, maisons_views, ChildCenterPurchase=_NoCenter):
        response = logged_client.post(reverse("centers_clients:maisons_update", kwargs={"pk": maison.pk}), data=maison_post_data)

    maison.refresh_from_db()
    assert response.status_code == 302
    assert maison.center_purchase.code == "ACF"


def test_modification_post_invalide(logged_client, make_maison, maison_post_data):
    """Formulaire invalide en modification"""
    maison = make_maison("AF0001")

    response = logged_client.post(
        reverse("centers_clients:maisons_update", kwargs={"pk": maison.pk}), data={**maison_post_data, "adresse": ""}
    )

    assert response.status_code == 200
    assert response.context["form"].errors["adresse"]


# EMAILS REST API (vue non routée) =================================================================


def _ajax_get(user, query="AF0001"):
    request = RequestFactory().get("/emails/", HTTP_X_REQUESTED_WITH="XMLHttpRequest")
    request.user = user
    return maisons_views.emails_rest_api_query(request, query)


def test_emails_rest_api_query(make_maison, make_user):
    """Renvoie id et cct des maisons en JSON"""
    maison = make_maison("AF0001")

    response = _ajax_get(make_user(), query="X" * 14)

    assert response["Content-Type"] == "application/json"
    assert json.loads(response.content) == {"success": [{"id": maison.pk, "cct": "AF0001"}]}


def test_emails_rest_api_query_trop_de_resultats(make_maison, make_user):
    """Au-delà de 30 maisons, la liste est vide"""
    for index in range(31):
        make_maison(f"AF{index:04d}")

    assert json.loads(_ajax_get(make_user()).content) == {"success": []}


def test_emails_rest_api_query_erreur(make_user, monkeypatch, caplog):
    """Une exception est journalisée et renvoie ko"""

    class _Broken:
        objects = None

    with patched_attrs(monkeypatch, maisons_views, Maison=_Broken), caplog.at_level(logging.ERROR, logger="error_views"):
        response = _ajax_get(make_user())

    assert json.loads(response.content) == {"success": "ko", "message": ""}
    assert "emails_rest_api_query" in caplog.text


def test_emails_rest_api_query_non_ajax(make_user):
    """Sans ajax, redirection vers l'accueil"""
    request = RequestFactory().get("/emails/")
    request.user = make_user()

    response = maisons_views.emails_rest_api_query(request, "AF")

    assert response.status_code == 302
    assert response.url == reverse("home")
