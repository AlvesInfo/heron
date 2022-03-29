def countdown(n):
    """function countdown"""
    while n > 0:
        n -= 1


def multiples_process():
    from threading import Thread
    import multiprocessing
    import time

    COUNT = 100_000_000

    start = time.time()
    countdown(COUNT)
    end = time.time()
    print(end - start)

    t1 = Thread(target=countdown, args=(COUNT / 4,))
    t2 = Thread(target=countdown, args=(COUNT / 4,))
    t3 = Thread(target=countdown, args=(COUNT / 4,))
    t4 = Thread(target=countdown, args=(COUNT / 4,))
    start = time.time()
    t1.start()
    t2.start()
    t3.start()
    t4.start()
    t1.join()
    t2.join()
    t3.join()
    t4.join()
    end = time.time()
    print(end - start)

    start = time.time()
    with multiprocessing.Pool() as pool:
        pool.map(
            countdown,
            [
                COUNT / 4,
                COUNT / 4,
                COUNT / 4,
                COUNT / 4,
            ],
        )

        pool.close()
        pool.join()

    end = time.time()
    print(end - start)


def essais_inserts():
    import io
    import csv
    import time
    from psycopg2 import sql
    from apps.core.functions.functions_setups import connection

    file = io.StringIO()

    w = csv.writer(
        file,
        delimiter=";",
        quotechar='"',
        lineterminator="\n",
        quoting=csv.QUOTE_ALL,
        escapechar='"',
    )
    t = """'essai"ess'"""
    w.writerow(["000", t, 90])
    print("génération fichier texte")

    for _ in range(100_000):
        file.write("""aaaaaaaaaaaa;"zzzzzzzzzzzzzzzzzz""zzzzzzzzzzzzzzzzz";"10"\n""")

    print("fin génération fichier texte")

    try:
        start_i = time.time()
        file.seek(0)

        with connection.cursor() as cursor:
            fields = sql.SQL(",").join(
                [
                    sql.Identifier("col_texte"),
                    sql.Identifier("col_3"),
                    sql.Identifier("col_int"),
                ]
            )
            table = sql.Identifier("aa_essais")
            sql_copy = sql.SQL(
                "COPY {table} ({fields}) FROM STDIN WITH DELIMITER AS ';' CSV"
            ).format(fields=fields, table=table)
            cursor.copy_expert(sql=sql_copy, file=file)
            copie = round(time.time() - start_i, 2)

            start = time.time()
            table_insert = sql.Identifier("aa_essais_1")
            sql_insert = sql.SQL(
                """
                INSERT INTO {table_insert} ({fields})
                SELECT {fields} FROM {table} 
                ON CONFLICT DO NOTHING
                """
            ).format(table_insert=table_insert, table=table, fields=fields, )
            cursor.execute(sql_insert)
            # print(cursor.mogrify(sql_insert).decode())
            insert = round(time.time() - start, 2)
            final = round(time.time() - start_i, 2)

            sql_delete = sql.SQL("DELETE FROM {table}").format(table=table)
            cursor.execute(sql_delete)

        print(f"copy_expert : {final} s -> copy : {copie} s -- insert : {insert} s")

    except Exception as except_error:
        raise Exception("") from except_error

    file.close()


if __name__ == "__main__":
    # multiples_process()
    essais_inserts()
