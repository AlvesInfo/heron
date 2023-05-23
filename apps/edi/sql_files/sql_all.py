# pylint: disable=E0401,C0303
"""
FR : Module des requêtes sql de post-traitement après import des fichiers de factures fournisseur
EN : Post-processing sql module after importing supplier invoice files

Commentaire:

created at: 2022-11-27
created by: Paulo ALVES

modified at: 2022-11-27
modified by: Paulo ALVES
"""
from psycopg2 import sql

SQL_QTY = sql.SQL(
    """
update "edi_ediimport"
set 
    "qty" = case 
                when "qty" = 0 or qty isnull 
                then 1::numeric 
                else "qty" 
            end,
    "devise" = case when "devise" is null then 'EUR' else "devise" end,
    "active" = false,
    "to_delete" = false,
    "to_export" = false
where ("valid" = false or "valid" isnull)
and "uuid_identification" = %(uuid_identification)s
"""
)

post_all_dict = {
    "sql_in_use_third_party_num": sql.SQL(
        """
        with alls as (
            select 
                "third_party_num"
            from (
                select 
                    "third_party_num" 
                from "edi_ediimport" ee 
                union all
                select
                    "third_party_num" 
                from "invoices_invoice" sii 
            ) r
            group by "third_party_num"
        )
        update "book_society" bs
        set "in_use" = true 
        where exists (select 1 from alls aa where aa."third_party_num" = bs."third_party_num")
    """
    ),
    "sql_update_item_weight": sql.SQL(
        """
        update "edi_ediimport" "ee"
        set "item_weight" = 0
        where "item_weight" isnull
    """
    ),
    "sql_orpheans": sql.SQL(
        """
        delete from "edi_ediimport" "ee"
        where "valid" isnull
    """
    ),
}
