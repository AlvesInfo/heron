from io import StringIO
import csv

from apps.core.functions.functions_setups import connections

from apps.accountancy.models.sage import (
    AccountSage,
    CategorySage,
    CctSage,
    CodePlanSage,
    CurrencySage,
    PaymentCondition,
    TabDivSage,
    VatRatSage,
    VatRegimeSage,
    VatSage,
)
from apps.accountancy.models.sage_axes_sections import (
    AxeSage,
    SectionSage,
)
from apps.articles.models import (
    Article,
    ArticleUpdate,
    SalePriceHistory,
    SellingPrice,
    Subscription,
    SubscriptionArticle,
)
from apps.book.models import (
    Address,
    Contact,
    Nature,
    Society,
    SocietyBank,
    SupplierCct,
    SupplierArticleAxePro,
    FamilleAxePro,
)
from apps.centers_clients.models import (
    Maison,
    MaisonBi,
    ClientFamilly,
    Contact as ClientContact,
    ContactExchange,
    DocumentsSubscription,
    MaisonSupllierExclusion,
    MaisonSupplierIdentifier,
)
from apps.centers_purchasing.models import (
    PrincipalCenterPurchase,
    ChildCenterPurchase,
    Signboard,
    SignboardModel,
    Action,
    SignboardModelTranslate,
    Translation,
    TranslationParamaters,
)
from apps.edi.models import SupplierDefinition, ColumnDefinition
from apps.parameters.models import (
    Category,
    CategoryModelInvoice,
    SubCategory,
    SubFamilly,
    ActionPermission,
    AddressCode,
    Counter,
    Parameters,
    Periodicity,
    SalePriceCategory,
    SendFiles,
    SendFilesMail,
)

MODELS_ACCOUNTANCY = (
    AccountSage,
    CategorySage,
    CodePlanSage,
    CurrencySage,
    FamilleAxePro,
    PaymentCondition,
    TabDivSage,
    VatRatSage,
    VatRegimeSage,
    VatSage,
    AxeSage,
    CctSage,
    SectionSage,
    SupplierArticleAxePro,
)

MODELS_ARTICLES = (
    Article,
    ArticleUpdate,
    SalePriceHistory,
    SellingPrice,
    Subscription,
    SubscriptionArticle,
)

MODELS_BOOK = (
    Society,
    Address,
    Contact,
    Nature,
    SocietyBank,
    SupplierCct,
    SupplierArticleAxePro,
    FamilleAxePro,
)
MODELS_CENTER_CLIENTS = (
    Maison,
    MaisonBi,
    ClientFamilly,
    ClientContact,
    ContactExchange,
    DocumentsSubscription,
    MaisonSupllierExclusion,
    MaisonSupplierIdentifier,
)
MODELS_CENTER_PURCHASING = (
    PrincipalCenterPurchase,
    ChildCenterPurchase,
    Signboard,
    SignboardModel,
    Action,
    SignboardModelTranslate,
    Translation,
    TranslationParamaters,
)
MODELS_EDI = (SupplierDefinition, ColumnDefinition)
MODELS_PARAMETERS = (
    Category,
    CategoryModelInvoice,
    SubCategory,
    SubFamilly,
    ActionPermission,
    AddressCode,
    Counter,
    Parameters,
    Periodicity,
    SalePriceCategory,
    SendFiles,
    SendFilesMail,
)


def make_insert(cursor_from, cursor_to, table, fields):
    """Fonction qui réalise l'insertion en base d'un cursor sur l'autre avec on conflict do nothing
    :param cursor_from: cursor bdd de prod
    :param cursor_to: cursor bdd de dev
    :param table: table à mettre à jour
    :param fields: champs de la table à importer
    :return: None
    """
    table_temp = f"temp_{table}"
    sql_create_temp_table_dev = (
        f"CREATE TEMPORARY TABLE IF NOT EXISTS {table_temp} (LIKE {table});".replace("\n", " ")
    )
    sql_insert_temp_dev = rf"""
        COPY {table_temp} ({', '.join(fields)}) 
        FROM STDIN 
        WITH 
        DELIMITER AS ';' 
        CSV 
        QUOTE AS '"';
    """.replace(
        "\n", " "
    )
    fields_without_id = [field for field in fields if field != "id"]
    sql_insert_table = f"""
    INSERT INTO {table} 
    ({', '.join(fields_without_id)})
    SELECT 
        {', '.join(fields_without_id)}
    FROM {table_temp}
    ON CONFLICT DO NOTHING;
    """.replace(
        "\n", " "
    )
    sql_drop_temp_table_dev = f"DROP TABLE IF EXISTS {table_temp};"

    stream = StringIO()
    writer = csv.writer(stream, delimiter=";")
    select_heron = f"""select {", ".join(fields)} from {table}""".replace("\n", " ")
    cursor_from.execute(select_heron)
    print(f"Select in PROD : {table}")
    print(f"\t{select_heron}")

    for line in cursor_from.fetchall():
        writer.writerow(line)

    stream.seek(0)
    print(f"Create table temp : {table_temp}, in DEV")
    print(f"\t{sql_create_temp_table_dev}")
    cursor_to.execute(sql_create_temp_table_dev)

    print(f"Insert into {table_temp} - {table}, in DEV")
    print(f"\t{sql_insert_table}")
    cursor_to.copy_expert(sql=sql_insert_temp_dev, file=stream)

    print(f"Insert into {table} do nothing, in DEV")
    print(f"\t{sql_insert_table}")
    cursor_to.execute(sql_insert_table)

    print(f"Drop {table_temp}, in DEV")
    print(f"\t{sql_drop_temp_table_dev}")
    cursor_to.execute(sql_drop_temp_table_dev)

    stream.close()


def main(model_list):
    """Lancement de tous les imports de l'app accountancy
    :param model_list: liste des modèles à importer
    :return: None
    """
    with connections["heron"].cursor() as cursor_prod, connections[
        "default"
    ].cursor() as cursor_dev:
        for model in model_list:
            table = model._meta.db_table
            fields = [
                f'"{field.name}"' if field.db_column is None else f'"{field.db_column}"'
                for field in model._meta.fields
            ]
            make_insert(cursor_from=cursor_prod, cursor_to=cursor_dev, table=table, fields=fields)


if __name__ == "__main__":
    # main(MODELS_ACCOUNTANCY)
    # main(MODELS_ARTICLES)
    # main(MODELS_BOOK)
    # main(MODELS_CENTER_CLIENTS)
    # main(MODELS_CENTER_PURCHASING)
    # main(MODELS_EDI)
    main(MODELS_PARAMETERS)
