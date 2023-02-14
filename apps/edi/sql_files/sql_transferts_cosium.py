# pylint: disable=E0401,C0303
"""
FR : Module des requêtes sql de post-traitement après import des Tranferts Cosium
EN : Post-processing sql module after importing supplier Cosium Transfers

Commentaire:

created at: 2023-01-14
created by: Paulo ALVES

modified at: 2023-01-14
modified by: Paulo ALVES
"""
from psycopg2 import sql

post_transfert_cosium_dict = {
    "sql_amounts": sql.SQL(
        """
    update "edi_ediimport" "edi"
    set "gross_unit_price" = "net_unit_price",
        "net_amount" = round(("qty"*"net_unit_price")::numeric, 2)::numeric,
        "gross_amount" = round(("qty"*"net_unit_price")::numeric, 2)::numeric,
        "vat_amount" = round(("qty"*"net_unit_price"*"vat_rate")::numeric, 2)::numeric,
        "amount_with_vat" = (
            round(("qty"*"net_unit_price"*"vat_rate")::numeric, 2)::numeric 
            + 
            round(("qty"*"net_unit_price")::numeric, 2)::numeric
        ),
        "purchase_invoice" = false,
        "sale_invoice" = true
    where "uuid_identification" = %(uuid_identification)s
      and ("valid" = false or "valid" isnull)
    """
    ),
    "sql_update_articles": sql.SQL(
        """
        update "edi_ediimport" edi 
        set "uuid_big_category" = (
                    select 
                        uuid_identification 
                      from parameters_category 
                     where slug_name = 'marchandises'
                     limit 1
                )
        where edi."uuid_identification" = %(uuid_identification)s
          and (edi."valid" = false or edi."valid" isnull)
    """
    ),
}
