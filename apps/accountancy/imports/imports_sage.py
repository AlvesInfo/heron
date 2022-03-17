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
)
from apps.book.models import BookBanksSage

import_tuple = (
    AccountSage,
    AxeSage,
    SectionSage,
    VatRegimeSage,
    VatSage,
    VatRatSage,
    PaymentCondition,
    TabDivSage,
    CategorySage,
    BookBanksSage,
)


def import_loop():
    for sage_import in import_tuple:
        file_test = sage_import.file_import_sage()
        columns = sage_import.get_columns_import()
        import_method = sage_import.get_import()
        sage_dir = settings.ACSENSREP_EM_DIR

        if isinstance(file_test, (str,)):
            file_for_import = sage_dir / file_test
            # import_method(file_for_import, columns)
            print(file_for_import, columns, import_method, sep=" - ")
        else:
            for file in file_test:
                file_for_import = sage_dir / file
                # import_method(file_for_import, columns)
                print(file_for_import, columns, import_method, sep=" - ")


if __name__ == "__main__":
    import_loop()
    for cls in import_tuple:
        if hasattr(cls, "model"):
            print(cls.model)
        else:
            print(cls)
