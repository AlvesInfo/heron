# pylint: disable=E0401,R0903
"""
FR : Module d'import des modèles de Sage X3
EN : Import module for Sage X3 models

Commentaire:

created at: 2021-09-09
created by: Paulo ALVES

modified at:2021-09-09
modified by: Paulo ALVES
"""
from pathlib import Path

from apps.core.functions.functions_setups import settings
from apps.accountancy.models import (
    AccountSage,
    AxeSage,
    SectionSage,
    VatRegimeSage,
    VatSage,
    VatRatSage,
    PaymentCondition,
    TabDivSage,
    CategorySage,
    CurrencySage,
)
from apps.accountancy.forms import (
    AccountSageForm,
    AxeSageForm,
    SectionSageForm,
    VatRegimeSageForm,
    VatSageForm,
    VatRatSageForm,
    PaymentConditionForm,
    TabDivSageForm,
    CategorySageForm,
    CurrencySageForm,
)


IMPORTS = (
    (AccountSage, AccountSageForm),
    (AxeSage, AxeSageForm),
    (SectionSage, SectionSageForm),
    (VatRegimeSage, VatRegimeSageForm),
    (VatSage, VatSageForm),
    (VatRatSage, VatRatSageForm),
    (PaymentCondition, PaymentConditionForm),
    (TabDivSage, TabDivSageForm),
    (CategorySage, CategorySageForm),
    (CurrencySage, CurrencySageForm),
)


def import_loop():
    for sage_import in IMPORTS:
        model, form = sage_import
        file_test = model.file_import_sage()
        columns = model.get_columns_import()
        import_method = model.get_import()
        sage_dir = settings.ACSENSREP_EM_DIR

        if isinstance(file_test, (str,)):
            file_for_import = sage_dir / file_test
            # import_method(file_for_import, columns)
            print(file_for_import, columns, import_method, form, sep=" - ")
        else:
            for file in file_test:
                file_for_import = sage_dir / file
                # import_method(file_for_import, columns)
                print(file_for_import, columns, import_method, form, sep=" - ")


if __name__ == "__main__":
    import_loop()
    for cls in IMPORTS:
        if hasattr(cls, "model"):
            print(cls.model)
        else:
            print(cls)


"""
# Exemple API bank de france sur les devises taux de change

import http.client

conn = http.client.HTTPSConnection("api.webstat.banque-france.fr")

headers = {
    'X-IBM-Client-Id': "REPLACE_THIS_KEY",
    'accept': "application/json"
    }

conn.request("GET", "/webstat-fr/v1/catalogue/REPLACE_DATASETNAME?format=json", headers=headers)

res = conn.getresponse()
data = res.read()

print(data.decode("utf-8"))
"""
