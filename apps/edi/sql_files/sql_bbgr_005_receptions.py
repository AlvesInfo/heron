# pylint: disable=
"""
FR : Module des requêtes sql de post-traitement après import des fichiers BBGR Receptions
EN : Post-processing sql module after importing supplier invoice files

Commentaire:

created at: 2023-01-04
created by: Paulo ALVES

modified at: 2023-01-04
modified by: Paulo ALVES
"""
from psycopg2 import sql

bbgr_005_receptions_dict = {
    "sql_vat": sql.SQL(
        """
        """
    ),
}
