# pylint: disable=E0401,W0621
"""FR : Tests des vues des centrales mères, centrales filles et enseignes


EN : Tests for principal centers, child centers and signboards views

created at: 2026-10-11
created by: Paulo ALVES
"""

import logging

import pytest
from django.contrib.messages import get_messages
from django.urls import reverse

from apps.centers_purchasing.models import ChildCenterPurchase, PrincipalCenterPurchase, Signboard
from apps.centers_purchasing.views import enseignes_views, filles_views, meres_views
from apps.core.models import ChangesTrace
from conftest import patched_attrs

pytestmark = pytest.mark.django_db


def _messages(response):
    return [message.message for message in get_messages(response.wsgi_request)]


# CENTRALES MÈRES ==================================================================================


def test_liste_des_centrales_meres(logged_client, make_principal_center):
    make_principal_center("HA", name="Héron Achats")

    response = logged_client.get(reverse("centers_purchasing:meres_list"))

    assert response.status_code == 200
    assert response.context["titre_table"] == "Centrales Mères"
    assert [mere.code for mere in response.context["meres"]] == ["HA"]


def test_creation_centrale_mere(logged_client):
    get = logged_client.get(reverse("centers_purchasing:mere_create"))
    response = logged_client.post(
        reverse("centers_purchasing:mere_create"),
        {"code": "HA", "name": "Héron Achats", "generic_coefficient": "1"},
    )

    mere = PrincipalCenterPurchase.objects.get(code="HA")
    assert get.status_code == 200
    assert get.context["create"] is True
    assert get.context["chevron_retour"] == reverse("centers_purchasing:meres_list")
    assert get.context["titre_table"] == "Création d'une nouvelle Centrale Mère"
    assert response.status_code == 302
    assert response.url == reverse("centers_purchasing:meres_list")
    assert mere.created_by == logged_client.user
    assert logged_client.session["level"] == 20
    assert "HA a été créé avec success" in _messages(response)[0]
    assert ChangesTrace.objects.count() == 1


def test_creation_centrale_mere_invalide(logged_client, caplog):
    with caplog.at_level(logging.ERROR, logger="views"):
        response = logged_client.post(
            reverse("centers_purchasing:mere_create"), {"code": "", "name": ""}
        )

    assert response.status_code == 200
    assert logged_client.session["level"] == 50
    assert PrincipalCenterPurchase.objects.count() == 0
    assert "ChangeTraceMixin error" in caplog.text


def test_modification_centrale_mere(logged_client, make_principal_center):
    mere = make_principal_center("HA", name="Héron Achats")
    url = reverse("centers_purchasing:mere_update", args=[mere.pk])

    get = logged_client.get(url)
    response = logged_client.post(
        url, {"code": "HA", "name": "Héron Achats SAS", "generic_coefficient": "1.5"}
    )

    mere.refresh_from_db()
    assert get.context["titre_table"] == "Mise à jour de la Centrale Mère : HA - Héron Achats"
    assert get.context["chevron_retour"] == reverse("centers_purchasing:meres_list")
    assert response.status_code == 302
    assert (mere.name, str(mere.generic_coefficient), mere.modified_by) == (
        "Héron Achats SAS",
        "1.50000",
        logged_client.user,
    )
    assert "a été modifiée avec success" in _messages(response)[0]


def test_export_centrales_meres(logged_client, make_principal_center, monkeypatch, caplog):
    make_principal_center("HA")

    response = logged_client.get(reverse("centers_purchasing:meres_export_list"))
    post = logged_client.post(reverse("centers_purchasing:meres_export_list"))

    assert response.status_code == 200
    assert response["Content-Disposition"].startswith(
        "attachment; filename=LISTING_DES_CENTRALES_MERES_"
    )
    assert response.content[:2] == b"PK"
    assert post.status_code == 302
    assert post.url == reverse("centers_purchasing:meres_list")

    def _boom(*_args, **_kwargs):
        raise RuntimeError("excel cassé")

    with (
        patched_attrs(monkeypatch, meres_views, excel_meres_list=_boom),
        caplog.at_level(logging.ERROR, logger="views"),
    ):
        error = logged_client.get(reverse("centers_purchasing:meres_export_list"))

    assert error.status_code == 302
    assert "meres_export_list" in caplog.text


# CENTRALES FILLES =================================================================================


def _fille_data(**overrides):
    data = {
        "code": "ACF",
        "base_center": "HA",
        "name": "Acuitis",
        "generic_coefficient": "1",
        "societe_cpy_x3": "ACU",
        "site_fcy_x3": "ACF",
        "code_plan_sage": "FRA",
        "iban": "FR7630006000",
    }
    data.update(overrides)
    return data


def test_liste_des_centrales_filles(logged_client, make_child_center):
    make_child_center("ACF", name="Acuitis")

    response = logged_client.get(reverse("centers_purchasing:filles_list"))

    assert response.status_code == 200
    assert response.context["titre_table"] == "Centrales Filles"
    assert [fille.code for fille in response.context["filles"]] == ["ACF"]


def test_creation_centrale_fille(logged_client, make_principal_center):
    make_principal_center("HA")

    get = logged_client.get(reverse("centers_purchasing:fille_create"))
    response = logged_client.post(reverse("centers_purchasing:fille_create"), _fille_data())

    fille = ChildCenterPurchase.objects.get(code="ACF")
    assert get.context["create"] is True
    assert get.context["titre_table"] == "Création d'une nouvelle Centrale Fille"
    assert response.status_code == 302
    assert response.url == reverse("centers_purchasing:filles_list")
    assert (fille.base_center.code, fille.iban, fille.created_by) == (
        "HA",
        "FR76 3000 6000",
        logged_client.user,
    )
    assert "ACF a été créé avec success" in _messages(response)[0]


def test_creation_centrale_fille_invalide(logged_client, make_principal_center):
    make_principal_center("HA")

    response = logged_client.post(reverse("centers_purchasing:fille_create"), _fille_data(name=""))

    assert response.status_code == 200
    assert "name" in response.context["form"].errors
    assert ChildCenterPurchase.objects.count() == 0


def test_modification_centrale_fille(logged_client, make_child_center, make_principal_center):
    fille = make_child_center("ACF", name="Acuitis", base_center=make_principal_center("HA"))
    url = reverse("centers_purchasing:fille_update", args=[fille.pk])

    get = logged_client.get(url)
    response = logged_client.post(
        url, _fille_data(name="Acuitis renommée", legal_notice="<p>Mentions</p>")
    )

    fille.refresh_from_db()
    assert get.context["titre_table"] == "Mise à jour de la Centrale Fille : ACF - Acuitis"
    assert response.status_code == 302
    assert (fille.name, fille.legal_notice, fille.modified_by) == (
        "Acuitis renommée",
        "<p>Mentions</p>",
        logged_client.user,
    )
    assert "a été modifiée avec success" in _messages(response)[0]


def test_export_centrales_filles(logged_client, make_child_center, monkeypatch, caplog):
    make_child_center("ACF")

    response = logged_client.get(reverse("centers_purchasing:filles_export_list"))
    post = logged_client.post(reverse("centers_purchasing:filles_export_list"))

    assert response.status_code == 200
    assert response["Content-Disposition"].startswith(
        "attachment; filename=LISTING_DES_CENTRALES_FILLES_"
    )
    assert post.url == reverse("centers_purchasing:filles_list")

    def _boom(*_args, **_kwargs):
        raise RuntimeError("excel cassé")

    with (
        patched_attrs(monkeypatch, filles_views, excel_filles_list=_boom),
        caplog.at_level(logging.ERROR, logger="views"),
    ):
        error = logged_client.get(reverse("centers_purchasing:filles_export_list"))

    assert error.status_code == 302
    assert "filles_export_list" in caplog.text


# ENSEIGNES ========================================================================================


def _enseigne_data(**overrides):
    data = {
        "child_center": "ACF",
        "code": "ACF",
        "name": "Acuitis",
        "generic_coefficient": "1",
        "comment": "",
        "message": "<p>Merci</p>",
    }
    data.update(overrides)
    return data


def test_liste_des_enseignes(logged_client, make_signboard):
    make_signboard("ACF", name="Acuitis")

    response = logged_client.get(reverse("centers_purchasing:enseignes_list"))

    assert response.status_code == 200
    assert response.context["nb_paging"] == 7
    assert [enseigne.code for enseigne in response.context["enseignes"]] == ["ACF"]


def test_creation_enseigne_avec_logo(logged_client, media_dirs, make_child_center, logo_file):
    """Le logo est enregistré dans media/logos et copié dans les répertoires static"""
    make_child_center("ACF")

    get = logged_client.get(reverse("centers_purchasing:enseigne_create"))
    response = logged_client.post(
        reverse("centers_purchasing:enseigne_create"), _enseigne_data(logo=logo_file("acuitis.png"))
    )

    enseigne = Signboard.objects.get(code="ACF")
    assert get.context["create"] is True
    assert get.context["titre_table"] == "Création d'une nouvelle Enseigne"
    assert response.status_code == 302
    assert response.url == reverse("centers_purchasing:enseignes_list")
    assert enseigne.logo.name == "logos/acuitis.png"
    assert (media_dirs.logos / "acuitis.png").exists()
    assert (media_dirs.static / "img" / "acuitis.png").exists()
    assert (media_dirs.static / "images" / "acuitis.png").exists()
    assert enseigne.created_by == logged_client.user
    assert "ACF a été créé avec success" in _messages(response)[0]


def test_creation_enseigne_invalide(logged_client, media_dirs, make_child_center):
    make_child_center("ACF")

    response = logged_client.post(
        reverse("centers_purchasing:enseigne_create"), _enseigne_data(name="")
    )

    assert response.status_code == 200
    assert Signboard.objects.count() == 0


def test_modification_enseigne_supprime_le_logo_orphelin(
    logged_client, media_dirs, make_child_center, make_signboard, logo_file
):
    """Case 'supprimer le logo' cochée : le logo est retiré et son fichier devenu orphelin effacé"""
    make_child_center("ACF")
    enseigne = make_signboard("ACF", name="Acuitis")
    enseigne.logo.save("ancien.png", logo_file("ancien.png"), save=True)
    (media_dirs.logos / "perdu.png").write_bytes(b"orphelin")
    url = reverse("centers_purchasing:enseigne_update", args=[enseigne.pk])

    get = logged_client.get(url)
    response = logged_client.post(url, _enseigne_data(name="Acuitis maison", img_delete="on"))

    enseigne.refresh_from_db()
    assert get.context["titre_table"] == "Mise à jour de l'enseigne : ACF - Acuitis"
    assert get.context["enseigne"] == enseigne
    assert "ancien.png" in get.content.decode()
    assert response.status_code == 302
    assert (enseigne.name, bool(enseigne.logo), enseigne.modified_by) == (
        "Acuitis maison",
        False,
        logged_client.user,
    )
    assert not (media_dirs.logos / "ancien.png").exists()
    assert not (media_dirs.logos / "perdu.png").exists()
    assert "a été modifiée avec success" in _messages(response)[0]


def test_modification_enseigne_conserve_le_logo(
    logged_client, media_dirs, make_child_center, make_signboard, logo_file
):
    make_child_center("ACF")
    enseigne = make_signboard("ACF", name="Acuitis")
    enseigne.logo.save("garde.png", logo_file("garde.png"), save=True)
    other = make_signboard("GAF", name="GrandAudition")
    other.logo.save("autre.png", logo_file("autre.png"), save=True)

    response = logged_client.post(
        reverse("centers_purchasing:enseigne_update", args=[enseigne.pk]),
        _enseigne_data(comment="mis à jour"),
    )

    enseigne.refresh_from_db()
    assert response.status_code == 302
    assert enseigne.logo.name == "logos/garde.png"
    assert (media_dirs.logos / "garde.png").exists()
    assert (media_dirs.logos / "autre.png").exists()
    assert (media_dirs.static / "garde.png").exists()


def test_export_enseignes(logged_client, make_signboard, monkeypatch, caplog):
    make_signboard("ACF")

    response = logged_client.get(reverse("centers_purchasing:enseignes_export_list"))
    post = logged_client.post(reverse("centers_purchasing:enseignes_export_list"))

    assert response.status_code == 200
    assert response["Content-Disposition"].startswith("attachment; filename=LISTING_DES_ENSEIGNES_")
    assert post.url == reverse("centers_purchasing:enseignes_list")

    def _boom(*_args, **_kwargs):
        raise RuntimeError("excel cassé")

    with (
        patched_attrs(monkeypatch, enseignes_views, excel_enseignes_list=_boom),
        caplog.at_level(logging.ERROR, logger="views"),
    ):
        error = logged_client.get(reverse("centers_purchasing:enseignes_export_list"))

    assert error.status_code == 302
    assert "enseignes_export_list" in caplog.text
