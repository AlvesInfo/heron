# pylint: disable=E0401,W0621
"""
FR : Tests des schémas djantic de validation des imports Sage de book (forms/forms_djantic/sage.py)
EN : Tests for djantic validation schemas of book Sage imports

created at: 2026-10-11
created by: Paulo ALVES
"""
import datetime
import uuid

import pytest
from pydantic import ValidationError

from apps.book.forms.forms_djantic.sage import (
    BookAdressesSageSchema,
    BookBanksSageSchema,
    BookContactsSageSchema,
    BpcBookSageSchema,
    BprBookSageSchema,
    BpsBookSageSchema,
    CodeContactsSageSchema,
)
from apps.book.models import (
    Address,
    BookAdressesSage,
    BookBanksSage,
    BookContactsSage,
    BpcBookSage,
    BprBookSage,
    BpsBookSage,
    CodeContactsSage,
    Contact,
    Society,
    SocietyBank,
)

WITH_UUID = ["created_at", "modified_at", "uuid_identification"]
WITHOUT_UUID = ["created_at", "modified_at"]


@pytest.mark.parametrize(
    ("schema", "sage_class", "model", "extra"),
    [
        (BprBookSageSchema, BprBookSage, Society, WITHOUT_UUID),
        (BpsBookSageSchema, BpsBookSage, Society, WITHOUT_UUID),
        (BpcBookSageSchema, BpcBookSage, Society, WITHOUT_UUID),
        (BookAdressesSageSchema, BookAdressesSage, Address, WITHOUT_UUID),
        (CodeContactsSageSchema, CodeContactsSage, Contact, WITH_UUID),
        (BookContactsSageSchema, BookContactsSage, Contact, WITH_UUID),
        (BookBanksSageSchema, BookBanksSage, SocietyBank, WITHOUT_UUID),
    ],
)
def test_config_des_schemas(schema, sage_class, model, extra):
    """Chaque schéma cible son modèle et inclut les colonnes du fichier + les champs techniques"""
    assert schema.Config.base_model is sage_class
    assert schema.Config.model is model
    assert schema.Config.include == list(sage_class.get_columns_import()) + extra
    assert set(schema.__fields__) == set(schema.Config.include)


def test_bpr_schema_nettoyage_sage():
    """Tildes supprimés, texte tronqué au max_length, booléens Sage 2/1, dates posées par défaut"""
    validated = BprBookSageSchema(
        third_party_num="  FOUR001 ",
        name="Fournisseur~~Supplier " + "x" * 100,
        short_name="Un nom court beaucoup trop long",
        country="FR",
        currency="",
        is_client="1",
        is_supplier="2",
        is_agent="",
    ).dict()

    assert validated["third_party_num"] == "FOUR001"
    assert validated["name"] == "Fournisseur"
    assert len(validated["short_name"]) == 20
    assert validated["currency"] is None
    assert validated["is_client"] is False
    assert validated["is_supplier"] is True
    assert validated["is_agent"] is False
    assert validated["is_physical_person"] is False
    assert validated["budget_code"] is None
    assert isinstance(validated["created_at"], datetime.datetime)


def test_bpr_schema_pays_obligatoire():
    with pytest.raises(ValidationError) as excinfo:
        BprBookSageSchema(third_party_num="FOUR001")

    assert {error["loc"][0] for error in excinfo.value.errors()} == {"country"}


@pytest.mark.parametrize(
    ("schema", "required"),
    [(BpsBookSageSchema, "payment_condition_supplier"), (BpcBookSageSchema, "payment_condition_client")],
)
def test_schemas_fournisseurs_clients_condition_de_paiement_obligatoire(schema, required):
    """La condition de paiement (auuid posé par le pré-traitement) est obligatoire"""
    auuid = str(uuid.uuid4())
    validated = schema(**{"third_party_num": "FOUR001", required: auuid, "is_supplier": "2"}).dict()

    assert validated[required] == auuid
    assert validated["is_supplier"] is True
    assert validated["is_client"] is False

    with pytest.raises(ValidationError) as excinfo:
        schema(third_party_num="FOUR001")

    assert {error["loc"][0] for error in excinfo.value.errors()} == {required}


def test_adresses_schema():
    validated = BookAdressesSageSchema(
        society="FOUR001", country="FR", default_adress="2", address_code="1", line_01="12 rue~~x", email_01="a@b.fr"
    ).dict()

    assert validated["default_adress"] is True
    assert validated["line_01"] == "12 rue"
    assert validated["web_site"] is None

    with pytest.raises(ValidationError) as excinfo:
        BookAdressesSageSchema(address_code="1")

    assert {error["loc"][0] for error in excinfo.value.errors()} == {"society", "country"}


def test_contacts_schemas_uuid_par_defaut():
    """Les contacts reçoivent un uuid par défaut, le code contact est tronqué à 15"""
    code = CodeContactsSageSchema(society="FOUR001", code="C" * 20, service="Compta", role="").dict()
    contact = BookContactsSageSchema(society="FOUR001", code="C01", country="FR", first_name="Jean", email="jean@acuitis.com").dict()

    assert isinstance(code["uuid_identification"], uuid.UUID)
    assert len(code["code"]) == 15
    assert code["role"] is None
    assert isinstance(contact["uuid_identification"], uuid.UUID)
    assert contact["first_name"] == "Jean"
    assert contact["last_name"] is None
    assert contact["code"] == "C01"

    with pytest.raises(ValidationError) as excinfo:
        BookContactsSageSchema(society="FOUR001", country="FR")

    assert {error["loc"][0] for error in excinfo.value.errors()} == {"code"}


def test_banques_schema():
    validated = BookBanksSageSchema(society="FOUR001", country="FR", account_number="FR76 3000", is_default="1").dict()

    assert validated["account_number"] == "FR76 3000"
    assert validated["is_default"] is False
    assert validated["currency"] is None

    with pytest.raises(ValidationError):
        BookBanksSageSchema(society="FOUR001")
