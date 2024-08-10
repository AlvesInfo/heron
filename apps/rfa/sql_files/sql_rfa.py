# pylint: disable=
"""
FR : Module des requêtes sql de post-traitement après génération des RFA
EN : Post-processing sql module after generate RFA

Commentaire:

created at: 2024-08-09
created by: Paulo ALVES

modified at: 2024-08-09
modified by: Paulo ALVES
"""
from psycopg2 import sql

rfa_dict = {
    "sql_vat": sql.SQL(
        """
        update "edi_ediimport"
        set "vat_rate" = ("vat_rate"::numeric / 100::numeric)::numeric,
            "origin" = 3
        where "uuid_identification" = %(uuid_identification)s
        and ("valid" = false or "valid" isnull)
        """
    ),
    "sql_familles": sql.SQL(
        """
        update edi_ediimport ei
        set "famille" = "reference_article"
        where ei."uuid_identification" = %(uuid_identification)s
        and "famille" isnull
        and (ei."valid" = false or ei."valid" isnull)
        """
    ),
}
