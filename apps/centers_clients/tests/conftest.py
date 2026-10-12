# pylint: disable=W0621,E0401,R0913,W0611,C0415
"""
FR : conftest de l'app centers_clients - fabriques des maisons et de leurs dépendances
EN : centers_clients app conftest - factories for shops and their dependencies

Commentaire:

Les fabriques sont des fonctions, idempotentes sur les codes (get_or_create). Les référentiels
partagés (make_maison, make_society, make_article, make_country, ...) sont dans le conftest racine ;
ici ne restent que les fabriques propres à l'app.

created at: 2026-10-10
created by: Paulo ALVES
"""
import datetime
import itertools
import types
from decimal import Decimal
from pathlib import Path
from typing import Any
from collections.abc import Callable

import pytest

from apps.articles.models import Article
from apps.book.models import Society
from apps.centers_clients.models import (
    Contact,
    DocumentsSubscription,
    Maison,
    MaisonBi,
    MaisonSubcription,
    MaisonSupllierExclusion,
    MaisonSupplierIdentifier,
    SupllierCountryExclusion,
)
from apps.countries.models import Country

_COUNTER = itertools.count(1)


def _next(prefix: str) -> str:
    return f"{prefix}{next(_COUNTER):04d}"


# ==================================================================================================
# RÉFÉRENTIELS (countries, book, centers_purchasing, parameters, articles)
# ==================================================================================================


# ==================================================================================================
# CENTERS CLIENTS
# ==================================================================================================


@pytest.fixture
def make_maison_bi(make_country) -> Callable[..., MaisonBi]:
    """Fabrique de maisons B.I"""

    def _factory(code_maison: str | None = None, **kwargs: Any) -> MaisonBi:
        code_maison = code_maison or _next("BI")
        defaults = {
            "intitule": f"Maison BI {code_maison}",
            "intitule_court": code_maison,
            "code_cosium": f"COS{code_maison}",
            "reference_cosium": f"REF{code_maison}",
            "code_bbgr": f"BB{code_maison}",
            "opening_date": datetime.date(2021, 6, 1),
            "adresse": "2 avenue des Champs",
            "code_postal": "69000",
            "ville": "Lyon",
            "pays": make_country("FR"),
            "telephone": "0102030405",
            "email": f"{code_maison.lower()}@heron.local",
        }
        defaults.update(kwargs)
        return MaisonBi.objects.create(code_maison=code_maison, **defaults)

    return _factory


@pytest.fixture
def make_contact(make_maison, make_language) -> Callable[..., Contact]:
    """Fabrique de contacts de maison"""

    def _factory(maison: Maison | None = None, **kwargs: Any) -> Contact:
        defaults = {"first_name": "Jean", "last_name": "Dupont", "language": make_language("FRA")}
        defaults.update(kwargs)
        return Contact.objects.create(maison=maison or make_maison(), **defaults)

    return _factory


@pytest.fixture
def make_document_subscription(db) -> Callable[..., DocumentsSubscription]:
    """Fabrique d'abonnements aux documents"""

    def _factory(name: str = "Factures") -> DocumentsSubscription:
        return DocumentsSubscription.objects.get_or_create(name=name)[0]

    return _factory


@pytest.fixture
def make_exclusion(make_maison, make_society) -> Callable[..., MaisonSupllierExclusion]:
    """Fabrique de couples d'exclusion Tiers X3 / Maison"""

    def _factory(maison: Maison | None = None, society: Society | None = None) -> MaisonSupllierExclusion:
        return MaisonSupllierExclusion.objects.create(
            third_party_num=society or make_society("FOUR001", is_client=False),
            cct_uuid_identification=maison or make_maison(),
        )

    return _factory


@pytest.fixture
def make_country_exclusion(make_society, make_country) -> Callable[..., SupllierCountryExclusion]:
    """Fabrique de couples d'exclusion Tiers X3 / Pays"""

    def _factory(society: Society | None = None, country: Country | None = None) -> SupllierCountryExclusion:
        return SupllierCountryExclusion.objects.create(
            third_party_num=society or make_society("FOUR001", is_client=False),
            pays=country or make_country("FR"),
        )

    return _factory


@pytest.fixture
def make_supplier_identifier(make_maison, make_society) -> Callable[..., MaisonSupplierIdentifier]:
    """Fabrique d'identifiants Maison chez un fournisseur EDI"""

    def _factory(maison=None, society=None, identifiant: str = "ID-001") -> MaisonSupplierIdentifier:
        return MaisonSupplierIdentifier.objects.create(
            third_party_num=society or make_society("FOUR001", is_client=False),
            maison=maison or make_maison(),
            identifiant=identifiant,
        )

    return _factory


@pytest.fixture
def make_subscription(
    make_maison, make_article, make_unit, make_invoice_function, make_signboard
) -> Callable[..., MaisonSubcription]:
    """Fabrique d'abonnements par maison"""

    def _factory(maison: Maison | None = None, article: Article | None = None, **kwargs: Any) -> MaisonSubcription:
        defaults = {
            "qty": Decimal("1"),
            "unit_weight": make_unit(),
            "net_unit_price": Decimal("100"),
            "function": make_invoice_function(),
            "for_signboard": make_signboard("ACF"),
        }
        defaults.update(kwargs)
        return MaisonSubcription.objects.create(
            maison=maison or make_maison(), article=article or make_article(), **defaults
        )

    return _factory


@pytest.fixture
def maison_post_data(
    make_cct, make_society, make_child_center, make_signboard, make_client_familly, make_vat,
    make_code_plan, make_country_currency, make_language, make_country, make_type_vente, make_account,
) -> dict[str, str]:
    """Données POST complètes et valides pour MaisonForm (référentiels créés à la volée)"""
    make_cct("AF0001", name="Paris")
    make_society("CLI001", name="Client un")
    make_child_center("ACF")
    make_signboard("ACF")
    make_client_familly("franchise")
    make_vat("001")
    make_code_plan("FRA")
    make_country_currency("EUR")
    make_language("FRA")
    make_country("FR")
    make_type_vente(0)
    make_type_vente(2)
    credit = make_account("FRA", "411000", collective=True)
    debit = make_account("FRA", "401000", collective=True)

    return {
        "cct": "AF0001",
        "sign_board": "ACF",
        "intitule": "Acuitis Paris",
        "intitule_court": "PARIS",
        "client_familly": "Franchise",
        "opening_date": "2020-01-01",
        "signature_franchise_date": "2020-01-01",
        "generic_coefficient": "1",
        "adresse": "1 rue de la Paix",
        "code_postal": "75001",
        "ville": "Paris",
        "pays": "FR",
        "third_party_num": "CLI001",
        "sage_vat_by_default": "001",
        "sage_plan_code": "FRA",
        "currency": "EUR",
        "language": "FRA",
        "rfa_frequence": "1",
        "rfa_remise": "1",
        "credit_account": str(credit.uuid_identification),
        "debit_account": str(debit.uuid_identification),
        "integrable": "on",
        "chargeable": "on",
        "type_x3": "0",
    }


# ==================================================================================================
# RÉPERTOIRES ET FICHIERS
# ==================================================================================================


@pytest.fixture
def subscription_dirs(tmp_path: Path, settings) -> types.SimpleNamespace:
    """Redirige les répertoires d'import/backup des abonnements vers tmp_path"""

    dirs = types.SimpleNamespace(processing=tmp_path / "abonnements", backup=tmp_path / "backup_abonnements")

    for directory in vars(dirs).values():
        directory.mkdir(parents=True, exist_ok=True)

    settings.PROCESSING_CLIENS_SUBSCRIPTION = dirs.processing
    settings.BACKUP_CLIENS_SUBSCRIPTION_DIR = dirs.backup
    return dirs


@pytest.fixture
def picklers_dir(tmp_path: Path, settings) -> Path:
    """Redirige les fichiers pickle de l'import B.I et le MEDIA_ROOT vers tmp_path"""
    directory = tmp_path / "pickler"
    directory.mkdir()
    settings.MEDIA_ROOT = str(tmp_path / "media")
    settings.PICKLERS_DIR = directory
    return directory
