# pylint: disable=E0401,W0621,C0415
"""FR : Fixtures propres aux tests de l'app validation_purchases (écrans de validation des achats)


EN : Fixtures for validation_purchases app tests

created at: 2026-10-10
created by: Paulo ALVES
"""

import datetime
import types
from collections.abc import Callable
from typing import Any

import pytest


@pytest.fixture
def validation_period(make_edi_validation) -> Any:
    """Période de validation en cours (EdiValidation final=False, janvier 2026)"""
    return make_edi_validation(
        billing_period=datetime.date(2026, 1, 1), billing_date=datetime.date(2026, 1, 31)
    )


@pytest.fixture
def month_period() -> types.SimpleNamespace:
    """Période valide du MonthForm (mois précédent) : value "dte_d_dte_f", dte_d, dte_f"""
    from apps.periods.forms.forms_django.periodes_forms import get_month_choices

    value = get_month_choices()["initial"][0]
    dte_d, dte_f = value.split("_")
    return types.SimpleNamespace(value=value, dte_d=dte_d, dte_f=dte_f)


@pytest.fixture
def excel_io() -> Callable[[Any], Any]:
    """Renvoie une fonction lisant les cellules de la première feuille d'un BytesIO xlsx"""
    import openpyxl

    def _read(file_io):
        file_io.seek(0)
        sheet = openpyxl.load_workbook(file_io).worksheets[0]
        return [[cell.value for cell in row] for row in sheet.iter_rows()]

    return _read


# Fixtures des modules d'aide de l'app (collectées ici, plus d'import dans les tests)
from apps.validation_purchases.tests.helpers_excel import (  # noqa: E402,F401  pylint: disable=W0611,C0413
    bi_maisons_table,
    ko_writer,
    make_edi_row,
    make_purchase_invoice,
    make_sale_rows,
    make_subscription,
)
from apps.validation_purchases.tests.helpers_excel_2 import (  # noqa: E402,F401  pylint: disable=W0611,C0413
    make_ca_client,
    make_purchase_invoice_2,
    make_sale_invoice,
    make_sale_invoice_detail,
    make_supplier_rate,
)
from apps.validation_purchases.tests.helpers_views import (  # noqa: E402,F401  pylint: disable=W0611,C0413
    integration_data,
    make_action,
    stub_excel,
)
