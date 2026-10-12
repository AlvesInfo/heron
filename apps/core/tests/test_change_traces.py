"""Tests de trace_change (apps.core.bin.change_traces) : comparaison avant/après et traçage"""

import pytest
from django.test import RequestFactory

from apps.core.bin.change_traces import trace_change
from apps.core.models import ChangesTrace
from apps.edi.models import EdiImport, EdiValidation

pytestmark = pytest.mark.django_db


@pytest.fixture
def request_with_user(make_user):
    request = RequestFactory().post("/")
    request.user = make_user()
    request.session = {}
    return request


def test_trace_change_rien_modifie(request_with_user, make_edi_validation):
    validation = make_edi_validation(integration=False)

    result = trace_change(
        request_with_user, EdiValidation,
        {"uuid_identification": validation.uuid_identification},
        {"uuid_identification": validation.uuid_identification, "integration": False},
    )

    assert result == (False, "Vous n'avez rien modifié !")
    assert ChangesTrace.objects.count() == 0


def test_trace_change_modifie_et_trace(request_with_user, make_edi_validation):
    validation = make_edi_validation(integration=False)

    result = trace_change(
        request_with_user, EdiValidation,
        {"uuid_identification": validation.uuid_identification},
        {"uuid_identification": validation.uuid_identification, "integration": True},
    )

    validation.refresh_from_db()
    assert result == (True, "L'update à bien été réalisé")
    assert validation.integration is True
    assert validation.modified_by == request_with_user.user
    assert request_with_user.session["level"] == 20
    trace = ChangesTrace.objects.get()
    assert trace.before["integration"] is False
    assert trace.after["integration"] is True
    assert trace.model_name == "edivalidation"


def test_trace_change_enregistrement_absent(request_with_user):
    with pytest.raises(EdiValidation.DoesNotExist):
        trace_change(request_with_user, EdiValidation, {"id": -1}, {"integration": True})


def test_trace_change_instance_de_cle_etrangere(request_with_user, make_edi_import, make_big_category):
    """Une instance passée pour une FK est comparée à la valeur stockée (uuid), pas à l'objet"""
    category = make_big_category("Marchandises")
    line = make_edi_import(big_category=category)

    unchanged = trace_change(
        request_with_user, EdiImport, {"id": line.id}, {"big_category": category}
    )
    assert unchanged == (False, "Vous n'avez rien modifié !")

    other = make_big_category("Services")
    trace_change(request_with_user, EdiImport, {"id": line.id}, {"big_category": other})

    line.refresh_from_db()
    assert line.big_category == other
    assert ChangesTrace.objects.count() == 1
