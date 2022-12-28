# pylint: disable=
"""
FR : Module des requêtes sql de post-traitement après import des fichiers BBGR Retours
EN : Post-processing sql module after importing supplier invoice files

Commentaire:

created at: 2022-11-27
created by: Paulo ALVES

modified at: 2022-11-27
modified by: Paulo ALVES
"""
from psycopg2 import sql

bbgr_004_retours_dict = {
    "sql_vat": sql.SQL(
        """
        update "edi_ediimport"
        set 
            "vat_rate" = ("vat_rate"::numeric / 100::numeric)::numeric
        where "uuid_identification" = %(uuid_identification)s
        and ("valid" = false or "valid" isnull)
        """
    ),
}
