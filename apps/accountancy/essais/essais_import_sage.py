from pathlib import Path

from apps.core.functions.function_imports import ModelFormInsertion, IterFileToInsert
from apps.accountancy.models import CurrencySage
from apps.accountancy.forms.forms_django.forms_sage import CurrencySageForm


def import_sage(file, model, model_form):
    model_to_insert = ModelFormInsertion(
        file_to_iter=file,
        columns_dict=model.get_columns_import(),
        validator=model_form,
        uniques=CurrencySage.get_uniques(),
    )
    model_to_insert.validate()


def import_sage_z(file, model_form):
    with ModelFormInsertion(
        file_to_iter=file,
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
    ) as model_to_insert:
        model_to_insert.validate()
        print(model_to_insert.errors)


columns_dict = (
    {
        "currency_current": 0,
        "currency_change": 1,
        "exchange_date": 2,
        "exchange_type": 3,
        "exchange_rate": 4,
        "exchange_inverse": 5,
        "divider": 6,
        "modification_date": 7,
    },
)

columns_dict_z = (
    {
        "currency_current": None,
        "currency_change": None,
        "exchange_date": None,
        "exchange_type": None,
        "exchange_rate": None,
        "exchange_inverse": None,
        "divider": None,
        "modification_date": None,
    },
)


def essai_iter_file_to_insert(file):
    from apps.accountancy.validations.djantic_sage import CurrencySageSchema
    from pydantic import ValidationError

    with IterFileToInsert(
        file_to_iter=file,
        first_line=1,
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
        add_fields_dict={"created_at": "101122"},
    ) as file_to_insert:
        for i, row in enumerate(file_to_insert.get_chunk_dict_rows(), 1):
            print(i, row)
            try:
                t = CurrencySageSchema(**row)
            except ValidationError as except_error:
                print(i + 1, except_error.errors())
                # raise Exception from errors
            else:
                # ...
                print(i + 1, t.dict())
                # try:
                # upsert = PostresDjangoUpsert(
                #     model=CurrencySage, fields_dict=t.dict(), cnx=connection
                # )
                # upsert.set_direct_insertion()
                # except IntegrityError:
                #     print("le champ existe déjà")


if __name__ == "__main__":
    fichier = Path(r"U:\ARCHIVE\ZBICUR_journalier.heron")
    fichier_z = Path(r"U:\ARCHIVE\ZBICUR_journalier.heronz")
    modele = CurrencySage
    modele_form = CurrencySageForm
    import time

    start = time.time()
    # import_sage(fichier, modele, modele_form)
    print("fin : import_sage -> ", time.time() - start)
    # import_sage_z(fichier_z, modele_form)
    essai_iter_file_to_insert(fichier_z)
    start = time.time()
    print("fin : import_sage_z -> ", time.time() - start)
