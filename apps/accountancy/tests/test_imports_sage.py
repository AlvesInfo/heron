# pylint: disable=E0401,W0621,R0913
"""FR : Tests des fonctions d'import des fichiers Sage X3 (apps/accountancy/imports/imports_sage.py)


EN : Tests for Sage X3 import functions

Commentaire:

- Tests unitaires : make_insert (data_flux) est remplacé par un enregistreur (fixture
  fake_make_insert), on vérifie la Trace créée et les paramètres transmis.
- Tests d'intégration (marqueur integration) : la chaîne data_flux réelle est exécutée sur un
  fichier Sage temporaire, en base de test.

created at: 2026-10-10
created by: Paulo ALVES
"""

import csv
import datetime
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

import pytest

from apps.accountancy.forms.forms_djantic.sage import (
    AccountSageSchema,
    AxeSageSchema,
    CategorySageSchema,
    ModeReglementSchema,
    PaymentConditionSchema,
    SectionSageSchema,
    TabDivSageSchema,
    VatRatSageSchema,
    VatRegimeSageSchema,
    VatSageSchema,
)
from apps.accountancy.imports import imports_sage
from apps.accountancy.imports.imports_sage import (
    account_sage,
    axe_sage,
    category_sage_client,
    category_sage_supplier,
    mode_reglement,
    payement_condition,
    section_sage,
    tab_div_sage,
    vat_rat_sage,
    vat_regime_sage,
    vat_sage,
)
from apps.accountancy.models import (
    AccountSage,
    AxeSage,
    CategorySage,
    ModeReglement,
    PaymentCondition,
    SectionSage,
    TabDivSage,
    VatRatSage,
    VatRegimeSage,
    VatSage,
)
from apps.data_flux.models import Trace
from conftest import csv_file

pytestmark = pytest.mark.django_db

APPLICATION_NAME = "accountacy_imports_import_sage"

IMPORT_CASES = [
    (
        account_sage,
        AccountSage,
        AccountSageSchema,
        "AccountSage",
        "Mise à jour Comptes Sage",
        "des Comptes comptables Sage",
        True,
    ),
    (axe_sage, AxeSage, AxeSageSchema, "AxeSage", "Mise à jour Axes Sage", "des Axes Sage", False),
    (
        section_sage,
        SectionSage,
        SectionSageSchema,
        "SectionSage",
        "Mise à jour Sections Sage",
        "des Sections Sage",
        True,
    ),
    (
        vat_regime_sage,
        VatRegimeSage,
        VatRegimeSageSchema,
        "VatRegimeSage",
        "Mise à jour Régimes de Taxes Sage",
        "des Régimes de taxe Sage",
        True,
    ),
    (
        vat_sage,
        VatSage,
        VatSageSchema,
        "VatSage",
        "Mise à jour Taxes Sage",
        "des Taxes Sage",
        False,
    ),
    (
        vat_rat_sage,
        VatRatSage,
        VatRatSageSchema,
        "VatRatSage",
        "Mise à jour Taux de Taxes Sage",
        "des Taux de Taxes Sage",
        False,
    ),
    (
        payement_condition,
        PaymentCondition,
        PaymentConditionSchema,
        "PaymentCondition",
        "Mise à jour Conditions de paiements Sage",
        "des Conditions de paiements Sage",
        False,
    ),
    (
        tab_div_sage,
        TabDivSage,
        TabDivSageSchema,
        "TabDivSage",
        "Mise à jour Tables Diverses Sage",
        "des Tables Diverses Sage",
        False,
    ),
    (
        category_sage_client,
        CategorySage,
        CategorySageSchema,
        "CategorySageClient",
        "Mise à jour Catégories Clients et Fournisseurs Sage",
        "des Catégories Clients Sage",
        False,
    ),
    (
        category_sage_supplier,
        CategorySage,
        CategorySageSchema,
        "CategorySageSupplier",
        "Mise à jour Catégories Clients et Fournisseurs Sage",
        "des Catégories Fournisseurs Sage",
        False,
    ),
]


# UNITAIRES ========================================================================================


@pytest.mark.parametrize(
    (
        "import_function",
        "model",
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
    import_function,
    model,
    validator,
    flow_name,
    trace_name,
    comment_part,
    with_uuid,
):
    """Chaque import crée une Trace nominative et délègue à make_insert avec les bons paramètres"""
    file_path = Path(
        f"/tmp/{model.file_import_sage() if isinstance(model.file_import_sage(), str) else 'ZBICAT.heron'}"
    )

    trace, to_print = import_function(file_path)

    call = next(call for call in fake_make_insert if "model" in call)
    add_fields = call["params_dict_loader"]["add_fields_dict"]

    assert isinstance(trace, Trace)
    assert Trace.objects.filter(pk=trace.pk).exists()
    assert trace.trace_name == trace_name
    assert trace.file_name == file_path.name
    assert trace.application_name == APPLICATION_NAME
    assert trace.flow_name == flow_name
    assert trace.comment == f"import journalier {file_path.name} {comment_part}"
    assert to_print == f"Import : {flow_name}\n\nPas d'erreurs\n"
    assert call["model"] is model
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


@pytest.mark.usefixtures("vat_rates_dataset")
def test_vat_rat_sage_attend_et_corrige_le_taux_011(fake_make_insert):
    """L'import des taux attend 15 s (fichier X3 en cours d'écriture) puis remet la 011 à 0"""
    vat_rat_sage(Path("/tmp/ZBIRATVAT_journalier.heron"))

    assert fake_make_insert[0] == {"sleep": 15}
    assert fake_make_insert[1]["model"] is VatRatSage
    assert set(VatRatSage.objects.filter(vat="011").values_list("rate", flat=True)) == {Decimal(0)}
    assert VatRatSage.objects.filter(vat="001", rate=Decimal(20)).exists()


@pytest.mark.usefixtures("sage_dirs")
def test_mode_reglement_pretraite_le_fichier(fake_make_insert, make_mode_reglement, tmp_path):
    """Le fichier des modes de règlement est enrichi des uuid avant make_insert"""
    existing = make_mode_reglement("CHQ", name="Chèque", short_name="CHQ", legislation="FRA")

    with csv_file(
        tmp_path / "ZBIMODREG_journalier.heron",
        [["CHQ", "Chèque", "CHQ", "FRA"], ["VRT", "Virement", "VRT", "FRA"]],
        quoting=csv.QUOTE_MINIMAL,
    ) as file:
        trace, _ = mode_reglement(file)

        with file.open("r", encoding="utf8", newline="") as transformed:
            rows = list(csv.reader(transformed, delimiter=";"))

    call = fake_make_insert[0]
    assert trace.flow_name == "ModeReglement"
    assert trace.trace_name == "Mise à jour Mode de règlement Sage"
    assert call["model"] is ModeReglement
    assert call["validator"] is ModeReglementSchema
    assert call["source"] == file
    assert "uuid_identification" not in call["params_dict_loader"]["add_fields_dict"]
    assert rows[0] == ["CHQ", "Chèque", "CHQ", "FRA", str(existing.uuid_identification)]
    assert len(rows[1]) == 5


def test_repertoire_de_processing_module():
    """Le module expose le répertoire de processing sous forme de Path"""
    assert isinstance(imports_sage.proccessing_dir, Path)
    assert imports_sage.proccessing_dir.name == "sage"


# INTÉGRATION (chaîne data_flux réelle) ============================================================


@pytest.mark.integration
@pytest.mark.usefixtures("sage_dirs")
def test_integration_axe_sage_insertion_puis_upsert(sage_file):
    """Lecture, validation djantic et upsert réels : création puis mise à jour des axes"""
    file = sage_file(AxeSage, [["BU", "Business~~Unit", "BU"], ["CCT", "Centre de coût", "CCT"]])

    trace, to_print = axe_sage(file)

    assert "Pas d'erreurs" in to_print
    assert trace.errors is False
    assert dict(AxeSage.objects.values_list("axe", "name")) == {
        "BU": "Business",
        "CCT": "Centre de coût",
    }

    file = sage_file(AxeSage, [["BU", "Business Unit renommée", "BU"], ["PRJ", "Projet", "PRJ"]])

    trace, _ = axe_sage(file)

    assert trace.errors is False
    assert AxeSage.objects.count() == 3
    assert AxeSage.objects.get(axe="BU").name == "Business Unit renommée"


@pytest.mark.integration
def test_integration_section_sage_avec_axe_existant(sage_file, make_axe):
    """Les sections s'insèrent sur un axe existant avec les booléens Sage (2 = vrai, 1 = faux)"""
    make_axe("CCT")
    file = sage_file(
        SectionSage,
        [
            ["CCT", "AF0001", "Paris~~Paris", "PAR", "2", "R1", "R2", "2", "ACU"],
            ["CCT", "AF0002", "Lyon", "LYO", "1", "", "", "1", ""],
        ],
    )

    trace, to_print = section_sage(file)

    sections = {s.section: s for s in SectionSage.objects.all()}
    assert trace.errors is False
    assert "Pas d'erreurs" in to_print
    assert sections["AF0001"].name == "Paris"
    assert sections["AF0001"].chargeable is True
    assert sections["AF0001"].active is True
    assert sections["AF0001"].cpy_fcy == "ACU"
    assert sections["AF0002"].chargeable is False
    assert sections["AF0002"].active is False
    assert sections["AF0002"].regroup_01 is None


@pytest.mark.integration
def test_integration_fichier_en_erreur_est_trace(sage_file):
    """Une ligne invalide (valeur trop longue pour le code axe...) est comptée en erreur dans la trace"""
    file = sage_file(
        VatSage,
        [
            ["001", "TVA 20", "20", "FRA", "pas-un-uuid"],
            ["002", "TVA 5.5", "5.5", "FRA", str(uuid4())],
        ],
    )

    trace, to_print = vat_sage(file)

    trace.refresh_from_db()
    assert "Lignes en erreur" in to_print
    assert trace.errors_numbers_records == 1
    assert list(VatSage.objects.values_list("vat", flat=True)) == ["002"]
