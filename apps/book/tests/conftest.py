# pylint: disable=W0621,E0401,R0913
"""
FR : conftest de l'app book - fabriques propres au répertoire des tiers et fichiers Sage
EN : book app conftest - directory factories and Sage files

Commentaire:

Les fabriques génériques (make_society, make_address, make_supplier_cct, make_cct, make_country,
make_user, logged_client, ajax_client, sage_dirs, make_csv, make_trace, ...) viennent du conftest
racine. Ici : fichiers d'extraction Sage nommés comme les modèles les attendent, doublure de
make_insert pour les tests unitaires des imports, fabriques des statistiques, contacts, banques et
conditions de paiement.

created at: 2026-10-11
created by: Paulo ALVES
"""
from pathlib import Path
from typing import Any
from collections.abc import Callable
from collections.abc import Iterable
from uuid import uuid4

import pytest

from apps.accountancy.models import PaymentCondition
from apps.book.imports import imports_sage
from apps.book.models import Contact, SocietyBank, StatFamillyAxes


# ==================================================================================================
# FICHIERS SAGE ET IMPORTS
# ==================================================================================================


@pytest.fixture
def book_dirs(sage_dirs, monkeypatch: pytest.MonkeyPatch):
    """
    Répertoires Sage temporaires (conftest racine) et répertoire de processing du module
    d'import de book (constante lue à l'import) redirigé vers le même répertoire temporaire.
    """
    monkeypatch.setattr(imports_sage, "proccessing_dir", sage_dirs.processing)
    return sage_dirs


@pytest.fixture
def sage_file(book_dirs, make_csv: Callable[..., Path]) -> Callable[..., Path]:
    """
    Fabrique de fichiers d'extraction Sage X3 (csv ; quoté, CRLF) nommés comme le modèle
    les attend (model.file_import_sage()), déposés par défaut dans le répertoire de processing.
    """

    def _factory(
        model_or_name: Any, rows: Iterable[Iterable[Any]], directory: Path | None = None
    ) -> Path:
        name = model_or_name if isinstance(model_or_name, str) else model_or_name.file_import_sage()
        target_dir = directory or book_dirs.processing
        written = make_csv(name, rows)
        destination = target_dir / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        written.replace(destination)
        return destination

    return _factory


@pytest.fixture
def fake_make_insert(monkeypatch: pytest.MonkeyPatch, book_dirs) -> list[dict[str, Any]]:
    """
    Remplace data_flux.make_insert dans le module d'import de book par un enregistreur d'appels.
    Retourne la liste des appels (dict des arguments).
    """
    calls: list[dict[str, Any]] = []

    def _recorder(model, flow_name, source, trace, validator, params_dict_loader, extend_model=None, **kwargs):
        calls.append(
            {
                "model": model,
                "flow_name": flow_name,
                "source": source,
                "trace": trace,
                "validator": validator,
                "params_dict_loader": params_dict_loader,
                "extend_model": extend_model,
                **kwargs,
            }
        )
        return f"Import : {flow_name}\n\nPas d'erreurs\n"

    monkeypatch.setattr(imports_sage, "make_insert", _recorder)
    return calls


# ==================================================================================================
# FABRIQUES DE MODÈLES
# ==================================================================================================


@pytest.fixture
def make_stat_familly(db) -> Callable[..., StatFamillyAxes]:  # pylint: disable=W0613
    """Fabrique de familles statistiques (réutilise la famille si elle existe)"""

    def _factory(name: str = "ACUITIS", **kwargs: Any) -> StatFamillyAxes:
        defaults = {"description": f"Statistique {name}", "regex_bool": False}
        defaults.update(kwargs)
        return StatFamillyAxes.objects.get_or_create(name=name, defaults=defaults)[0]

    return _factory


@pytest.fixture
def make_payment_condition(db) -> Callable[..., PaymentCondition]:  # pylint: disable=W0613
    """Fabrique de conditions de paiement Sage (auuid aléatoire, réutilise le code s'il existe)"""

    def _factory(code: str = "30J", **kwargs: Any) -> PaymentCondition:
        existing = PaymentCondition.objects.filter(code=code).first()

        if existing:
            return existing

        defaults = {"name": f"Paiement {code}", "short_name": code[:20], "auuid": str(uuid4())}
        defaults.update(kwargs)
        return PaymentCondition.objects.create(code=code, **defaults)

    return _factory


@pytest.fixture
def make_contact(make_society) -> Callable[..., Contact]:
    """Fabrique de contacts Sage d'un tiers"""

    def _factory(society=None, code: str = "C01", **kwargs: Any) -> Contact:
        return Contact.objects.create(society=society or make_society(), code=code, **kwargs)

    return _factory


@pytest.fixture
def make_society_bank(make_society) -> Callable[..., SocietyBank]:
    """Fabrique de comptes bancaires Sage d'un tiers"""

    def _factory(society=None, account_number: str = "FR7600000001", **kwargs: Any) -> SocietyBank:
        return SocietyBank.objects.create(
            society=society or make_society(), account_number=account_number, **kwargs
        )

    return _factory


@pytest.fixture
def automate(make_user):
    """Utilisateur automate, créateur des identifiants cct générés par add_news_cct_sage"""
    return make_user(email="automate@acuitis.com", username="automate")
