# pylint: disable=E0401,W0621
"""
FR : Tests des vues des Tiers X3 (apps/book/views/book_views.py)
EN : Tests for third parties views

created at: 2026-10-11
created by: Paulo ALVES
"""
import logging

import pytest
from django.contrib.messages import get_messages
from django.urls import reverse

from apps.book.views import book_views
from apps.core.bin.encoders import get_base_64
from apps.core.models import ChangesTrace
from conftest import patched_attrs

pytestmark = pytest.mark.django_db


def _form_data(response, **overrides):
    """Données POST reconstruites depuis le formulaire affiché (valeurs initiales du tiers)"""
    form = response.context["form"]
    data = {}

    for name in form.fields:
        value = form[name].value()

        if value is None:
            value = ""
        elif isinstance(value, bool):
            value = "True" if value else "False"

        data[name] = value

    data.update(overrides)
    return data


@pytest.fixture
def societies(make_society, make_society_bank):
    four = make_society("FOUR001", name="Fournisseur", is_client=False, is_supplier=True, in_use=True)
    make_society_bank(four, "FR01")
    default_bank = make_society_bank(four, "FR02", is_default=True)
    make_society("CLI001", name="Client", is_client=True, in_use=True)
    make_society("OLD001", name="Ancien", is_client=True, in_use=False)
    make_society("DIV001", name="Divers", is_client=False, is_supplier=False, in_use=True)
    return {"four": four, "default_bank": default_bank}


# LISTES ===========================================================================================


def test_liste_de_tous_les_tiers(logged_client, societies):
    response = logged_client.get(reverse("book:societies_list"))

    assert response.status_code == 200
    assert response.context["in_use"] == "alls"
    assert [row["third_party_num"] for row in response.context["societies"]] == ["CLI001", "DIV001", "FOUR001", "OLD001"]
    assert "Fournisseur" in response.content.decode()


def test_liste_des_tiers_utilises(logged_client, societies):
    """Clients ou fournisseurs marqués utilisés : ni l'ancien client, ni le tiers divers"""
    response = logged_client.get(reverse("book:societies_list_in_use"))

    assert response.status_code == 200
    assert response.context["in_use"] == "in_use"
    assert response.context["nb_paging"] == 100
    assert [row["third_party_num"] for row in response.context["societies"]] == ["CLI001", "FOUR001"]


# FICHE TIERS ======================================================================================


@pytest.mark.parametrize(("in_use", "back_name"), [("alls", "societies_list"), ("in_use", "societies_list_in_use")])
def test_fiche_tiers_get(logged_client, societies, in_use, back_name):
    """Le chevron de retour et l'url de retour des identifiants dépendent de la liste d'origine"""
    four = societies["four"]
    url = reverse("book:society_update", args=[four.pk, in_use])

    response = logged_client.get(url)

    assert response.status_code == 200
    assert response.context["chevron_retour"] == reverse(f"book:{back_name}")
    assert response.context["titre_table"] == "Mise à jour du Tiers : FOUR001 - Fournisseur"
    assert response.context["compte_banque"] == societies["default_bank"]
    assert response.context["third_party_num"] == "FOUR001"
    assert response.context["pk"] == four.pk
    assert get_base_64(response.context["url_retour_supplier_cct"]) == [url]


def test_fiche_tiers_inconnu(logged_client):
    assert logged_client.get(reverse("book:society_update", args=[999999, "alls"])).status_code == 404


@pytest.mark.parametrize(("in_use", "back_name"), [("alls", "societies_list"), ("in_use", "societies_list_in_use")])
def test_fiche_tiers_post_modification(logged_client, societies, in_use, back_name):
    """La modification est tracée, l'utilisateur enregistré, retour à la liste d'origine"""
    four = societies["four"]
    url = reverse("book:society_update", args=[four.pk, in_use])
    data = _form_data(logged_client.get(url), name="Fournisseur renommé", in_use="True", centers_suppliers_indentifier="B|A")

    response = logged_client.post(url, data)

    four.refresh_from_db()
    assert response.status_code == 302
    assert response.url == reverse(f"book:{back_name}")
    assert four.name == "Fournisseur renommé"
    assert four.centers_suppliers_indentifier == "A|B"
    assert four.modified_by == logged_client.user
    assert four.in_use is True
    assert logged_client.session["level"] == 20
    trace = ChangesTrace.objects.get()
    assert trace.model_name == "society"
    assert trace.difference["avant"]["name"] == "Fournisseur"
    assert trace.difference["après"]["name"] == "Fournisseur renommé"
    assert "a été modifiée avec success" in next(iter(get_messages(response.wsgi_request))).message


def test_fiche_tiers_post_sans_modification(logged_client, societies):
    four = societies["four"]
    url = reverse("book:society_update", args=[four.pk, "alls"])

    response = logged_client.post(url, _form_data(logged_client.get(url)))

    assert response.status_code == 302
    assert ChangesTrace.objects.count() == 0


def test_fiche_tiers_post_identifiant_en_doublon(logged_client, societies, make_society, caplog):
    """Un identifiant centrale déjà porté par un autre tiers est refusé"""
    make_society("AUTRE01", centers_suppliers_indentifier="DEJA")
    four = societies["four"]
    url = reverse("book:society_update", args=[four.pk, "alls"])

    with caplog.at_level(logging.ERROR, logger="views"):
        response = logged_client.post(url, _form_data(logged_client.get(url), centers_suppliers_indentifier="DEJA"))

    four.refresh_from_db()
    assert response.status_code == 200
    assert "existe dèjà pour le Tiers : AUTRE01" in response.context["form"].errors["__all__"][0]
    assert four.centers_suppliers_indentifier is None
    assert logged_client.session["level"] == 50
    assert "ChangeTraceMixin error" in caplog.text


# EXPORTS ==========================================================================================


@pytest.mark.parametrize(
    ("export", "file_name"),
    [
        ("export_list_societies", "LISTING_DES_TIERS.xlsx"),
        ("export_list_clients", "LISTING_DES_CLIENTS.xlsx"),
        ("export_list_suppliers", "LISTING_DES_FOURNISSEURS.xlsx"),
    ],
)
def test_export_des_listes_pregenerees(logged_client, settings, tmp_path, export, file_name):
    """Hors debug, le fichier pré-généré est servi par nginx (X-Accel-Redirect)"""
    settings.MEDIA_EXCEL_FILES_DIR = tmp_path
    settings.DEBUG = False

    response = logged_client.get(reverse("book:excel_outputs", args=[export]))

    assert response.status_code == 200
    assert response["X-Accel-Redirect"] == f"/excel_media/{file_name}"
    assert response["Content-Disposition"] == f'attachment; filename="{file_name}"'


def test_export_inconnu(logged_client):
    assert logged_client.get(reverse("book:excel_outputs", args=["export_inconnu"])).status_code == 404


# EMAILS EN ERREUR =================================================================================


def test_liste_des_emails_en_erreur(logged_client, make_society):
    make_society("TIERS01", email_01="faux", email_02="bon@acuitis.com")

    response = logged_client.get(reverse("book:emails_errors_list"))

    assert response.status_code == 200
    content = response.content.decode()
    assert response.context["titre_table"] == "Erreurs emails Tiers X3"
    assert "TIERS01" in content
    assert "faux" in content
    assert "bon@acuitis.com" not in content


def test_export_excel_des_emails_en_erreur(logged_client, make_society):
    make_society("TIERS01", email_01="faux")

    response = logged_client.get(reverse("book:excel_errors_emails_outputs"))

    assert response.status_code == 200
    assert response["Content-Disposition"].startswith("attachment; filename=LISTING_DES_EMAILS_EN_ERREUR_")
    assert response.content[:2] == b"PK"


def test_export_excel_des_emails_en_erreur_echoue(logged_client, monkeypatch, caplog):
    """L'erreur de génération est journalisée et l'utilisateur revient sur la liste"""

    def _boom(*_args, **_kwargs):
        raise RuntimeError("excel cassé")

    with patched_attrs(monkeypatch, book_views, excel_errors_emails=_boom), caplog.at_level(logging.ERROR, logger="export_excel"):
        response = logged_client.get(reverse("book:excel_errors_emails_outputs"))

    assert response.status_code == 302
    assert response.url == reverse("book:emails_errors_list")
    assert "view excel_errors_emails_outputs" in caplog.text
    assert "excel cassé" in caplog.text
