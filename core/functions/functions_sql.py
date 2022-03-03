"""
Module pour utilitaires sql
"""
import types
import collections
from psycopg2.sql import Literal


class IntError(ValueError):
    """Class transform int error
    """


class ColumnsError(Exception):
    """Exception de gestion de la class ModelDjango
    """


def essai_sql():
    """
    Module pour utilitaires sql

    Placeholder :
        >>> names = ['foo', 'bar', 'baz']

        >>> q1 = sql.SQL("insert into table ({}) values ({})").format(
        ...     sql.SQL(', ').join(map(sql.Identifier, names)),
        ...     sql.SQL(', ').join(sql.Placeholder() * len(names)))
        >>> print(q1.as_string(conn))
        insert into table ("foo", "bar", "baz") values (%s, %s, %s)

        >>> q2 = sql.SQL("insert into table ({}) values ({})").format(
        ...     sql.SQL(', ').join(map(sql.Identifier, names)),
        ...     sql.SQL(', ').join(map(sql.Placeholder, names)))
        >>> print(q2.as_string(conn))
        insert into table ("foo", "bar", "baz") values (%(foo)s, %(bar)s, %(baz)s)

    Identifier :
        >>> t1 = sql.Identifier("foo")
        >>> t2 = sql.Identifier("ba'r")
        >>> t3 = sql.Identifier('ba"z')
        >>> print(sql.SQL(', ').join([t1, t2, t3]).as_string(conn))
        "foo", "ba'r", "ba""z"

        >>> query = sql.SQL("SELECT {} FROM {}").format(
        ...     sql.Identifier("table", "field"),
        ...     sql.Identifier("schema", "table"))
        >>> print(query.as_string(conn))
        SELECT "table"."field" FROM "schema"."table"

    Literal :
        >>> s1 = sql.Literal("foo")
        >>> s2 = sql.Literal("ba'r")
        >>> s3 = sql.Literal(42)
        >>> print(sql.SQL(', ').join([s1, s2, s3]).as_string(conn))
        'foo', 'ba''r', 42
    """


def clean_int(int_value):

    try:
        return int(int_value)
    except ValueError:
        raise IntError("Les valeurs doivent etre des int")


def clean_int_list(iter_values):

    try:
        return [int(value) for value in iter_values]
    except ValueError:
        raise IntError("Les valeurs doivent etre des int")


def clean_int_sql_in(iter_values):

    try:
        return f"in ({', '.join(int(value) for value in iter_values)})"
    except ValueError:
        raise IntError("Les valeurs doivent etre des int")


def clean_str(str_value):
    return Literal(str(str_value))


def clean_str_list(iter_values):

    return [str(Literal(str_value)) for str_value in iter_values]


def clean_str_sql_in(iter_values):

    return f"in ({', '.join(str(Literal(str_value)) for str_value in iter_values)})"


def clean_id(p_k):
    """
    Fonction qui renvoie 0, si le pk reçu n'est pas une instance de int
        :param p_k: int
        :return: p_k ou 0
    """
    pk_int = 0

    try:
        pk_int = int(p_k)

    except ValueError:
        pass

    return pk_int


def clean_id_liste(id_list):
    """
    Fonction qui renvoie une liste vide, si tous les pk de l'id_list reçue ne sont pas des instances
    de int
        :param id_list: [17, 32, 44, 2]
        :return: [17, 32, 44, 2] ou []
    """
    list_id = []

    if isinstance(id_list, (list, tuple, types.GeneratorType)):

        try:
            for p_k in id_list:
                list_id.append(int(p_k))

        except ValueError:
            list_id = []

    return list_id


def clean_str_id_liste(id_list):
    """
    Fonction qui renvoie une liste vide, si tous les pk de l'id_list reçue ne sont pas des int
        :param id_list: ['17', '32', '44', '2']
        :return: [17, 32, 44, 2] ou []
    """
    list_id = []

    if isinstance(id_list, (list, tuple, types.GeneratorType)):
        for p_k in id_list:
            try:
                i_pk = int(p_k)
                list_id.append(i_pk)

            except ValueError:
                list_id = []
                break

    return list_id


def clean_sql_in(sql, entier=None):
    """
    Fonction qui renvoie la fonction sql : in, proprement
        :param sql: [14, 28, ...] ou ['test', 'test2', ...]
        :param entier: Si la liste doit être des entiers
        :return: in (14, 28, ...) ou in ('test', 'test2', ...)
    """
    sql_in = ""

    if sql:
        if isinstance(sql, str):
            sql_r = str(sql).replace("'", "''")
            sql_in = f"IN ('{sql_r}')"

        elif isinstance(sql, int):
            sql_in = f"IN ({sql})"

        else:
            sql_in = f"""IN ({
                ', '.join("'" + str(value).replace("'", "''") + "'" 
                          if entier is None 
                          else value 
                          for value in sql)
            })"""

    return sql_in


def clean_sql_in_params(sql, entier=None):
    """
    Fonction qui renvoie la fonction sql : in, proprement
        :param sql: [14, 28, ...] ou ['test', 'test2', ...]
        :param entier: Si la liste doit être des entiers
        :return: in (14, 28, ...) ou in ('test', 'test2', ...)
    """
    sql_in = ""

    if sql:
        if isinstance(sql, str):
            sql_r = str(sql).replace("'", "''")
            sql_in = f"'{sql_r}'"

        elif isinstance(sql, int):
            sql_in = f"{sql}"

        else:
            sql_in = f"""{
                ', '.join("'" + str(value).replace("'", "''") + "'" 
                          if entier is None 
                          else value 
                          for value in sql)
            }"""

    return sql_in


def clean_sql_in_like(sql, entier=None):
    """
    Fonction qui renvoie la fonction sql : in, proprement. Si % est dans sql alors on renvoie la
    fonction sql like
        :param sql: [14, 28, ...] ou ['test', 'test2', ...]
        :param entier: Si la liste doit être des entiers
        :return: in (14, 28, ...) ou in ('test', 'test2', ...) ou like '%'
    """
    sql_in = ""

    if isinstance(sql, (list, tuple, set, types.GeneratorType)):
        test_pourcent = None

        for row in sql:
            if isinstance(row, collections.Iterable) and "%" in row:
                test_pourcent = True
                break

        if test_pourcent:
            sql_in = "LIKE '%'"

        else:
            if sql:
                sql_in = "IN ("

                for row in sql:
                    if entier:
                        sql_in += f"""{str(row).replace("'", "''")}, """

                    else:
                        sql_in += f"""'{str(row).replace("'", "''")}', """

                sql_in = f"{sql_in[:-2]})"

    return sql_in


def get_model_fields(modele, p_k=None, columns=None, exclude=None):
    """
    Fonction qui retourne les champs de modèles
        :param modele: modèle
        :param p_k: si on souhaite explicitement le champ id
        :param columns: champs que l'on souhaite
        :param exclude: champs que l'on souhaite exclure
        :return: générator de la liste des modèles
    """
    model = modele.__doc__.replace(modele.__name__, "").replace("(", "")
    model = model.replace(")", "").replace(" ", "")

    if p_k is None:
        model = model.replace("id", "")

    if exclude is not None:
        model = ",".join(r for r in model.split(",") if r not in exclude)

    if columns is not None:
        model = ",".join(r for r in model.split(",") if r in columns)

    return (r for r in model.split(",") if r)


def get_model_table_name(modele):
    """
    Fonction qui retourne le nom de la table d'un modèle
    :param modele:
    :return:
    """
    module = modele.__module__.split(".")[-2]
    table_name = f"{module}_{modele.__name__.lower()}"

    return table_name


def main():
    """
    Fonction qui renvoie la fonction sql : in, proprement
        :param sql: [14, 28, ...] ou ['test', 'test2', ...]
        :param entier: Si la liste doit être des entiers
        :return: in (14, 28, ...) ou in ('test', 'test2', ...)
    """
    sql = ["2002163238", "2002133169"]
    entier = None

    sql_in = ""

    if sql:
        if isinstance(sql, str):
            sql_r = str(sql).replace("'", "''")
            sql_in = f"IN ('{sql_r}')"

        elif isinstance(sql, int):
            sql_in = f"IN ({sql})"

        else:
            sql_in = f"""IN ({
                ', '.join("'" + str(value).replace("'", "''") + "'" 
                          if entier is None 
                          else value 
                          for value in sql)
            })"""

    return sql_in


if __name__ == "__main__":
    print(main())
