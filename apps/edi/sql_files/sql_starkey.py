# pylint: disable=E0401,C0303
"""
FR : Module des requêtes sql de post-traitement après import des fichiers Starkey
EN : Post-processing sql module after importing supplier invoice files

Commentaire:

created at: 2022-11-27
created by: Paulo ALVES

modified at: 2022-11-27
modified by: Paulo ALVES
"""
from psycopg2 import sql

post_starkey_dict = {
    "sql_update": sql.SQL(
        """
        update "edi_ediimport"
        set 
            "invoice_type" = case when "invoice_type" = 'FA' then '380' else '381' end,
            "net_unit_price" = ("net_amount"::numeric / "qty"::numeric)::numeric,
            "purchase_invoice" = true,
            "sale_invoice" = true,
            "origin" = 1
        where "uuid_identification" = %(uuid_identification)s
        and ("valid" = false or "valid" isnull)
        """
    ),
    "sql_update_units": sql.SQL(
        """
        update "edi_ediimport"
        set 
            "qty" = case 
                        when "net_amount" < 0 then (abs("qty")::numeric * -1::numeric)
                        when "net_amount" > 0 then abs("qty")::numeric
                        else "qty" 
                    end,
            "gross_unit_price" = abs("gross_unit_price"),
            "net_unit_price" = abs("net_unit_price"),
            "gross_amount" = case 
                                when "net_amount" = 0 then 0
                                when "net_amount" < 0 
                                    then (
                                        abs("gross_unit_price"::numeric * "qty"::numeric)::numeric 
                                        * 
                                        -1::numeric
                                    )
                                when "net_amount" > 0 
                                    then (
                                        abs("gross_unit_price"::numeric * "qty"::numeric)::numeric 
                                    )
                            end
        where "uuid_identification" = %(uuid_identification)s
        and ("valid" = false or "valid" isnull)
        """
    ),
    "sql_copie_envoi_depot": sql.SQL(
        """
        insert into "edi_starkeydepot"
        select * from "edi_ediimport" ee
        where ee."uuid_identification" = %(uuid_identification)s
        and ee."comment" = 'ENVOI_DEPOT'
        and (ee."valid" = false or ee."valid" isnull)
        on conlict do nothing
        """
    ),
    "sql_delete_envoi_depot": sql.SQL(
        """
        delete from "edi_ediimport"
        where "uuid_identification" = %(uuid_identification)s
        and "comment" = 'ENVOI_DEPOT'
        and ("valid" = false or "valid" isnull)
        """
    ),
}
