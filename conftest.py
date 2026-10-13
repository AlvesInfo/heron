# pylint: disable=W0621,E0401
"""FR : conftest racine - bibliothèque de fixtures et de context managers génériques,


     partagée par toutes les apps du projet Héron
EN : Root conftest - library of generic fixtures and context managers shared by all apps

Commentaire:

Tout ce qui est ici est indépendant d'une app métier :
    - context managers réutilisables (patch de module, fichiers csv temporaires, capture SQL)
    - fixtures de répertoires Sage temporaires (aucune écriture dans files/)
    - fabrique de Trace (apps.data_flux) utilisée par tous les imports

Les fixtures spécifiques à une app vivent dans apps/<app>/tests/conftest.py

created at: 2026-10-10
created by: Paulo ALVES
"""

import contextlib
import csv
import datetime
import itertools
import types
from collections.abc import Callable, Iterable, Iterator
from decimal import Decimal
from pathlib import Path
from typing import Any
from uuid import uuid4

import email_validator
import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

# Les fabriques de test utilisent des adresses en `.local` (domaine réservé, refusé par
# email-validator >= 1.2, donc par pydantic.EmailStr) : autorisé pour la session de test seulement.
email_validator.SPECIAL_USE_DOMAIN_NAMES.remove("local")

# Les scripts utilitaires des répertoires bin/ (ex. apps/invoices/bin/api_gmail/test_gmail_api.py,
# interactif) ne sont pas des tests : on les exclut de la collecte
collect_ignore_glob = ["apps/*/bin/*", "heron/bin/*"]

# Instantané de production des définitions de flux fournisseurs (edi.SupplierDefinition +
# edi.ColumnDefinition). Depuis la directive D1, l'URLconf se charge sans ces lignes : elles ne
# servent plus qu'aux tests qui construisent réellement les schémas djantic des flux (apps/edi).
COLUMN_DEFINITIONS_FIXTURES = [
    str(Path(__file__).parent / "apps/edi/tests/test_fixtures/column_definitions.json"),
]


@pytest.fixture(scope="session")
def column_definitions_data(django_db_setup, django_db_blocker):  # pylint: disable=W0613
    """Charge l'instantané des définitions de colonnes des flux fournisseurs (à la demande)"""
    from django.core.management import call_command  # pylint: disable=C0415

    with django_db_blocker.unblock():
        call_command("loaddata", *COLUMN_DEFINITIONS_FIXTURES, verbosity=0)


# ==================================================================================================
# CONTEXT MANAGERS GÉNÉRIQUES (importables directement dans les tests)
# ==================================================================================================


@contextlib.contextmanager
def patched_attrs(monkeypatch: pytest.MonkeyPatch, target: Any, **attrs: Any) -> Iterator[Any]:
    """Patch temporaire d'attributs d'un module ou d'un objet, restaurés à la sortie du bloc.

    :param monkeypatch: fixture monkeypatch de pytest
    :param target: module ou objet à patcher
    :param attrs: attributs à poser
    """
    with monkeypatch.context() as patch:
        for name, value in attrs.items():
            patch.setattr(target, name, value, raising=False)
        yield target


@contextlib.contextmanager
def csv_file(
    path: Path,
    rows: Iterable[Iterable[Any]],
    delimiter: str = ";",
    quoting: int = csv.QUOTE_ALL,
    encoding: str = "utf8",
    lineterminator: str = "\r\n",
) -> Iterator[Path]:
    """Écrit un fichier csv (format des extractions Sage X3 par défaut) et le supprime à la sortie.

    :param path: chemin du fichier à écrire
    :param rows: lignes à écrire
    :param delimiter: séparateur de champs
    :param quoting: mode de quoting csv
    :param encoding: encodage du fichier
    :param lineterminator: fin de ligne (CRLF comme les exports Sage)
    """
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding=encoding, newline="") as file:
        writer = csv.writer(
            file,
            delimiter=delimiter,
            quoting=quoting,  # type: ignore[arg-type]
            lineterminator=lineterminator,
        )
        writer.writerows(rows)

    try:
        yield path
    finally:
        path.unlink(missing_ok=True)


@contextlib.contextmanager
def captured_queries() -> Iterator[CaptureQueriesContext]:
    """Capture les requêtes SQL exécutées sur la connexion par défaut."""
    with CaptureQueriesContext(connection) as context:
        yield context


@contextlib.contextmanager
def raising_once(exception: BaseException) -> Iterator[Callable[..., None]]:
    """Fournit un callable qui lève `exception` la première fois puis ne fait plus rien.

    Utile pour tester les branches except des boucles de traitement.
    """
    state = {"raised": False}

    def _call(*_args: Any, **_kwargs: Any) -> None:
        if not state["raised"]:
            state["raised"] = True
            raise exception

    yield _call


# ==================================================================================================
# FIXTURES GÉNÉRIQUES
# ==================================================================================================


@pytest.fixture
def patch_module(
    monkeypatch: pytest.MonkeyPatch,
) -> Callable[..., contextlib.AbstractContextManager]:
    """Fabrique de context manager : with patch_module(module, ATTR=valeur): ..."""

    def _factory(target: Any, **attrs: Any) -> contextlib.AbstractContextManager:
        return patched_attrs(monkeypatch, target, **attrs)

    return _factory


@pytest.fixture
def sage_dirs(tmp_path: Path, settings) -> types.SimpleNamespace:
    """Redirige tous les répertoires Sage (archive X3, processing, backup, pré-traitement)

    vers un répertoire temporaire, pour que les tests n'écrivent jamais dans files/.
    """
    dirs = types.SimpleNamespace(
        archive=tmp_path / "archive",
        processing=tmp_path / "processing" / "sage",
        backup=tmp_path / "backup" / "sage",
        pre_processing=tmp_path / "pre_processing",
    )

    for directory in vars(dirs).values():
        directory.mkdir(parents=True, exist_ok=True)

    settings.ACUITIS_ARCHIVE_EM_DIR = dirs.archive
    settings.PROCESSING_SAGE_DIR = dirs.processing
    settings.BACKUP_SAGE_DIR = dirs.backup
    settings.PRE_PROCESSING = dirs.pre_processing
    return dirs


@pytest.fixture
def make_csv(tmp_path: Path) -> Callable[..., Path]:
    """Fabrique de fichiers csv persistants le temps du test (dans tmp_path)."""

    def _factory(name: str, rows: Iterable[Iterable[Any]], **kwargs: Any) -> Path:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open("w", encoding=kwargs.pop("encoding", "utf8"), newline="") as file:
            writer = csv.writer(
                file,
                delimiter=kwargs.pop("delimiter", ";"),
                quoting=kwargs.pop("quoting", csv.QUOTE_ALL),
                lineterminator=kwargs.pop("lineterminator", "\r\n"),
            )
            writer.writerows(rows)

        return path

    return _factory


@pytest.fixture
def make_trace(db) -> Callable[..., Any]:  # pylint: disable=W0613
    """Fabrique de Trace (apps.data_flux) avec les valeurs minimales requises."""
    from apps.data_flux.models import Trace  # pylint: disable=C0415

    def _factory(**kwargs: Any) -> Trace:
        defaults = {
            "created_at": timezone.now(),
            "uuid_identification": uuid4(),
            "trace_name": "trace de test",
            "file_name": "fichier_test.heron",
            "application_name": "tests",
            "flow_name": "Test",
            "comment": "trace créée par les tests",
            "created_numbers_records": 0,
            "updated_numbers_records": 0,
            "errors_numbers_records": 0,
            "unknown_numbers_records": 0,
        }
        defaults.update(kwargs)
        return Trace.objects.create(**defaults)

    return _factory


# ==================================================================================================
# UTILISATEURS ET CLIENTS HTTP
# ==================================================================================================


@pytest.fixture
def make_user(db) -> Callable[..., Any]:  # pylint: disable=W0613
    """Fabrique d'utilisateurs Héron (email = identifiant), actif par défaut"""
    from apps.users.models import User  # pylint: disable=C0415

    def _factory(
        email: str = "test@heron.local",
        username: str = "test",
        password: str = "motdepasse",
        **kwargs: Any,
    ) -> User:
        kwargs.setdefault("code_child_center", "ACU")
        return User.objects.create_user(username, email, password, **kwargs)

    return _factory


@pytest.fixture
def logged_client(client, make_user) -> Any:
    """Client Django authentifié (passe le LoginMiddleware), l'utilisateur est en `client.user`"""
    user = make_user()
    client.force_login(user)
    client.user = user
    return client


@pytest.fixture
def ajax_client(make_user) -> Any:
    """Client Django authentifié dont chaque requête porte l'en-tête X-Requested-With (is_ajax)"""
    from django.test import Client  # pylint: disable=C0415

    ajax = Client(HTTP_X_REQUESTED_WITH="XMLHttpRequest")
    ajax.user = make_user(email="ajax@heron.local", username="ajax")  # type: ignore[attr-defined]
    ajax.force_login(ajax.user)  # type: ignore[attr-defined]
    return ajax


# ==================================================================================================
# RÉFÉRENTIELS PARTAGÉS (fabriques-fonctions idempotentes sur les codes)
# ==================================================================================================
_REF_COUNTER = itertools.count(1)


def next_code(prefix: str) -> str:
    """Code unique et lisible pour les champs uniques des fabriques"""
    return f"{prefix}{next(_REF_COUNTER):04d}"


# --- accountancy ----------------------------------------------------------------------------------


@pytest.fixture
def make_axe(db) -> Callable[..., Any]:  # pylint: disable=W0613
    """Fabrique d'AxeSage (réutilise l'axe s'il existe déjà)"""
    from apps.accountancy.models import AxeSage  # pylint: disable=C0415

    def _factory(axe: str = "BU", **kwargs: Any):
        existing = AxeSage.objects.filter(axe=axe).first()

        if existing:
            return existing

        defaults = {"name": f"Axe {axe}", "short_name": axe}
        defaults.update(kwargs)
        return AxeSage.objects.create(axe=axe, **defaults)

    return _factory


@pytest.fixture
def make_section(make_axe) -> Callable[..., Any]:
    """Fabrique de SectionSage rattachée à un axe (réutilise le couple axe/section s'il existe)"""
    from apps.accountancy.models import SectionSage  # pylint: disable=C0415

    def _factory(axe: str = "CCT", section: str | None = None, **kwargs: Any):
        section = section or next_code("S")
        axe_obj = make_axe(axe)
        existing = SectionSage.objects.filter(axe=axe_obj, section=section).first()

        if existing and not kwargs:
            return existing

        defaults = {"name": f"Section {section}", "short_name": section[:20]}
        defaults.update(kwargs)
        return SectionSage.objects.create(axe=axe_obj, section=section, **defaults)

    return _factory


@pytest.fixture
def make_cct(db) -> Callable[..., Any]:  # pylint: disable=W0613
    """Fabrique de CctSage (réutilise le cct s'il existe déjà)"""
    from apps.accountancy.models import CctSage  # pylint: disable=C0415

    def _factory(cct: str | None = None, **kwargs: Any):
        cct = cct or next_code("AF")
        existing = CctSage.objects.filter(cct=cct).first()

        if existing:
            return existing

        defaults = {"name": f"Maison {cct}", "short_name": cct}
        defaults.update(kwargs)
        return CctSage.objects.create(cct=cct, **defaults)

    return _factory


@pytest.fixture
def make_vat(db) -> Callable[..., Any]:  # pylint: disable=W0613
    """Fabrique de VatSage (réutilise la taxe si elle existe déjà)"""
    from apps.accountancy.models import VatSage  # pylint: disable=C0415

    def _factory(vat: str = "001", vat_regime: str = "FRA", **kwargs: Any):
        existing = VatSage.objects.filter(vat=vat).first()

        if existing:
            return existing

        defaults = {"name": f"TVA {vat}", "short_name": vat, "auuid": uuid4()}
        defaults.update(kwargs)
        return VatSage.objects.create(vat=vat, vat_regime=vat_regime, **defaults)

    return _factory


@pytest.fixture
def make_account(db) -> Callable[..., Any]:  # pylint: disable=W0613
    """Fabrique d'AccountSage (réutilise le couple plan/compte s'il existe)"""
    from apps.accountancy.models import AccountSage  # pylint: disable=C0415

    def _factory(code_plan_sage: str = "FRA", account: str | None = None, **kwargs: Any):
        account = account or next_code("41")
        existing = AccountSage.objects.filter(
            code_plan_sage=code_plan_sage, account=account
        ).first()

        if existing and not kwargs:
            return existing

        defaults = {"name": f"Compte {account}", "short_name": account[:20]}
        defaults.update(kwargs)
        return AccountSage.objects.create(
            code_plan_sage=code_plan_sage, account=account, **defaults
        )

    return _factory


@pytest.fixture
def make_code_plan(db) -> Callable[..., Any]:  # pylint: disable=W0613
    """Fabrique de CodePlanSage"""
    from apps.accountancy.models import CodePlanSage  # pylint: disable=C0415

    def _factory(code_plan_sage: str = "FRA"):
        return CodePlanSage.objects.get_or_create(code_plan_sage=code_plan_sage)[0]

    return _factory


@pytest.fixture
def make_tab_div(db) -> Callable[..., Any]:  # pylint: disable=W0613
    """Fabrique de TabDivSage (table 6100 = budgets par défaut)"""
    from apps.accountancy.models import TabDivSage  # pylint: disable=C0415

    def _factory(num_table: int = 6100, code: str | None = None, **kwargs: Any):
        code = code or next_code("B")
        defaults = {"name": f"Divers {code}", "short_name": code}
        defaults.update(kwargs)
        return TabDivSage.objects.create(num_table=num_table, code=code, **defaults)

    return _factory


# --- countries / book / centers_purchasing / parameters -------------------------------------------


@pytest.fixture
def make_country(db) -> Callable[..., Any]:  # pylint: disable=W0613
    """Fabrique de pays (pk = code pays)"""
    from apps.countries.models import Country  # pylint: disable=C0415

    def _factory(country: str = "FR", country_name: str | None = None, **kwargs: Any):
        return Country.objects.get_or_create(
            country=country, defaults={"country_name": country_name or f"Pays {country}", **kwargs}
        )[0]

    return _factory


@pytest.fixture
def make_language(db) -> Callable[..., Any]:  # pylint: disable=W0613
    """Fabrique de langues (pk = code)"""
    from apps.countries.models import Language  # pylint: disable=C0415

    def _factory(code: str = "FRA", name: str = "Français"):
        return Language.objects.get_or_create(code=code, defaults={"name": name})[0]

    return _factory


@pytest.fixture
def make_country_currency(db) -> Callable[..., Any]:  # pylint: disable=W0613
    """Fabrique de devises countries.Currency (pk = code)"""
    from apps.countries.models import Currency  # pylint: disable=C0415

    def _factory(code: str = "EUR", name: str = "Euro"):
        return Currency.objects.get_or_create(code=code, defaults={"name": name})[0]

    return _factory


@pytest.fixture
def make_society(db) -> Callable[..., Any]:  # pylint: disable=W0613
    """Fabrique de tiers X3 (client et utilisé par défaut, réutilise le tiers s'il existe)"""
    from apps.book.models import Society  # pylint: disable=C0415

    def _factory(third_party_num: str | None = None, **kwargs: Any):
        third_party_num = third_party_num or next_code("TIERS")
        defaults = {
            "name": f"Société {third_party_num}",
            "short_name": third_party_num[:20],
            "is_client": True,
            "in_use": True,
        }
        defaults.update(kwargs)
        return Society.objects.get_or_create(third_party_num=third_party_num, defaults=defaults)[0]

    return _factory


@pytest.fixture
def make_address(make_society) -> Callable[..., Any]:
    """Fabrique d'adresses Sage d'un tiers (address_code 1 = adresse principale)"""
    from apps.book.models import Address  # pylint: disable=C0415

    def _factory(society=None, address_code: str = "1", **kwargs: Any):
        return Address.objects.create(
            society=society or make_society(), address_code=address_code, **kwargs
        )

    return _factory


@pytest.fixture
def make_supplier_cct(make_society, make_cct) -> Callable[..., Any]:
    """Fabrique d'identifiants fournisseur par cct (book.SupplierCct)"""
    from apps.book.models import SupplierCct  # pylint: disable=C0415

    def _factory(society=None, cct=None, cct_identifier: str | None = None):
        return SupplierCct.objects.create(
            third_party_num=society or make_society("COSI001", is_client=False),
            cct_uuid_identification=cct or make_cct(),
            cct_identifier=cct_identifier,
        )

    return _factory


@pytest.fixture
def make_child_center(db) -> Callable[..., Any]:  # pylint: disable=W0613
    """Fabrique de centrales filles (avec sa centrale mère ACU)"""
    from apps.centers_purchasing.models import ChildCenterPurchase, PrincipalCenterPurchase  # pylint: disable=C0415

    def _factory(code: str = "ACF", **kwargs: Any):
        principal = PrincipalCenterPurchase.objects.get_or_create(
            code="ACU", defaults={"name": "Acuitis centrale"}
        )[0]
        defaults = {
            "base_center": principal,
            "name": f"Centrale {code}",
            "societe_cpy_x3": "ACU",
            "site_fcy_x3": code,
            "code_plan_sage": "FRA",
        }
        defaults.update(kwargs)
        return ChildCenterPurchase.objects.get_or_create(code=code, defaults=defaults)[0]

    return _factory


@pytest.fixture
def make_signboard(db) -> Callable[..., Any]:  # pylint: disable=W0613
    """Fabrique d'enseignes"""
    from apps.centers_purchasing.models import Signboard  # pylint: disable=C0415

    def _factory(code: str = "ACF", **kwargs: Any):
        defaults = {"name": f"Enseigne {code}", "email_contact": f"{code.lower()}@heron.local"}
        defaults.update(kwargs)
        return Signboard.objects.get_or_create(code=code, defaults=defaults)[0]

    return _factory


@pytest.fixture
def make_sale_price_category(db) -> Callable[..., Any]:  # pylint: disable=W0613
    """Fabrique de catégories de prix"""
    from apps.parameters.models import SalePriceCategory  # pylint: disable=C0415

    def _factory(name: str = "Tarif franchise"):
        return SalePriceCategory.objects.get_or_create(name=name)[0]

    return _factory


@pytest.fixture
def make_nature(db) -> Callable[..., Any]:  # pylint: disable=W0613
    """Fabrique de natures (contacts)"""
    from apps.parameters.models import Nature  # pylint: disable=C0415

    def _factory(name: str = "Gérant", **kwargs: Any):
        kwargs.setdefault("for_contact", True)
        return Nature.objects.get_or_create(name=name, defaults=kwargs)[0]

    return _factory


@pytest.fixture
def make_invoice_function(db) -> Callable[..., Any]:  # pylint: disable=W0613
    """Fabrique de fonctions de facturation"""
    from apps.parameters.models import InvoiceFunctions  # pylint: disable=C0415

    def _factory(function_name: str = "ABONNEMENT", **kwargs: Any):
        kwargs.setdefault("function", "def abonnement(): ...")
        return InvoiceFunctions.objects.get_or_create(function_name=function_name, defaults=kwargs)[
            0
        ]

    return _factory


@pytest.fixture
def make_unit(db) -> Callable[..., Any]:  # pylint: disable=W0613
    """Fabrique d'unités"""
    from apps.parameters.models import UnitChoices  # pylint: disable=C0415

    def _factory(num: int = 1, unity: str = "U"):
        return UnitChoices.objects.get_or_create(num=num, defaults={"unity": unity})[0]

    return _factory


@pytest.fixture
def make_big_category(db) -> Callable[..., Any]:  # pylint: disable=W0613
    """Fabrique de grandes catégories d'articles (slug_name calculé à la sauvegarde)"""
    from apps.parameters.models import Category  # pylint: disable=C0415

    def _factory(name: str = "Abonnements", **kwargs: Any):
        existing = Category.objects.filter(name=name).first()

        if existing:
            return existing

        defaults = {"code": name[:15].upper(), "ranking": next(_REF_COUNTER) + 1000}
        defaults.update(kwargs)
        return Category.objects.create(name=name, **defaults)

    return _factory


@pytest.fixture
def make_sub_category(make_big_category) -> Callable[..., Any]:
    """Fabrique de rubriques (sous-catégories) rattachées à une grande catégorie"""
    from apps.parameters.models import SubCategory  # pylint: disable=C0415

    def _factory(name: str = "Rubrique", big_category=None, **kwargs: Any):
        existing = SubCategory.objects.filter(name=name).first()

        if existing:
            return existing

        defaults = {"code": name[:15].upper(), "ranking": next(_REF_COUNTER) + 2000}
        defaults.update(kwargs)
        return SubCategory.objects.create(
            name=name, big_category=big_category or make_big_category(), **defaults
        )

    return _factory


@pytest.fixture
def make_article(make_society, make_big_category, make_unit) -> Callable[..., Any]:
    """Fabrique d'articles (par défaut dans la grande catégorie Abonnements, unité 1)"""
    from apps.articles.models import Article  # pylint: disable=C0415

    def _factory(reference: str | None = None, society=None, big_category=None, **kwargs: Any):
        make_unit(1, "U")
        return Article.objects.create(
            third_party_num=society or make_society("FOUR001", is_client=False),
            reference=reference or next_code("ART"),
            big_category=big_category or make_big_category(),
            **kwargs,
        )

    return _factory


@pytest.fixture
def make_article_account(make_article, make_child_center, make_vat) -> Callable[..., Any]:
    """Fabrique de comptes achat/vente par article, centrale et tva"""
    from apps.articles.models import ArticleAccount  # pylint: disable=C0415

    def _factory(
        article=None,
        child_center: str = "ACF",
        vat: str = "001",
        purchase_account: str = "607000",
        sale_account: str = "707000",
    ):
        return ArticleAccount.objects.create(
            article=article or make_article(),
            child_center=make_child_center(child_center),
            vat=make_vat(vat),
            purchase_account=purchase_account,
            sale_account=sale_account,
        )

    return _factory


@pytest.fixture
def make_accounts_axe_pro_category(
    make_child_center, make_big_category, make_section, make_vat, make_account
) -> Callable[..., Any]:
    """Fabrique du paramétrage des comptes par axe pro / catégorie / tva / centrale"""
    from apps.centers_purchasing.models import AccountsAxeProCategory  # pylint: disable=C0415

    def _factory(
        axe_pro=None,
        big_category=None,
        sub_category=None,
        child_center: str = "ACF",
        vat: str = "001",
        purchase: str = "607000",
        sale: str = "707000",
    ):
        return AccountsAxeProCategory.objects.create(
            child_center=make_child_center(child_center),
            big_category=big_category or make_big_category(),
            sub_category=sub_category,
            axe_pro=axe_pro or make_section("PRO", "DIV"),
            vat=make_vat(vat),
            purchase_account=make_account("FRA", purchase),
            sale_account=make_account("FRA", sale),
        )

    return _factory


# --- centers_clients ------------------------------------------------------------------------------


@pytest.fixture
def make_type_vente(db) -> Callable[..., Any]:  # pylint: disable=W0613
    """Fabrique de types de vente (0 BLOCAGE, 1 VENTE, 2 OD ANA)"""
    from apps.centers_clients.models import TypeVente  # pylint: disable=C0415

    names = {0: "BLOCAGE", 1: "VENTE", 2: "OD ANA"}

    def _factory(num: int = 0, name: str | None = None):
        return TypeVente.objects.get_or_create(
            num=num, defaults={"name": name or names.get(num, f"TYPE {num}")}
        )[0]

    return _factory


@pytest.fixture
def make_client_familly(db) -> Callable[..., Any]:  # pylint: disable=W0613
    """Fabrique de familles clients"""
    from apps.centers_clients.models import ClientFamilly  # pylint: disable=C0415

    def _factory(name: str = "franchise", **kwargs: Any):
        existing = ClientFamilly.objects.filter(name=name.capitalize()).first()
        return existing or ClientFamilly.objects.create(name=name, **kwargs)

    return _factory


@pytest.fixture
def make_maison(
    make_cct,
    make_society,
    make_child_center,
    make_signboard,
    make_client_familly,
    make_vat,
    make_code_plan,
    make_country_currency,
    make_language,
    make_country,
    make_type_vente,
) -> Callable[..., Any]:
    """Fabrique de maisons avec toutes leurs dépendances créées à la volée"""
    from apps.centers_clients.models import Maison  # pylint: disable=C0415

    def _factory(cct: str | None = None, **kwargs: Any):
        cct = cct or next_code("AF")
        defaults = {
            "cct": make_cct(cct),
            "third_party_num": make_society("CLI001"),
            "center_purchase": make_child_center("ACF"),
            "sign_board": make_signboard("ACF"),
            "intitule": f"Maison {cct}",
            "intitule_court": cct,
            "client_familly": make_client_familly(),
            "opening_date": datetime.date(2020, 1, 1),
            "sage_vat_by_default": make_vat("001"),
            "sage_plan_code": make_code_plan("FRA"),
            "currency": make_country_currency("EUR"),
            "language": make_language("FRA"),
            "adresse": "1 rue de la Paix",
            "code_postal": "75001",
            "ville": "Paris",
            "pays": make_country("FR"),
            "type_x3": make_type_vente(0),
        }
        defaults.update(kwargs)

        if isinstance(defaults["type_x3"], int):
            defaults["type_x3"] = make_type_vente(defaults["type_x3"])

        return Maison.objects.create(**defaults)

    return _factory


@pytest.fixture
def make_default_axes(make_section, make_big_category) -> Callable[..., Any]:
    """Fabrique du paramétrage des axes par défaut des nouveaux articles (slug axes_articles)"""
    from apps.parameters.models import DefaultAxeArticle  # pylint: disable=C0415

    def _factory(slug_name: str = "axes_articles", **kwargs: Any):
        defaults = {
            "big_category": make_big_category("Marchandises"),
            "axe_bu": make_section("BU", "CAHA"),
            "axe_prj": make_section("PRJ", "NAF"),
            "axe_pys": make_section("PYS", "FR"),
            "axe_rfa": make_section("RFA", "NAF"),
        }
        defaults.update(kwargs)
        return DefaultAxeArticle.objects.get_or_create(slug_name=slug_name, defaults=defaults)[0]

    return _factory


@pytest.fixture
def make_supplier_family_axes(make_section, make_big_category) -> Callable[..., Any]:
    """Fabrique des statistiques familles -> axe pro (stat ACUITIS par défaut)"""
    from apps.book.models import StatFamillyAxes, SupplierFamilyAxes  # pylint: disable=C0415

    def _factory(
        regex_match: str = "LUNETTES",
        stat_name: str = "ACUITIS",
        axe_pro=None,
        big_category=None,
        **kwargs: Any,
    ):
        stat = StatFamillyAxes.objects.get_or_create(name=stat_name)[0]
        return SupplierFamilyAxes.objects.create(
            stat_name=stat,
            regex_match=regex_match,
            expected_result=regex_match,
            axe_pro=axe_pro or make_section("PRO", "OPT"),
            big_category=big_category or make_big_category("Marchandises"),
            **kwargs,
        )

    return _factory


# ==================================================================================================
# FACTURES DE VENTE (partagées : invoices, book, ...)
# ==================================================================================================
SALE_INVOICE_DATE = datetime.date(2026, 1, 31)


@pytest.fixture
def make_centers_invoices(db) -> Callable[..., Any]:  # pylint: disable=W0613
    """Fabrique de centrales figées sur facture (invoices.CentersInvoices)"""
    from apps.invoices.models import CentersInvoices  # pylint: disable=C0415

    def _factory(code_center: str = "ACF", **kwargs: Any):
        defaults = {
            "member_num": "123456",
            "vat_regime_center": "FRA",
            "cpy": "ACF",
            "fcy": "ACF",
            "code_plan_sage": "FRA",
            "bank_center": "Banque",
            "iban_center": "FR7600000000000000000000000",
            "code_swift_center": "SWIFTFRPP",
            "legal_notice_center": "Mentions légales",
            "footer": "Bas de page",
        }
        defaults.update(kwargs)
        return CentersInvoices.objects.create(code_center=code_center, **defaults)

    return _factory


@pytest.fixture
def make_signboards_invoices(db) -> Callable[..., Any]:  # pylint: disable=W0613
    """Fabrique d'enseignes figées sur facture (invoices.SignboardsInvoices)"""
    from apps.invoices.models import SignboardsInvoices  # pylint: disable=C0415

    def _factory(code_signboard: str = "ACF", **kwargs: Any):
        defaults = {"message": "Merci de votre confiance", "email_contact": "contact@heron.local"}
        defaults.update(kwargs)
        return SignboardsInvoices.objects.create(code_signboard=code_signboard, **defaults)

    return _factory


@pytest.fixture
def make_parties_invoices(make_cct, make_society) -> Callable[..., Any]:
    """Fabrique des parties figées sur facture (invoices.PartiesInvoices : maison et tiers)"""
    from apps.invoices.models import PartiesInvoices  # pylint: disable=C0415

    def _factory(cct=None, society=None, **kwargs: Any):
        defaults = {
            "name_cct": "Maison Paris",
            "adresse_cct": "1 rue de la Paix",
            "code_postal_cct": "75001",
            "ville_cct": "Paris",
            "pays_cct": "France",
            "name_third_party": "Client SAS",
            "adresse_third_party": "2 avenue des Champs",
            "code_postal_third_party": "75008",
            "ville_third_party": "Paris",
            "pays_third_party": "France",
            "payment_condition_client": "30 jours",
        }
        defaults.update(kwargs)
        return PartiesInvoices.objects.create(
            cct=cct or make_cct("AF0001"),
            third_party_num=society or make_society("CLI001"),
            **defaults,
        )

    return _factory


@pytest.fixture
def make_sale_invoice(
    make_society, make_cct, make_centers_invoices, make_signboards_invoices, make_parties_invoices
) -> Callable[..., Any]:
    """Fabrique de factures de vente invoices.SaleInvoice (marchandises, type_x3 1 = vente)"""
    from apps.invoices.models import SaleInvoice  # pylint: disable=C0415

    def _factory(cct: str = "AF0001", third_party_num: str = "CLI001", **kwargs: Any):
        cct_obj = make_cct(cct)
        society = make_society(third_party_num)
        defaults = {
            "invoice_sage_number": next_code("VTE"),
            "invoice_number": next_code("FV"),
            "invoice_date": SALE_INVOICE_DATE,
            "invoice_month": SALE_INVOICE_DATE.replace(day=1),
            "invoice_year": SALE_INVOICE_DATE.year,
            "invoice_type": "380",
            "invoice_type_name": "Facture",
            "devise": "EUR",
            "invoice_amount_without_tax": Decimal(100),
            "invoice_amount_tax": Decimal(20),
            "invoice_amount_with_tax": Decimal(120),
            "big_category": "Marchandises",
            "big_category_code": "MAR",
            "big_category_slug_name": "marchandises",
            "big_category_ranking": 1,
            "formation": "",
            "type_x3": 1,
            "vat_regime": "FRA",
            "cpy": "ACF",
            "fcy": "ACF",
            "centers": make_centers_invoices(),
            "signboard": make_signboards_invoices(),
            "parties": make_parties_invoices(cct=cct_obj, society=society),
        }
        defaults.update(kwargs)
        return SaleInvoice.objects.create(cct=cct_obj, third_party_num=society, **defaults)

    return _factory


@pytest.fixture
def make_edi_import(make_society) -> Callable[..., Any]:
    """Fabrique de lignes edi_ediimport minimales (facture fournisseur par défaut)"""
    from apps.edi.models import EdiImport  # pylint: disable=C0415

    def _factory(third_party_num: str = "FOUR001", reference_article: str = "ART-1", **kwargs: Any):
        make_society(third_party_num, is_client=False)
        defaults = {
            "invoice_number": next_code("FAC"),
            "invoice_date": datetime.date(2026, 1, 15),
            "libelle": f"Libellé {reference_article}",
            "qty": Decimal(1),
            "net_unit_price": Decimal(10),
            "net_amount": Decimal(10),
            "code_center": "ACF",
            "sale_invoice": False,
            "valid": True,
        }
        defaults.update(kwargs)
        return EdiImport.objects.create(
            third_party_num=third_party_num, reference_article=reference_article, **defaults
        )

    return _factory


@pytest.fixture
def make_invoice_common_details(make_society, make_cct) -> Callable[..., Any]:
    """Fabrique de lignes invoices_invoicecommondetails (factures définitives)"""
    from apps.invoices.models import InvoiceCommonDetails  # pylint: disable=C0415

    def _factory(third_party_num: str = "FOUR001", invoice_number: str = "FAC-1", **kwargs: Any):
        defaults = {
            "import_uuid_identification": uuid4(),
            "invoice_date": datetime.date(2026, 1, 15),
            "invoice_year": 2026,
            "unit_weight": "U",
            "cct": make_cct("AF0001"),
            "final": True,
        }
        defaults.update(kwargs)
        return InvoiceCommonDetails.objects.create(
            third_party_num=make_society(third_party_num, is_client=False),
            invoice_number=invoice_number,
            **defaults,
        )

    return _factory


@pytest.fixture
def make_edi_validation(db) -> Callable[..., Any]:  # pylint: disable=W0613
    """Fabrique de edi.EdiValidation (période de facturation en cours)"""
    from apps.edi.models import EdiValidation  # pylint: disable=C0415

    def _factory(billing_period: datetime.date = datetime.date(2026, 1, 1), **kwargs: Any):
        defaults = {"final": False}
        defaults.update(kwargs)
        return EdiValidation.objects.create(billing_period=billing_period, **defaults)

    return _factory


@pytest.fixture
def make_edi_import_control(db) -> Callable[..., Any]:  # pylint: disable=W0613
    """Fabrique de edi.EdiImportControl (relevé fournisseur)"""
    from apps.edi.models import EdiImportControl  # pylint: disable=C0415

    def _factory(**kwargs: Any):
        defaults = {"statement_without_tax": Decimal(100), "statement_with_tax": Decimal(120)}
        defaults.update(kwargs)
        return EdiImportControl.objects.create(**defaults)

    return _factory


@pytest.fixture
def make_icon_origin(db) -> Callable[..., Any]:  # pylint: disable=W0613
    """Fabrique idempotente de parameters.IconOriginChoice (origine des lignes)"""
    from apps.parameters.models import IconOriginChoice  # pylint: disable=C0415

    def _factory(origin: int = 4, origin_name: str = "Saisie", icon: str = "edit"):
        return IconOriginChoice.objects.get_or_create(
            origin=origin, defaults={"origin_name": origin_name, "icon": icon}
        )[0]

    return _factory


@pytest.fixture
def make_sale_invoice_detail(make_sale_invoice) -> Callable[..., Any]:
    """Fabrique de lignes invoices.SaleInvoiceDetail"""
    from apps.invoices.models import SaleInvoiceDetail  # pylint: disable=C0415

    def _factory(sale_invoice=None, **kwargs: Any):
        defaults = {
            "import_uuid_identification": uuid4(),
            "axe_bu": "CAHA",
            "axe_prj": "NAF",
            "axe_pro": "OPT",
            "axe_rfa": "NAF",
            "axe_pys": "FR",
            "vat": "001",
            "vat_rate": Decimal("0.2"),
            "vat_regime": "FRA",
            "big_category": "Marchandises",
            "base": "Marchandises",
            "grouping_goods": "Montures",
            "account": "707000",
            "account_od_600": "607000",
            "ranking": 1,
            "gross_unit_price": Decimal(100),
            "net_unit_price": Decimal(100),
            "gross_amount": Decimal(100),
            "net_amount": Decimal(100),
            "vat_amount": Decimal(20),
            "amount_with_vat": Decimal(120),
        }
        defaults.update(kwargs)
        return SaleInvoiceDetail.objects.create(
            uuid_invoice=sale_invoice or make_sale_invoice(), **defaults
        )

    return _factory
