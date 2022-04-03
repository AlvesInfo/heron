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
    from apps.core.functions.functions_setups import settings
    from apps.data_flux.postgres_save import (
        PostgresDjangoUpsert,
        PostgresDjangoError,
        PostgresCardinalityViolationError,
        PostgresTypeError,
        PostgresUniqueError,
        PostgresInsertMethodError,
    )
    from apps.data_flux.models import Essais, EssaisZ

    from apps.data_flux.loggers import INSERT_LOGGER_FLUX

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

    for _ in range(1_000):
        file.write("""aaaaaaaaaaaa;"zzzzzzzzzzzzzzzzzz""zzzzzzzzzzzzzzzzz";"1Z"\n""")

    print("fin génération fichier texte")

    try:
        start_i = time.time()
        file.seek(0)

        # test_01 = PostgresDjangoUpsert(
        #     Essais, {"col_texte": False, "col_3": False, "col_int": True}
        # )
        # test_01.insert(file, insert_mode="insert")
        # copie = round(time.time() - start_i, 2)
        # print("copie : ", copie)

        # start = time.time()
        # file.seek(0)
        # test_02 = PostgresDjangoUpsert(
        #     EssaisZ, {"col_texte": False, "col_3": False, "col_int": True}
        # )
        # test_02.insert(file, insert_mode="do_nothing")
        # do_nothing = round(time.time() - start, 2)
        # print("do_nothing : ", do_nothing)

        start = time.time()
        file.seek(0)
        test_03 = PostgresDjangoUpsert(
            EssaisZ, {"col_texte": False, "col_3": False, "col_int": True}
        )
        test_03.insert(file, insert_mode="upsert")
        upsert = round(time.time() - start, 2)
        print("upsert : ", upsert)

        final = round(time.time() - start_i, 2)

        print(
            f"copy_expert : {final} s -> "
            # f"copy insert : {copie} s -- "
            # f"copy do_nothing : {do_nothing} s -- "
            f"copy upsert : {upsert} s"
        )

    except PostgresInsertMethodError:
        INSERT_LOGGER_FLUX.exception("La methode d'insertion choisie n'existe pas")

    except PostgresCardinalityViolationError:
        INSERT_LOGGER_FLUX.exception(
            f"Plusieurs mise à jour pour le même élément reçu, table : {EssaisZ._meta.db_table!r}"
        )

    except PostgresTypeError:
        INSERT_LOGGER_FLUX.exception("Erreur de type")

    except PostgresUniqueError:
        INSERT_LOGGER_FLUX.exception("Erreur sur clé dupliquée")

    except PostgresDjangoError:
        INSERT_LOGGER_FLUX.exception("Erreur inconnue")

    file.close()


if __name__ == "__main__":
    # multiples_process()
    essais_inserts()
