"""
Module apportant des fonctionnalités pratique à psycopg2
"""
import sys
import types
from itertools import chain, islice
import psycopg2
from psycopg2 import pool
from psycopg2.extras import execute_batch, execute_values
from psycopg2.extensions import parse_dsn

from core.functions.functions_sql import clean_sql_in
from core.functions.loggers import POSTGRES_LOGGER


TYPE_POSTGRESQL = {
    "bigint": ("int", "validate_int"),
    "bigserial": ("int", "validate_int"),
    "bit": ("bit", "validate_bit"),
    "bit varying": ("bit", "validate_bit"),
    "boolean": ("bool", "validate_bool"),
    "box": ("box", "validate_box"),
    "bytea": ("bit", "validate_bit"),
    "character": ("str", "validate_str"),
    "character varying": ("str", "validate_str"),
    "cidr": ("cidr", "validate_cidr"),
    "circle": ("circle", "validate_circle"),
    "date": ("date", "validate_date"),
    "double precision": ("float", "validate_float"),
    "inet": ("inet", "validate_inet"),
    "integer": ("int", "validate_int"),
    "interval": ("interval", "validate_interval"),
    "json": ("json", "validate_json"),
    "jsonb": ("json", "validate_json"),
    "line": ("line", "validate_line"),
    "lseg": ("lseg", "validate_lseg"),
    "macaddr": ("macaddr", "validate_macaddr"),
    "macaddr8": ("macaddr8", "validate_macaddr8"),
    "money": ("float", "validate_float"),
    "numeric": ("float", "validate_numeric"),
    "path": ("path", "validate_path"),
    "pg_lsn": ("pg_lsn", "validate_pg_lsn"),
    "point": ("point", "validate_point"),
    "polygon": ("polygon", "validate_polygon"),
    "real": ("real", "validate_real"),
    "smallint": ("int", "validate_int"),
    "smallserial": ("int", "validate_int"),
    "serial": ("int", "validate_int"),
    "text": ("str", "validate_str"),
    "time": ("time", "validate_time"),
    "time with time zone": ("time", "validate_time"),
    "timestamp": ("datetime", "validate_date"),
    "timestamp with time zone": ("datetime", "validate_date"),
    "tsquery": ("tsquery", "validate_tsquery"),
    "tsvector": ("tsvector", "validate_tsvector"),
    "txid_snapshot": ("txid_snapshot", "validate_txid_snapshot"),
    "uuid": ("uuid", "validate_uuid"),
    "xml": ("xml", "validate_xml"),
}


class PoolPostgresql:
    """
    Class de pool de connection à Postgresql, cela permet d'utiliser
    les fonctions qui demande une connection psycopg2
        :param string_of_connexion: string de connection à postgresql
        exemple d'utilisation :
            >>> from core.functions.functions_postgresql import PoolPostgresql
            >>> cnx_string = (
                    f"dbname=dbname "
                    f"user=user "
                    f"password=password "
                    f"host=host "
                    f"port=port"
                )
            >>> with PoolPostgresql(cnx_string) as cnx:
            ...     with cnx.cursor() as cur:
            ...         cur.execute("SELECT * FROM articles_article limit 1")
            ...         print(cur.fetchall()[0][:3])
            (816134, datetime.datetime(2014, 8, 21), datetime.datetime(2019, 1, 29))
    """

    pool_instance = None
    cnx_string = None
    pool_cnx = None

    def __init__(self, string_of_connexion):
        self.key = id(self)

        if not PoolPostgresql.pool_instance:
            self.__class__.pool_instance = self
            self.__class__.cnx_string = string_of_connexion
            self.pool_connect()

        self.cnx = self.get_cnx()

    def pool_connect(self):
        """
        Fonction de génération du pool de connexion
        """
        if not self.__class__.pool_cnx:
            i = 0

            while i < 5:
                try:
                    self.__class__.pool_cnx = pool.SimpleConnectionPool(
                        1, 20, self.__class__.cnx_string
                    )
                    break

                except psycopg2.Error as error:
                    log_line = f"PoolPostgresql error: {error}\n"
                    print(log_line)

                i += 1

    def get_cnx(self):
        """
        Fonction de génération de demande de connexion au pool
        """
        connection = None

        try:
            if not self.__class__.pool_cnx:
                self.pool_connect()
            connection = self.__class__.pool_cnx.getconn(key=self.key)

        except psycopg2.pool.PoolError as error:
            if error == "connection pool is closed":
                self.pool_connect()
                self.cnx = self.get_cnx()
            else:
                print(sys.exc_info()[1])

        return connection

    def close_cnx(self):
        """
        Fonction de fermeture de la connexion au pool
        """
        if self.__class__.pool_cnx:
            self.__class__.pool_cnx.putconn(self.cnx, key=self.key, close=True)

    @classmethod
    def close_all(cls):
        """
        Fonction de fermeture de toutes les connexions
        """
        cls.pool_cnx.closeall()
        cls.pool_cnx = None

    def __enter__(self):
        """
        Fonction __enter__ pour la gestion du with
        """
        return self.get_cnx()

    def __exit__(self, *args, **kwargs):
        """
        Fonction __exit__ pour la gestion du with
        """
        self.close_cnx()


class WithCnxPostgresql:
    """
    Classe de connection à postgresql avec with
        conn = WithCnxPostgresql(dsn)
        # transaction 1
        with conn:
            with conn.cursor() as cur:
                cur.execute(sql)
        # transaction 2
        with conn:
            with conn.cursor() as cur:
                cur.execute(sql)
    """

    def __init__(self, string_of_connexion):
        self.connexion = None
        i = 0
        while i < 5:
            try:
                kwargs_cnx = parse_dsn(string_of_connexion)
                self.connexion = psycopg2.connect(**kwargs_cnx)
                break

            except psycopg2.Error as error:
                log_line = f"WithCnxPostgresql error: {error}\n"
                print(log_line)

            i += 1

    def __enter__(self):
        return self.connexion

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.connexion is not None:
            self.connexion.close()


def cnx_postgresql(string_of_connexion):
    """
    Fonction de connexion à Postgresql par psycopg2
        :param string_of_connexion: cnx_string = (
                                        f"dbname={NAME_DATABASE} "
                                        f"user={USER_DATABASE} "
                                        f"password={PASSWORD_DATABASE} "
                                        f"host={HOST_DATABASE} "
                                        f"port={PORT_DATABASE}"
                                    )
        :return: cnx
    """
    try:
        kwargs_cnx = parse_dsn(string_of_connexion)
        connexion = psycopg2.connect(**kwargs_cnx)

    except psycopg2.Error as error:
        log_line = f"cnx_postgresql error: {error}\n"
        print(log_line)
        connexion = None

    return connexion


def query_select(cnx, sql_requete=None):
    """
    Fonction qui retourne le resultat d'une requête sql Postgresql.
        :param cnx: connexion à la base postgresql psycopg2
        :param sql_requete: requête selection souhaitée
                                ex: "SELECT * FROM table"
        :return: La liste des éléments de la requête
    """
    if sql_requete:
        try:
            with cnx.cursor() as cur:
                cur.execute(sql_requete)
                list_rows = cur.fetchall()
            return list_rows

        except psycopg2.Error as error:
            log_line = f"query_select error: {error}\n"
            print(log_line)
            # write_log(self.log_file, log_line)
            # envoi_mail_erreur(log_line)
    return None


def query_real_dict_cursor(cnx, sql_requete=None):
    """
    Fonction qui retourne le resultat d'une requête sql Postgresql, comme un dictionnaire
        :param cnx: connexion à la base postgresql psycopg2
        :param sql_requete: requête selection souhaitée
                                ex: "SELECT * FROM table"
        :return: La liste des dictionnaires de la requête
    """
    if sql_requete:
        try:
            with cnx.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(sql_requete)
                list_rows = cur.fetchall()
            return list_rows

        except psycopg2.Error as error:
            log_line = f"query_real_dict_cursor error: {error}\n"
            print(log_line)
            # write_log(self.log_file, log_line)
            # envoi_mail_erreur(log_line)

    return None


def query_execute(cnx, sql_requete=None):
    """
    Fonction qui exécute une requête sql Postgresql.
        :param cnx: connexion à la base postgresql psycopg2
        :param sql_requete: requête selection souhaitée
                                ex: "UPDATE table SET champ=1"
                                    "UPDATE table SET champ=1 WHERE x = 0"
                                    "DELETE FROM table"
        :return: True ou None si exception
    """
    if sql_requete:
        try:
            with cnx.cursor() as cur:
                cur.execute(sql_requete)
                cnx.commit()
            return True

        except psycopg2.Error as error:
            log_line = f"query_execute error: {error}\n"
            print(log_line)
            # write_log(self.log_file, log_line)
            # envoi_mail_erreur(log_line)

    return None


def query_dict(cnx, sql_requete=None):
    """
    Fonction qui retourne le resultat d'une requête sql Postgresql, comme un dictionnaire
        :param cnx: connexion à la base postgresql psycopg2
        :param sql_requete: requête selection souhaitée
                                ex: "SELECT * FROM table"
        :return: La liste des dictionnaires de la requête
    """

    if sql_requete:
        try:
            with cnx.cursor() as cur:
                cur.execute(sql_requete)
                columns = [col[0] for col in cur.description]
                return [dict(zip(columns, row)) for row in cur.fetchall()]

        except psycopg2.Error as error:
            log_line = f"query_real_dict_cursor error: {error}\n"
            print(log_line)

    return None


def copy_from(
    cnx, file, table, sep=";", columns=None, size=8192, null=None, header=None
):
    """
    Fonction qui integre un csv dans une table Postgresql.
        copy_from(file, table, sep='\t', null='\\N', , columns=None)
        :param cnx: connexion à la base postgresql psycopg2
        :param file: fichier csv à intégrer
        :param table: table d'insertion
        :param sep: séparation des champs du fichier
        :param columns: colonnes
        :param size: taille du buffer
        :param null: valeur du null dans le fichier
        :param header: si il y a des entêtes dans le fichier
        :return: True ou None si exception
    """
    try:
        with cnx.cursor() as cur:
            with open(file, "r") as fichier:
                if header is not None:
                    next(fichier)

                if null is not None:
                    cur.copy_from(
                        fichier, table, sep=sep, columns=columns, size=size, null=null
                    )
                else:
                    cur.copy_from(fichier, table, sep=sep, columns=columns, size=size)

                return True, "succes"

    except psycopg2.Error as error:
        log_line = "copy_from error: {0}\n".format(error)
        print(log_line)
        # write_log(self.log_file, log_line)
        # envoi_mail_erreur(log_line)
        return None, log_line


def get_types_champs(cnx, table, list_champs=None):
    """
    Fonction qui récupère les types de champs de la table et des champs demandés pour la requête
        :return: list des champs, (taille, type, list des champs)
    """
    columns = (
        "AND column_name {0}".format(clean_sql_in(list_champs)) if list_champs is not None else ""
    )

    with cnx.cursor() as cursor:
        sql_champs = """
            SELECT column_name, data_type, character_maximum_length, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = '{0}' 
            {1};
        """.format(
            table, columns
        )
        # print(sql_champs)
        cursor.execute(sql_champs)
        list_champs_taille_type = {r[0]: tuple(r[1:]) for r in cursor.fetchall()}

    return list_champs_taille_type, list_champs


def _paginate(seq, page_size):
    """
    Fonction prise à psycopg2.
    Slicing d'un itérable pour execute_batch
        :param seq: itérable
        :param page_size: taille en sortie
        :return: Slicing de l'itérateur par longeur de page_size
    """
    page = []
    ite = iter(seq)
    while 1:
        try:
            for _ in range(page_size):
                page.append(next(ite))
            yield page
            page = []
        except StopIteration:
            if page:
                yield page
            return


def executebatch(cur, sql, iterable, page_size=500):
    """
    Fonction prise à psycopg2.
    execute batch, qui renvoi le nombre d'éléments envoyés en insertion
        :param cur: cursor psycopg2
        :param sql: requete sql
        :param iterable: iterateur des données à insèrer en base
        :param page_size: taille du slicing des tranches
        :return: Slicing de l'itérateur par longeur de page_size
    """
    erreur = True
    count_initial = 0
    count_final = 0

    for page in _paginate(iterable, page_size=page_size):
        nbre = len(page)
        count_initial += nbre

        try:
            if erreur:
                sqls = [cur.mogrify(sql, args) for args in page]
                cur.execute(b";".join(sqls))
                count_final += nbre
                # print(count_final)
        except:
            print(sys.exc_info())
            # print(sqls)
            POSTGRES_LOGGER.exception("execute_bash")
            erreur = None
            break

    return erreur, (count_initial, count_final)


def execute_prepared_upsert(kwargs_upsert):
    """Fonction qui exécute une requete préparée, INSERT ou UPSERT.
    Attention!!! cette requête sera en autocommit.
    exemple :
    cursor.execute("PREPARE stmt (int, text, bool)
    AS INSERT INTO foo VALUES ($1, $2, $3) ON CONFLICT DO NOTHING;")
    execute_batch(cursor, "EXECUTE stmt (%s, %s, %s)", list_values)
    cursor.execute("DEALLOCATE stmt")

        :param kwargs_upsert: {
                      cnx: connexion psycopg2
                    table: table concerné par la requête
                  columns: champs de la table, souhaités dans la requête
                     rows: Liste des valeurs à inserer dans la table
            champs_unique: liste des champs d'unicité dans la table,
                           si on veut un Upsert ON CONFLICT UPDATE
                   upsert: None explicit, si on ne veut pas d'upsert
                page_size: rien ou nbre par iteration
                }
        :return: True, (1000, 1000) en cas de succès
                 None, (elements_all, elements_ok) en cas d'erreur
    """
    dict_rows = get_types_champs(
        kwargs_upsert["cnx"], kwargs_upsert["table"], kwargs_upsert["columns"]
    )[0]
    prepare = "PREPARE stmt ("
    insert = "("
    colonnes = "("
    execute = "EXECUTE stmt ("

    for i, k in enumerate(kwargs_upsert["columns"]):
        champ, t_p = k, dict_rows[k][0]
        prepare += "{0}, ".format(t_p)
        insert += "${0}, ".format(i + 1)
        colonnes += '"{0}", '.format(champ)
        execute += "%s, "

    colonnes = "{0})".format(colonnes[:-2])
    insert = "{0})".format(insert[:-2])
    prepare = """
    {0}) AS INSERT INTO "{1}" {2} VALUES {3} 
    """.format(
        prepare[:-2], kwargs_upsert["table"], colonnes, insert
    )
    execute = "{0});".format(execute[:-2])

    if kwargs_upsert["upsert"] is None:
        prepare += ";"

    else:
        if kwargs_upsert["champs_unique"] is None:
            prepare += "ON CONFLICT DO NOTHING;"

        else:
            chu = "("
            for k in kwargs_upsert["champs_unique"]:
                chu += '"{0}", '.format(k)
            chu = "{0})".format(chu[:-2])
            prepare += " ON CONFLICT {0} DO UPDATE SET ".format(chu)
            for champ in kwargs_upsert["columns"]:
                if champ not in kwargs_upsert["champs_unique"]:
                    prepare += '"{0}" = excluded."{0}", '.format(str(champ))

            prepare = "{0};".format(prepare[:-2])

    page_size = kwargs_upsert.get("page_size", 500)

    # print(prepare)
    # print(execute)
    # print(kwargs_upsert['rows'])
    try:
        with kwargs_upsert["cnx"] as cnx:
            with cnx.cursor() as cursor:
                cursor.execute(prepare)
                error, tup_count = executebatch(
                    cursor, execute, kwargs_upsert["rows"], page_size=page_size
                )
                cursor.execute("DEALLOCATE stmt")

    except psycopg2.Error as err:
        POSTGRES_LOGGER.exception(f"{err}")
        tup_count = err
        error = None
        try:
            with kwargs_upsert["cnx"] as cnx:
                with cnx.cursor() as cursor:
                    cursor.execute("DEALLOCATE stmt")
        except:
            POSTGRES_LOGGER.exception("deallocate stmt")

    return error, tup_count


if __name__ == "__main__":
    pass
