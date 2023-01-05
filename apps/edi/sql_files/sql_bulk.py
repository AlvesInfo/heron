# pylint: disable=
"""
FR : Module des requêtes sql de post-traitement après import des fichiers de Bbgr BULK
EN : Post-processing sql module after importing supplier invoice files

Commentaire:

created at: 2022-11-27
created by: Paulo ALVES

modified at: 2022-11-27
modified by: Paulo ALVES
"""
from psycopg2 import sql

post_bulk_dict = {
    "sql_update": sql.SQL(
        """
    update "edi_ediimport"
    set 
        "famille" = case when "famille" is null then 'VERRE' else "famille" end,
        "gross_unit_price" = "net_unit_price",
        "gross_amount" = "net_amount",
        "purchase_invoice" = true,
        "sale_invoice" = true
    where "uuid_identification" = %(uuid_identification)s
    and ("valid" = false or "valid" isnull)
    """
    )
}
