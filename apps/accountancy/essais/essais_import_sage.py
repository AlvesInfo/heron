from pathlib import Path
from apps.core.functions.functions_setups import *
from apps.core.functions.function_imports import ModelFormInsertion
from apps.accountancy.models import CurrencySage
from apps.accountancy.forms.forms_sage import CurrencySageForm


def import_sage(file, model, model_form):
    model_to_insert = ModelFormInsertion(
        file_to_iter=file,
        columns_dict=model.get_columns_import(),
        validator=model_form,
        uniques=CurrencySage.get_uniques(),
    )
    model_to_insert.validate()


def import_sage_z(file, model_form):
    model_to_insert = ModelFormInsertion(
        file_to_iter=file,
        header_line=1,
        columns_dict={
            "currency_current": "currency_current",
            "currency_change": "currency_change",
            "exchange_date": "exchange_date",
            "exchange_type": "exchange_type",
            "exchange_rate": "exchange_rate",
            "exchange_inverse": "exchange_inverse",
            "divider": "divider",
            "modification_date": "modification_date",
        },
        validator=model_form,
        uniques=CurrencySage.get_uniques(),
    )
    model_to_insert.validate()
    print(model_to_insert.errors)


if __name__ == "__main__":
    fichier = Path(r"U:\ARCHIVE\ZBICUR_journalier.heron")
    fichier_z = Path(r"U:\ARCHIVE\ZBICUR_journalier.heronz")
    modele = CurrencySage
    modele_form = CurrencySageForm
    import time
    start = time.time()
    # import_sage(fichier, modele, modele_form)
    print("fin : import_sage -> ", time.time() - start)
    import_sage_z(fichier_z, modele_form)
    start = time.time()
    print("fin : import_sage_z -> ", time.time() - start)
