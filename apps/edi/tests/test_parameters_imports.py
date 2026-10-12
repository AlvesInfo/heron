"""
Tests des paramètres d'import des factures fournisseurs (apps/edi/parameters/invoices_imports.py)

created at: 2026-10-10
created by: Paulo ALVES
"""
import pytest

from apps.edi.models import ColumnDefinition, SupplierDefinition
from apps.edi.parameters.invoices_imports import (
    get_columns,
    get_first_line,
    get_loader_params_dict,
)


def test_get_columns_indexes_numeriques_et_noms(make_column_definitions):
    """Les colonnes numériques deviennent des index int, les autres restent des noms"""
    make_column_definitions("Widex", [("invoice_number", "3"), ("libelle", "designation")])

    assert get_columns(ColumnDefinition, "Widex") == {"invoice_number": 3, "libelle": "designation"}


def test_get_columns_respecte_le_ranking(make_supplier_definition):
    # Flux hors instantané de production (la base réutilisée peut le contenir)
    supplier = make_supplier_definition("FluxRanking")
    ColumnDefinition.objects.create(flow_name=supplier, ranking=2, attr_name="b", file_column="1")
    ColumnDefinition.objects.create(flow_name=supplier, ranking=1, attr_name="a", file_column="0")

    assert list(get_columns(ColumnDefinition, "FluxRanking")) == ["a", "b"]


@pytest.mark.usefixtures('db')
def test_get_columns_flux_inconnu():
    assert get_columns(ColumnDefinition, "Inconnu") == {}


def test_get_first_line(make_supplier_definition):
    make_supplier_definition("FluxLigne3", first_line=3)

    assert get_first_line(SupplierDefinition, "FluxLigne3") == 3
    assert get_first_line(SupplierDefinition, "Inconnu") == 1


def test_get_loader_params_dict_valeurs_par_defaut(make_supplier_definition):
    """Les paramètres vides du fournisseur prennent les valeurs csv par défaut"""
    make_supplier_definition(
        "FluxVide", encoding=None, delimiter=None, lineterminator=None, quotechar=None, escapechar=None
    )

    assert get_loader_params_dict(SupplierDefinition, "FluxVide") == {
        "encoding": None,
        "delimiter": ";",
        "lineterminator": "\n",
        "quotechar": '"',
        "escapechar": '"',
    }


def test_get_loader_params_dict_valeurs_renseignees(make_supplier_definition):
    make_supplier_definition(
        "FluxTab", encoding="cp1252", delimiter="\t", lineterminator="\r\n", quotechar="'", escapechar="\\"
    )

    assert get_loader_params_dict(SupplierDefinition, "FluxTab") == {
        "encoding": "cp1252",
        "delimiter": "\t",
        "lineterminator": "\r\n",
        "quotechar": "'",
        "escapechar": "\\",
    }


@pytest.mark.django_db
def test_get_loader_params_dict_flux_inconnu():
    assert get_loader_params_dict(SupplierDefinition, "Inconnu") == {}
