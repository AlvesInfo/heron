# pylint: disable=E0401,W0621,R0913
"""FR : Tests des fonctions d'import des fichiers Sage X3 de book (apps/book/imports/imports_sage.py)


EN : Tests for book Sage X3 import functions

Commentaire:

- Tests unitaires : make_insert (data_flux) est remplacé par un enregistreur (fixture
  fake_make_insert), on vérifie la Trace créée, les paramètres transmis et les pré/post-traitements.
- Tests d'intégration (marqueur integration) : la chaîne data_flux réelle est exécutée sur un
  fichier Sage temporaire, en base de test.

created at: 2026-10-11
created by: Paulo ALVES
"""

import csv
import datetime
from pathlib import Path
from uuid import uuid4

import pytest

from apps.book.forms.forms_djantic.sage import (
    BookAdressesSageSchema,
    BookBanksSageSchema,
    BookContactsSageSchema,
    BpcBookSageSchema,
    BprBookSageSchema,
    BpsBookSageSchema,
    CodeContactsSageSchema,
)
from apps.book.imports import imports_sage
from apps.book.imports.imports_sage import (
    adress_sage,
    bank_sage,
    bpc_sage,
    bpr_sage,
    bps_sage,
    code_contact_sage,
    contact_sage,
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
from apps.data_flux.models import Trace

pytestmark = pytest.mark.django_db

APPLICATION_NAME = "book_imports_import_sage"

IMPORT_CASES = [
    (
        bpr_sage,
        BprBookSage,
        BprBookSageSchema,
        "bpr_sage",
        "Mise à jour Tiers BPR Sage",
        "des Tiers Sage",
        False,
    ),
    (
        bps_sage,
        BpsBookSage,
        BpsBookSageSchema,
        "bps_sage",
        "Mise à jour Tiers BPS Sage",
        "des Tiers Fournisseurs Sage",
        False,
    ),
    (
        bpc_sage,
        BpcBookSage,
        BpcBookSageSchema,
        "bpc_sage",
        "Mise à jour Tiers BPC Sage",
        "des Tiers Clients Sage",
        False,
    ),
    (
        adress_sage,
        BookAdressesSage,
        BookAdressesSageSchema,
        "adress_sage",
        "Mise à jour Adresses Tiers BPC Sage",
        "des Adresses Tiers Sage",
        False,
    ),
    (
        code_contact_sage,
        CodeContactsSage,
        CodeContactsSageSchema,
        "code_contact_sage",
        "Mise à jour Codes Contacts Tiers BPC Sage",
        "des Codes Contacts Tiers Sage",
        True,
    ),
    (
        contact_sage,
        BookContactsSage,
        BookContactsSageSchema,
        "contact_sage",
        "Mise à jour Contacts Tiers BPC Sage",
        "des Contacts Tiers Sage",
        True,
    ),
    (
        bank_sage,
        BookBanksSage,
        BookBanksSageSchema,
        "bank_sage",
        "Mise à jour Banques Tiers BPC Sage",
        "des Banques Tiers Sage",
        False,
    ),
]


def _read_rows(path):
    with path.open("r", encoding="utf8", newline="") as file:
        return list(csv.reader(file, delimiter=";", quotechar='"'))


# UNITAIRES ========================================================================================


@pytest.mark.parametrize(
    (
        "import_function",
        "sage_class",
        "validator",
        "flow_name",
        "trace_name",
        "comment_part",
        "with_uuid",
    ),
    IMPORT_CASES,
)
def test_fonctions_import_creent_la_trace_et_appellent_make_insert(
    fake_make_insert,
    sage_file,
    make_society,
    import_function,
    sage_class,
    validator,
    flow_name,
    trace_name,
    comment_part,
    with_uuid,
):
    """Chaque import crée une Trace nominative et délègue à make_insert avec les bons paramètres"""
    make_society("FOUR001", is_client=False)
    file_path = sage_file(sage_class, [["FOUR001", "30J", "FRA", "FOU"]])

    trace, to_print = import_function(file_path)

    call = fake_make_insert[0]
    add_fields = call["params_dict_loader"]["add_fields_dict"]

    assert isinstance(trace, Trace)
    assert Trace.objects.filter(pk=trace.pk).exists()
    assert trace.trace_name == trace_name
    assert trace.file_name == file_path.name
    assert trace.application_name == APPLICATION_NAME
    assert trace.flow_name == flow_name
    assert trace.comment == f"import journalier {file_path.name} {comment_part}"
    assert to_print == f"Import : {flow_name}\n\nPas d'erreurs\n"
    assert call["model"] is sage_class.model
    assert call["extend_model"] is sage_class
    assert call["validator"] is validator
    assert call["flow_name"] == flow_name
    assert call["source"] == file_path
    assert call["trace"] is trace
    assert call["params_dict_loader"]["trace"] is trace
    assert isinstance(add_fields["created_at"], datetime.datetime)
    assert isinstance(add_fields["modified_at"], datetime.datetime)
    assert ("uuid_identification" in add_fields) is with_uuid

    if with_uuid:
        assert add_fields["uuid_identification"] == (uuid4, {})


def test_bpr_sage_lance_le_post_traitement(fake_make_insert, sage_file, make_society):
    """Après l'import des tiers, les drapeaux null sont remis aux défauts"""
    make_society("TIERS01", name=None, integrable=None)
    file_path = sage_file(BprBookSage, [["TIERS01"]])

    bpr_sage(file_path)

    society = Society.objects.get(third_party_num="TIERS01")
    assert len(fake_make_insert) == 1
    assert (society.name, society.integrable) == ("TIERS01", True)
    assert _read_rows(file_path) == [["TIERS01"]]


@pytest.mark.parametrize(
    ("import_function", "sage_class"), [(bps_sage, BpsBookSage), (bpc_sage, BpcBookSage)]
)
def test_bps_bpc_sage_pretraitent_le_fichier(
    fake_make_insert, sage_file, make_society, make_payment_condition, import_function, sage_class
):
    """Le fichier est enrichi des auuid de conditions de paiement et des types de tiers"""
    make_society("FOUR001", is_client=False, is_supplier=True)
    condition = make_payment_condition("30J")
    file_path = sage_file(
        sage_class, [["FOUR001", "30J", "FRA", "FOU"], ["ABSENT", "30J", "FRA", "X"]]
    )

    import_function(file_path)

    assert fake_make_insert[0]["source"] == file_path
    assert _read_rows(file_path) == [
        ["FOUR001", condition.auuid, "FRA", "FOU", "1", "1", "1", "2", "1", "1", "1", "1", "1"]
    ]


@pytest.mark.parametrize(
    ("import_function", "sage_class"),
    [
        (adress_sage, BookAdressesSage),
        (code_contact_sage, CodeContactsSage),
        (contact_sage, BookContactsSage),
    ],
)
def test_imports_par_tiers_filtrent_les_tiers_inconnus(
    fake_make_insert, sage_file, make_society, import_function, sage_class
):
    make_society("FOUR001", is_client=False)
    file_path = sage_file(sage_class, [["FOUR001", "x"], ["ABSENT", "y"]])

    import_function(file_path)

    assert len(fake_make_insert) == 1
    assert _read_rows(file_path) == [["FOUR001", "x"]]


def test_bank_sage_dedoublonne_le_fichier(fake_make_insert, sage_file, make_society):
    make_society("FOUR001", is_client=False)
    file_path = sage_file(
        BookBanksSage, [["FOUR001", "FR01", "a"], ["FOUR001", "FR01", "b"], ["ABSENT", "FR01", "c"]]
    )

    bank_sage(file_path)

    assert len(fake_make_insert) == 1
    assert _read_rows(file_path) == [["FOUR001", "FR01", "a"]]


def test_repertoire_de_processing_module():
    """Le module expose le répertoire de processing sous forme de Path"""
    assert isinstance(imports_sage.proccessing_dir, Path)
    assert imports_sage.proccessing_dir.name == "sage"


# INTÉGRATION (chaîne data_flux réelle) ============================================================


def _bpr_row(third_party_num, name, **flags):
    """Ligne du fichier ZBIBPR : 22 colonnes, booléens Sage 2 = vrai / 1 = faux"""
    booleans = [
        "is_client",
        "is_agent",
        "is_prospect",
        "is_supplier",
        "is_various",
        "is_service_provider",
        "is_transporter",
        "is_contractor",
    ]
    return [
        third_party_num,
        name,
        name[:20],
        f"Raison {name}",
        "12345678900011",
        "FR123",
        "V1",
        "4773A",
        "EUR",
        "FR",
        "FRA",
        *["2" if flags.get(flag) else "1" for flag in booleans],
        "B01",
        "PA",
        "2" if flags.get("is_physical_person") else "1",
    ]


@pytest.mark.integration
def test_integration_bpr_sage_insertion_puis_upsert(sage_file, make_country):
    """Lecture, validation djantic et upsert réels : création puis mise à jour des tiers"""
    make_country("FR")
    file = sage_file(
        BprBookSage,
        [
            _bpr_row("FOUR001", "Fournisseur~~Supplier", is_supplier=True),
            _bpr_row("CLI001", "Client", is_client=True, is_physical_person=True),
        ],
    )

    trace, to_print = bpr_sage(file)

    four = Society.objects.get(third_party_num="FOUR001")
    client = Society.objects.get(third_party_num="CLI001")
    assert "Pas d'erreurs" in to_print
    assert trace.errors is False
    assert (four.name, four.short_name, four.is_supplier, four.is_client) == (
        "Fournisseur",
        "Fournisseur",
        True,
        False,
    )
    assert (client.is_client, client.is_physical_person, client.country.country) == (
        True,
        True,
        "FR",
    )
    assert (four.integrable, four.chargeable, four.od_ana) == (True, True, False)

    file = sage_file(BprBookSage, [_bpr_row("FOUR001", "Fournisseur renommé", is_supplier=True)])

    trace, _ = bpr_sage(file)

    assert trace.errors is False
    assert Society.objects.count() == 2
    assert Society.objects.get(third_party_num="FOUR001").name == "Fournisseur renommé"


@pytest.mark.integration
def test_integration_bps_sage_met_a_jour_les_fournisseurs(
    sage_file, make_society, make_payment_condition
):
    """Condition de paiement traduite en auuid et types de tiers conservés depuis le référentiel"""
    make_society("FOUR001", is_client=False, is_supplier=True, name="Fournisseur")
    condition = make_payment_condition("30J")
    file = sage_file(BpsBookSage, [["FOUR001", "30J", "FRA", "FOU"], ["ABSENT", "30J", "FRA", "X"]])

    trace, to_print = bps_sage(file)

    four = Society.objects.get(third_party_num="FOUR001")
    assert "Pas d'erreurs" in to_print
    assert trace.errors is False
    assert four.payment_condition_supplier == condition
    assert (four.vat_sheme_supplier, four.account_supplier_code) == ("FRA", "FOU")
    assert (four.is_supplier, four.is_client, four.name) == (True, False, "Fournisseur")
    assert Society.objects.count() == 1


@pytest.mark.integration
def test_integration_bpc_sage_met_a_jour_les_clients(
    sage_file, make_society, make_payment_condition
):
    make_society("CLI001", is_client=True)
    condition = make_payment_condition("COMPTANT")
    file = sage_file(BpcBookSage, [["CLI001", "INCONNU", "FRA", "CLI"]])

    trace, _ = bpc_sage(file)

    client = Society.objects.get(third_party_num="CLI001")
    assert trace.errors is False
    assert client.payment_condition_client == condition
    assert client.account_client_code == "CLI"
    assert client.is_client is True


@pytest.mark.integration
def test_integration_adress_sage_recopie_l_adresse_principale(
    sage_file, make_society, make_country
):
    """Adresses insérées, puis l'adresse 1 est recopiée sur le tiers par le post-traitement"""
    make_country("FR")
    society = make_society("FOUR001", is_client=False)
    row = [
        "FOUR001",
        "2",
        "1",
        "SIEGE",
        "",
        "Batiment A",
        "None",
        "12 rue de la Paix",
        "",
        "75001",
        "Paris",
        "FR",
        "0102030405",
        "None",
        "",
        "",
        "",
        "contact@acuitis.com",
        "",
        "",
        "",
        "",
        "www.acuitis.com",
    ]
    file = sage_file(BookAdressesSage, [row, ["ABSENT", *row[1:]]])

    trace, to_print = adress_sage(file)

    society.refresh_from_db()
    address = Address.objects.get(society=society, address_code="1")
    assert "Pas d'erreurs" in to_print
    assert trace.errors is False
    assert Address.objects.count() == 1
    assert (address.default_adress, address.line_02, address.phone_number_02) == (True, None, None)
    assert (society.immeuble, society.adresse, society.ville) == (
        "Batiment A",
        "12 rue de la Paix",
        "Paris",
    )
    assert (society.email_01, society.phone_number_01, society.pays.country) == (
        "contact@acuitis.com",
        "0102030405",
        "FR",
    )


@pytest.mark.integration
def test_integration_code_contact_sage(sage_file, make_society):
    society = make_society("FOUR001", is_client=False)
    file = sage_file(
        CodeContactsSage,
        [["FOUR001", "C01", "Comptabilité", "Resp"], ["FOUR001", "C02", "Achats", ""]],
    )

    trace, to_print = code_contact_sage(file)

    contacts = {contact.code: contact for contact in Contact.objects.filter(society=society)}
    assert "Pas d'erreurs" in to_print
    assert trace.errors is False
    assert set(contacts) == {"C01", "C02"}
    assert (contacts["C01"].service, contacts["C01"].role) == ("Comptabilité", "Resp")
    assert contacts["C02"].role is None
    assert contacts["C01"].uuid_identification != contacts["C02"].uuid_identification


@pytest.mark.integration
def test_integration_contact_sage_complete_les_codes_contacts(
    sage_file, make_society, make_country
):
    """Les contacts CRM s'alignent sur les codes contacts (clé tiers / code) sans écraser service et rôle"""
    make_country("FR")
    society = make_society("FOUR001", is_client=False)
    code_contact_sage(sage_file(CodeContactsSage, [["FOUR001", "C01", "Comptabilité", "Resp"]]))
    file = sage_file(
        BookContactsSage,
        [
            [
                "FOUR001",
                "C01",
                "M.",
                "Jean",
                "Dupont",
                "FRA",
                "CAD",
                "12 rue",
                "",
                "",
                "",
                "75001",
                "Paris",
                "FR",
                "01",
                "06",
                "jean@acuitis.com",
            ],
            [
                "FOUR001",
                "C02",
                "Mme",
                "Anne",
                "Martin",
                "FRA",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "FR",
                "",
                "",
                "anne@acuitis.com",
            ],
        ],
    )

    trace, to_print = contact_sage(file)

    contacts = {contact.code: contact for contact in Contact.objects.filter(society=society)}
    assert "Pas d'erreurs" in to_print
    assert trace.errors is False
    assert set(contacts) == {"C01", "C02"}
    assert (contacts["C01"].first_name, contacts["C01"].last_name, contacts["C01"].email) == (
        "Jean",
        "Dupont",
        "jean@acuitis.com",
    )
    assert (contacts["C01"].service, contacts["C01"].role) == ("Comptabilité", "Resp")
    assert (contacts["C02"].civility, contacts["C02"].service) == ("Mme", None)


@pytest.mark.integration
def test_integration_bank_sage(sage_file, make_society, make_country):
    make_country("FR")
    society = make_society("FOUR001", is_client=False)
    file = sage_file(
        BookBanksSage,
        [
            [
                "FOUR001",
                "FR7600001",
                "1",
                "Acuitis",
                "BNP",
                "",
                "",
                "",
                "FR76",
                "BNPAFRPP",
                "FR",
                "EUR",
                "2",
            ],
            ["FOUR001", "FR7600001", "1", "Doublon", "", "", "", "", "", "", "FR", "EUR", "1"],
        ],
    )

    trace, to_print = bank_sage(file)

    bank = SocietyBank.objects.get(society=society)
    assert "Pas d'erreurs" in to_print
    assert trace.errors is False
    assert (bank.payee, bank.bic_code, bank.is_default, bank.country.country) == (
        "Acuitis",
        "BNPAFRPP",
        True,
        "FR",
    )


@pytest.mark.integration
def test_integration_fichier_en_erreur_est_trace(sage_file, make_country):
    """Une ligne invalide (numéro de tiers vide) est comptée en erreur, les autres sont insérées"""
    make_country("FR")
    row = _bpr_row("", "Fournisseur")
    file = sage_file(BprBookSage, [row, _bpr_row("FOUR002", "Autre")])

    trace, to_print = bpr_sage(file)

    trace.refresh_from_db()
    assert "Lignes en erreur" in to_print
    assert trace.errors_numbers_records == 1
    assert list(Society.objects.values_list("third_party_num", flat=True)) == ["FOUR002"]
