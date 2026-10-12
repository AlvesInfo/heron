# pylint: disable=W0621,E0401,R0913
"""
FR : conftest de l'app centers_purchasing - fabriques des dictionnaires de la centrale d'achat
EN : centers_purchasing app conftest - purchasing center dictionaries factories

Commentaire:

Les fabriques génériques (make_child_center, make_signboard, make_sale_price_category,
make_section, make_vat, make_account, make_big_category, make_sub_category, make_article,
make_article_account, make_accounts_axe_pro_category, make_user, logged_client, ajax_client, ...)
viennent du conftest racine. Ici : centrales mères, regroupements de facturation, dictionnaires
axe pro / regroupement, axe pro / tva, types de facture, répertoires media / static temporaires
et fichier image de logo.

created at: 2026-10-11
created by: Paulo ALVES
"""
import io
import types
from pathlib import Path
from typing import Any
from collections.abc import Callable

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from apps.centers_purchasing.models import (
    ApplicableProVat,
    AxeProGroupingGoods,
    GroupingGoods,
    PrincipalCenterPurchase,
    TypeFacture,
)


@pytest.fixture
def make_principal_center(db) -> Callable[..., PrincipalCenterPurchase]:  # pylint: disable=W0613
    """Fabrique de centrales mères (réutilise le code s'il existe)"""

    def _factory(code: str = "HA", **kwargs: Any) -> PrincipalCenterPurchase:
        defaults = {"name": f"Centrale mère {code}"}
        defaults.update(kwargs)
        return PrincipalCenterPurchase.objects.get_or_create(code=code, defaults=defaults)[0]

    return _factory


@pytest.fixture
def make_grouping_goods(db) -> Callable[..., GroupingGoods]:  # pylint: disable=W0613
    """Fabrique de regroupements de facturation"""

    def _factory(grouping_goods: str = "Montures", ranking: int = 1, base: str = "Marchandises") -> GroupingGoods:
        return GroupingGoods.objects.get_or_create(
            grouping_goods=grouping_goods, defaults={"ranking": ranking, "base": base}
        )[0]

    return _factory


@pytest.fixture
def make_axe_pro_grouping(make_section, make_grouping_goods) -> Callable[..., AxeProGroupingGoods]:
    """Fabrique du dictionnaire axe pro / regroupement de facturation"""

    def _factory(section: str = "OPT", grouping=None) -> AxeProGroupingGoods:
        return AxeProGroupingGoods.objects.create(
            axe_pro=make_section("PRO", section), grouping_goods=grouping or make_grouping_goods()
        )

    return _factory


@pytest.fixture
def make_applicable_pro_vat(make_child_center, make_section, make_vat) -> Callable[..., ApplicableProVat]:
    """Fabrique du dictionnaire centrale fille / axe pro / tva"""

    def _factory(child_center: str = "ACF", section: str | None = "OPT", vat: str = "001") -> ApplicableProVat:
        return ApplicableProVat.objects.create(
            child_center=make_child_center(child_center),
            axe_pro=make_section("PRO", section) if section else None,
            vat=make_vat(vat),
        )

    return _factory


@pytest.fixture
def make_type_facture(make_child_center) -> Callable[..., TypeFacture]:
    """Fabrique des types de facture par centrale fille"""

    def _factory(child_center: str = "ACF", invoice_type: str = "380", **kwargs: Any) -> TypeFacture:
        defaults = {"purchase_type_facture": "FAC", "sale_type_facture": "FAV", "invoice_name": "Facture"}
        defaults.update(kwargs)
        return TypeFacture.objects.create(
            child_center=make_child_center(child_center), invoice_type=invoice_type, **defaults
        )

    return _factory


@pytest.fixture
def media_dirs(tmp_path: Path, settings) -> types.SimpleNamespace:
    """
    Redirige les répertoires media (logos), static (copies des logos) et d'import des comptes
    vers tmp_path : les vues et les scripts n'écrivent jamais dans files/.
    """
    dirs = types.SimpleNamespace(
        media=tmp_path / "media",
        logos=tmp_path / "media" / "logos",
        static=tmp_path / "static",
        import_accounts=tmp_path / "processing" / "IMPORT_ACCOUNTS",
        backup_accounts=tmp_path / "backup" / "IMPORT_ACCOUNTS",
    )

    for directory in (*vars(dirs).values(), dirs.static / "images", dirs.static / "img"):
        directory.mkdir(parents=True, exist_ok=True)

    settings.MEDIA_ROOT = str(dirs.media)
    settings.MEDIA_DIR = dirs.media
    settings.STATIC_DIR = dirs.static
    settings.IMPORT_ACCOUNTS = dirs.import_accounts
    settings.BACKUP_IMPORT_ACCOUNTS = dirs.backup_accounts
    return dirs


@pytest.fixture
def logo_file() -> Callable[..., SimpleUploadedFile]:
    """Fabrique de fichiers image png (logo) téléversables"""

    def _factory(name: str = "logo.png", color: str = "red") -> SimpleUploadedFile:
        buffer = io.BytesIO()
        Image.new("RGB", (4, 4), color).save(buffer, format="PNG")
        return SimpleUploadedFile(name, buffer.getvalue(), content_type="image/png")

    return _factory


@pytest.fixture
def star_client(logged_client):
    """Client authentifié dont l'utilisateur voit toutes les centrales (code_child_center *)"""
    logged_client.user.code_child_center = "*"
    logged_client.user.save()
    return logged_client
