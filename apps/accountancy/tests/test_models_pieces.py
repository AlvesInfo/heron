# pylint: disable=E0401,W0621
"""
FR : Tests des modèles de pièces comptables (apps/accountancy/models/pieces.py)
EN : Tests for accounting documents models

created at: 2026-10-10
created by: Paulo ALVES
"""
import uuid

import pytest
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError

from apps.accountancy.models import CodePlanSage, Ecritures, Journaux, Pieces, Transactions

pytestmark = pytest.mark.django_db


def test_creation_chaine_complete(make_ecriture):
    """Une écriture référence pièce, journal et transaction par leurs codes (to_field)"""
    ecriture = make_ecriture("ODANA", type_piece="OD", journal="ODA", transaction="ODANA")

    assert ecriture.type_piece.type_piece == "OD"
    assert ecriture.journal.journal == "ODA"
    assert ecriture.transaction.transaction == "ODANA"
    assert ecriture.type_piece.legislation.code_plan_sage == "FRA"
    assert ecriture.type_x3 == 1
    assert isinstance(ecriture.transaction.uuid_identification, uuid.UUID)


def test_related_names(make_ecriture):
    """Les related_name permettent de remonter les écritures et les pièces d'un plan"""
    ecriture = make_ecriture("ODANA")
    plan = CodePlanSage.objects.get(pk="FRA")

    assert list(plan.piece_code_plan.all()) == [ecriture.type_piece]
    assert list(plan.journal_code_plan.all()) == [ecriture.journal]
    assert list(ecriture.type_piece.type_piece_ecriture.all()) == [ecriture]
    assert list(ecriture.journal.journal_ecriture.all()) == [ecriture]
    assert list(ecriture.transaction.transaction_ecriture.all()) == [ecriture]


def test_colonnes_en_base_portent_le_code(make_ecriture):
    """Les FK sont stockées sous le nom du code Sage (db_column) et non *_id"""
    make_ecriture("ODANA")

    columns = {field.column for field in Ecritures._meta.fields}  # pylint: disable=W0212

    assert {"type_piece", "journal", "transaction"} <= columns
    assert Pieces._meta.get_field("legislation").column == "legislation"  # pylint: disable=W0212


@pytest.mark.parametrize(
    ("model", "field"),
    [(Pieces, "type_piece"), (Journaux, "journal"), (Transactions, "transaction"), (Ecritures, "ecriture")],
)
def test_codes_uniques(make_ecriture, model, field):
    """Les codes de pièce, journal, transaction et écriture sont uniques"""
    ecriture = make_ecriture("ODANA")
    source = ecriture if model is Ecritures else getattr(ecriture, field)
    duplicate = {f.name: getattr(source, f.name) for f in model._meta.fields if f.name != "id"}  # pylint: disable=W0212
    duplicate.pop("uuid_identification", None)

    with transaction.atomic(), pytest.raises(IntegrityError):
        model.objects.create(**duplicate)


@pytest.mark.parametrize("attribute", ["type_piece", "journal", "transaction"])
def test_suppression_protegee_des_dependances(make_ecriture, attribute):
    """Pièce, journal et transaction utilisés par une écriture ne peuvent pas être supprimés"""
    ecriture = make_ecriture("ODANA")

    dependency = getattr(ecriture, attribute)
    dependency_queryset = type(dependency).objects.filter(pk=dependency.pk)

    # NB : FlagsTable.delete (BooleanField) masque Model.delete(), on passe par le QuerySet
    with pytest.raises(ProtectedError):
        dependency_queryset.delete()


def test_suppression_protegee_du_plan(make_ecriture):
    """Le plan de compte utilisé par une pièce ou un journal est protégé"""
    make_ecriture("ODANA")

    plan = CodePlanSage.objects.filter(pk="FRA")

    with pytest.raises(ProtectedError):
        plan.delete()


def test_suppression_ecriture_libere_les_dependances(make_ecriture):
    """Après suppression de l'écriture, la transaction peut être supprimée"""
    ecriture = make_ecriture("ODANA")
    transaction_obj = ecriture.transaction

    Ecritures.objects.filter(pk=ecriture.pk).delete()
    Transactions.objects.filter(pk=transaction_obj.pk).delete()

    assert not Transactions.objects.filter(transaction="ODANA").exists()
    assert Pieces.objects.filter(type_piece="OD").exists()


def test_flagstable_delete_masque_la_methode_delete(make_ecriture):
    """
    Le champ booléen `delete` hérité de FlagsTable masque Model.delete() sur l'instance :
    la suppression doit passer par le QuerySet (comportement structurel à connaître)
    """
    ecriture = make_ecriture("ODANA")

    assert ecriture.delete is False
    assert not callable(ecriture.delete)
