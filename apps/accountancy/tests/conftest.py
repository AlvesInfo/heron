# pylint: disable=W0621,E0401,R0913
"""
FR : conftest de l'app accountancy - fabriques de modèles Sage et fichiers d'import
EN : accountancy app conftest - Sage model factories and import files

Commentaire:

Toutes les fabriques sont des fixtures retournant des fonctions (pas de classes), avec des
valeurs par défaut cohérentes, surchargeables par kwargs. Les fixtures génériques et les
référentiels partagés (make_axe, make_section, make_cct, make_vat, make_account, make_code_plan,
make_tab_div, sage_dirs, make_csv, make_trace, patch_module, ...) viennent du conftest racine.

created at: 2026-10-10
created by: Paulo ALVES
"""
import datetime
import itertools
from decimal import Decimal
from pathlib import Path
from typing import Any
from collections.abc import Callable
from collections.abc import Iterable
from uuid import uuid4

import pytest

from apps.accountancy.models import (
    CategorySage,
    CodePlanSage,
    CurrencySage,
    Ecritures,
    Journaux,
    ModeReglement,
    PaymentCondition,
    Pieces,
    Transactions,
    VatRatSage,
    VatRegimeSage,
    VatSage,
)

_COUNTER = itertools.count(1)


def _next_code(prefix: str) -> str:
    """Code unique et lisible pour les champs uniques"""
    return f"{prefix}{next(_COUNTER):04d}"


# ==================================================================================================
# FABRIQUES DE MODÈLES
# ==================================================================================================


@pytest.fixture
def make_vat_rat(make_vat: Callable[..., VatSage]) -> Callable[..., VatRatSage]:
    """Fabrique de VatRatSage (taux à une date de début)"""

    def _factory(
        vat: str = "001",
        vat_start_date: datetime.date = datetime.date(2014, 1, 1),
        rate: Decimal | str = Decimal("20"),
        vat_regime: str = "FRA",
        **kwargs: Any,
    ) -> VatRatSage:
        defaults = {"auuid": uuid4(), "exoneration": False}
        defaults.update(kwargs)
        return VatRatSage.objects.create(
            vat=make_vat(vat, vat_regime),
            vat_start_date=vat_start_date,
            rate=Decimal(str(rate)),
            vat_regime=vat_regime,
            **defaults,
        )

    return _factory


@pytest.fixture
def vat_rates_dataset(make_vat_rat: Callable[..., VatRatSage]) -> dict[str, list[VatRatSage]]:
    """
    Jeu de taux de TVA historisés :
        001 : 19.6 % depuis 2000, 20 % depuis 2014 (régime FRA)
        002 : 5.5 % depuis 2000 (régime FRA)
        011 : 20 % depuis 2014 (régime INT, tva intracommunautaire)
    """
    return {
        "001": [
            make_vat_rat("001", datetime.date(2000, 1, 1), "19.6"),
            make_vat_rat("001", datetime.date(2014, 1, 1), "20"),
        ],
        "002": [make_vat_rat("002", datetime.date(2000, 1, 1), "5.5")],
        "011": [make_vat_rat("011", datetime.date(2014, 1, 1), "20", vat_regime="INT")],
    }


@pytest.fixture
def make_vat_regime(db) -> Callable[..., VatRegimeSage]:  # pylint: disable=W0613
    """Fabrique de VatRegimeSage"""

    def _factory(vat_regime: str = "FRA", legislation: str = "FRA", **kwargs: Any) -> VatRegimeSage:
        defaults = {"name": f"Régime {vat_regime}", "short_name": vat_regime}
        defaults.update(kwargs)
        return VatRegimeSage.objects.create(
            vat_regime=vat_regime, legislation=legislation, **defaults
        )

    return _factory


@pytest.fixture
def make_mode_reglement(db) -> Callable[..., ModeReglement]:  # pylint: disable=W0613
    """Fabrique de ModeReglement (uuid_identification obligatoire, sans défaut sur le modèle)"""

    def _factory(code: str = "CHQ", **kwargs: Any) -> ModeReglement:
        defaults = {
            "name": f"Mode {code}",
            "short_name": code,
            "legislation": "FRA",
            "uuid_identification": uuid4(),
        }
        defaults.update(kwargs)
        return ModeReglement.objects.create(code=code, **defaults)

    return _factory


@pytest.fixture
def make_payment_condition(db) -> Callable[..., PaymentCondition]:  # pylint: disable=W0613
    """Fabrique de PaymentCondition (une ligne = une échéance)"""

    def _factory(code: str = "30J", **kwargs: Any) -> PaymentCondition:
        defaults = {
            "name": f"Condition {code}",
            "short_name": code,
            "mode": "VRT",
            "percent_at_term": Decimal("100"),
            "paiement_type": "VIREMENT",
            "offset_month": 0,
            "offset_days": 30,
            "end_month": "1",
            "mont_echeance_min": Decimal("0"),
            "auuid": _next_code(f"{code}-"),
        }
        defaults.update(kwargs)
        return PaymentCondition.objects.create(code=code, **defaults)

    return _factory


@pytest.fixture
def make_category(db) -> Callable[..., CategorySage]:  # pylint: disable=W0613
    """Fabrique de CategorySage"""

    def _factory(initial: str = "C", code: str | None = None, **kwargs: Any) -> CategorySage:
        code = code or _next_code("C")[:5]
        defaults = {"name": f"Catégorie {code}", "short_name": code, "cur": "EUR"}
        defaults.update(kwargs)
        return CategorySage.objects.create(initial=initial, code=code, **defaults)

    return _factory


@pytest.fixture
def make_currency(db) -> Callable[..., CurrencySage]:  # pylint: disable=W0613
    """Fabrique de CurrencySage"""

    def _factory(
        currency_current: str = "EUR",
        currency_change: str = "USD",
        exchange_date: datetime.date = datetime.date(2024, 1, 1),
        **kwargs: Any,
    ) -> CurrencySage:
        defaults = {
            "exchange_rate": Decimal("1.1"),
            "exchange_inverse": Decimal("0.9"),
            "modification_date": exchange_date,
        }
        defaults.update(kwargs)
        return CurrencySage.objects.create(
            currency_current=currency_current,
            currency_change=currency_change,
            exchange_date=exchange_date,
            **defaults,
        )

    return _factory


@pytest.fixture
def make_ecriture(make_code_plan: Callable[..., CodePlanSage]) -> Callable[..., Ecritures]:
    """Fabrique d'Ecritures avec toute sa chaîne de dépendances (plan, pièce, journal, transaction)"""

    def _factory(ecriture: str = "ODANA", legislation: str = "FRA", **kwargs: Any) -> Ecritures:
        plan = make_code_plan(legislation)
        piece = Pieces.objects.get_or_create(
            type_piece=kwargs.pop("type_piece", "OD"), defaults={"legislation": plan}
        )[0]
        journal = Journaux.objects.get_or_create(
            journal=kwargs.pop("journal", "ODA"), defaults={"legislation": plan}
        )[0]
        transaction = Transactions.objects.get_or_create(
            transaction=kwargs.pop("transaction", "ODANA")
        )[0]
        defaults = {"type_x3": 1, "description": f"Ecriture {ecriture}"}
        defaults.update(kwargs)
        return Ecritures.objects.create(
            ecriture=ecriture,
            type_piece=piece,
            journal=journal,
            transaction=transaction,
            **defaults,
        )

    return _factory


# ==================================================================================================
# FICHIERS SAGE ET DOUBLURES D'IMPORT
# ==================================================================================================


@pytest.fixture
def sage_file(sage_dirs, make_csv: Callable[..., Path]) -> Callable[..., Path]:
    """
    Fabrique de fichiers d'extraction Sage X3 (csv ; quoté, CRLF) nommés comme le modèle
    les attend (model.file_import_sage()), déposés par défaut dans le répertoire de processing.
    """

    def _factory(
        model_or_name: Any, rows: Iterable[Iterable[Any]], directory: Path | None = None
    ) -> Path:
        name = model_or_name

        if not isinstance(model_or_name, str):
            name = model_or_name.file_import_sage()

            if isinstance(name, tuple):
                name = name[0]

        target_dir = directory or sage_dirs.processing
        written = make_csv(name, rows)
        destination = target_dir / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        written.replace(destination)
        return destination

    return _factory


@pytest.fixture
def fake_make_insert(monkeypatch: pytest.MonkeyPatch) -> list[dict[str, Any]]:
    """
    Remplace data_flux.make_insert dans le module d'import par un enregistreur d'appels
    et neutralise time.sleep. Retourne la liste des appels (dict des arguments).
    """
    from apps.accountancy.imports import imports_sage  # pylint: disable=C0415

    calls: list[dict[str, Any]] = []

    def _recorder(model, flow_name, source, trace, validator, params_dict_loader, **kwargs):
        calls.append(
            {
                "model": model,
                "flow_name": flow_name,
                "source": source,
                "trace": trace,
                "validator": validator,
                "params_dict_loader": params_dict_loader,
                **kwargs,
            }
        )
        return f"Import : {flow_name}\n\nPas d'erreurs\n"

    monkeypatch.setattr(imports_sage, "make_insert", _recorder)
    monkeypatch.setattr(imports_sage.time, "sleep", lambda seconds: calls.append({"sleep": seconds}))
    return calls
