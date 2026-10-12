# pylint: disable=E0401,W0621,C0415
"""FR : Fixtures d'aide aux tests des vues et des tâches de l'app invoices.


     Importées explicitement par les modules de tests : `from apps.invoices.tests.helpers_views import *`
EN : Helper fixtures for invoices views / tasks tests

created at: 2026-10-10
created by: Paulo ALVES
"""

import types
import uuid
from collections.abc import Callable
from typing import Any

import pytest


@pytest.fixture
def make_action(db) -> Callable[..., Any]:  # pylint: disable=W0613
    """Fabrique idempotente de parameters.ActionInProgress"""
    from apps.parameters.models import ActionInProgress

    def _factory(action: str = "insertion_invoices", in_progress: bool = False, **kwargs: Any):
        obj, _ = ActionInProgress.objects.get_or_create(
            action=action, defaults={"in_progress": in_progress, "comment": action, **kwargs}
        )

        if obj.in_progress != in_progress:
            obj.in_progress = in_progress
            obj.save()

        return obj

    return _factory


@pytest.fixture
def make_counter_views(db) -> Callable[..., Any]:  # pylint: disable=W0613
    """Fabrique de compteurs parameters.Counter (+ CounterNums initialisé)"""
    from apps.parameters.models import Counter, CounterNums

    def _factory(name: str = "invoices_num", num: int = 1, **kwargs: Any):
        defaults = {"lpad_num": 5, "separateur": ""}
        defaults.update(kwargs)
        counter, _ = Counter.objects.get_or_create(name=name, defaults=defaults)
        CounterNums.objects.get_or_create(counter=counter, defaults={"num": num})
        return counter

    return _factory


@pytest.fixture
def export_counters(make_counter_views) -> None:
    """Compteurs des fichiers d'export X3 (GASPAR, BICPAR, BISPAR, BISPARD, zip)"""
    # Numéros distincts : les fichiers AC00_<num>.txt des trois compteurs portent le même préfixe
    for num, name in enumerate(
        ("gaspar_num", "bicpar_num", "bispard_num", "bispar_num", "generic"), 1
    ):
        make_counter_views(name, num=num)


@pytest.fixture
def month_period() -> types.SimpleNamespace:
    """Période valide du MonthForm (mois précédent) : value "dte_d_dte_f", dte_d, dte_f"""
    from apps.periods.forms.forms_django.periodes_forms import get_month_choices

    value = get_month_choices()["initial"][0]
    dte_d, dte_f = value.split("_")
    return types.SimpleNamespace(value=value, dte_d=dte_d, dte_f=dte_f)


@pytest.fixture
def make_sse_progress(make_user) -> Callable[..., Any]:
    """Fabrique de core.SSEProgress (jauge de progression des tâches)"""
    from apps.core.models import SSEProgress

    def _factory(job_id: str | None = None, user=None, **kwargs: Any):
        defaults = {
            "task_type": "invoices",
            "total_items": 1,
            "metadata": {"success": [], "failed": []},
        }
        defaults.update(kwargs)
        return SSEProgress.objects.create(
            job_id=job_id or str(uuid.uuid4()), user=user or make_user(), **defaults
        )

    return _factory


@pytest.fixture
def make_email(db) -> Callable[..., Any]:  # pylint: disable=W0613
    """Fabrique de parameters.Email (corps des mails de facturation)"""
    from apps.parameters.models import Email

    def _factory(name: int = 0, **kwargs: Any):
        defaults = {
            "description": "Factures",
            "subject": "Vos factures",
            "email_body": "<p>Bonjour,</p><p>voici vos factures.</p>",
        }
        defaults.update(kwargs)
        return Email.objects.get_or_create(name=name, defaults=defaults)[0]

    return _factory


class FakeTrace:
    """Trace factice renvoyée par les fonctions métier patchées (save enregistré)"""

    def __init__(self, errors: bool = False, comment: str = "", fail_created_by: bool = False):
        self.errors = errors
        self.comment = comment
        self.saved = 0
        self._created_by = None
        self._fail_created_by = fail_created_by

    @property
    def created_by(self):
        return self._created_by

    @created_by.setter
    def created_by(self, value):
        if self._fail_created_by:
            raise TypeError("created_by refusé")

        self._created_by = value

    def save(self):
        self.saved += 1


@pytest.fixture
def celery_recorder(monkeypatch) -> Callable[..., types.SimpleNamespace]:
    """Remplace `celery_app.signature` et `group` d'un module : les signatures sont enregistrées,

    `group(...)()` renvoie un objet dont `.get()` renvoie `results`, `group(...).apply_async()`
    enregistre l'appel. `recorder.signatures` = liste des (name, kwargs).
    """

    def _patch(module, results=None, raise_on_get: BaseException | None = None):
        recorder = types.SimpleNamespace(signatures=[], applied=0, got=0)

        def signature(name, kwargs=None, **_):
            recorder.signatures.append((name, kwargs or {}))
            return (name, kwargs)

        class _Result:
            def get(self, timeout=None):
                recorder.got += 1

                if raise_on_get is not None:
                    raise raise_on_get

                return results if results is not None else [True] * len(recorder.signatures)

        class _Group:
            def __init__(self, *tasks):
                self.tasks = tasks

            def __call__(self):
                return _Result()

            def apply_async(self):
                recorder.applied += 1

        with_attrs: dict[str, Any] = {"group": _Group}

        if hasattr(module, "celery_app"):
            with_attrs["celery_app"] = types.SimpleNamespace(signature=signature)

        for name, value in with_attrs.items():
            monkeypatch.setattr(module, name, value, raising=False)

        return recorder

    return _patch
