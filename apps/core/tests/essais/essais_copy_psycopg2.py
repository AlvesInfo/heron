import io
from pathlib import Path
import random
import string
import csv
import time
import uuid
from datetime import datetime

from apps.core.functions.functions_setups import settings
from apps.core.functions.function_imports import IterFileToInsert

columns = [
    "l_00",
    "l_01",
    "l_02",
    "l_03",
    "l_05",
    "l_06",
    "l_07",
    "l_09",
    "l_10",
    "l_12",
    "l_13",
    "l_14",
    "l_15",
    "l_16",
    "l_17",
    "l_18",
    "l_20",
    "l_21",
    "l_22",
    "l_24",
    "l_25",
    "l_27",
    "l_28",
    "l_29",
    "l_30",
]

columns_dict_none = {
    "l_00": None,
    "l_01": None,
    "l_02": None,
    "l_03": None,
    "l_05": None,
    "l_06": None,
    "l_07": None,
    "l_09": None,
    "l_10": None,
    "l_12": None,
    "l_13": None,
    "l_14": None,
    "l_15": None,
    "l_16": None,
    "l_17": None,
    "l_18": None,
    "l_20": None,
    "l_21": None,
    "l_22": None,
    "l_24": None,
    "l_25": None,
    "l_27": None,
    "l_28": None,
    "l_29": None,
    "l_30": None,
}

columns_dict_int = {
    "l_00": 0,
    "l_28": 22,
    "l_01": 1,
    "l_02": 2,
    "l_03": 3,
    "l_05": 4,
    "l_06": 5,
    "l_07": 6,
    "l_29": 23,
    "l_09": 7,
    "l_10": 8,
    "l_12": 9,
    "l_13": 10,
    "l_14": 11,
    "l_15": 12,
    "l_16": 13,
    "l_17": 14,
    "l_18": 15,
    "l_25": 20,
    "l_20": 16,
    "l_21": 17,
    "l_22": 18,
    "l_24": 19,
    "l_27": 21,
    "l_30": 24,
}

columns_dict_named = {
    "l_00": "l_00",
    "l_28": "l_28",
    "l_01": "l_01",
    "l_02": "l_02",
    "l_03": "l_03",
    "l_05": "l_05",
    "l_06": "l_06",
    "l_07": "l_07",
    "l_29": "l_29",
    "l_09": "l_09",
    "l_10": "l_10",
    "l_12": "l_12",
    "l_13": "l_13",
    "l_14": "l_14",
    "l_15": "l_15",
    "l_16": "l_16",
    "l_17": "l_17",
    "l_18": "l_18",
    "l_25": "l_25",
    "l_20": "l_20",
    "l_21": "l_21",
    "l_22": "l_22",
    "l_24": "l_24",
    "l_27": "l_27",
    "l_30": "l_30",
}
file = Path(settings.APPS_DIR) / "core/tests/test_fixtures/test_copy_psycopg2.csv"
l = [0, 22, 1, 2, 3, 4, 5, 6, 23, 7, 8, 9, 10, 11, 12, 13, 14, 15, 20, 16, 17, 18, 19, 21, 24]


def get_random_name(size=20):
    """
    Retourne une suite de lettre alléatoire
    :param size: taille
    :return: texte
    """
    pool = string.ascii_lowercase
    return "".join(random.SystemRandom().choice(pool) for _ in range(size)).lower()


def gen_csv():
    """Génaration du csv pour test isertion"""

    with open(file, "w", encoding="utf8", newline="") as csv_file:
        csv_writer = csv.writer(csv_file, delimiter=";", quotechar='"', quoting=csv.QUOTE_ALL)

        csv_writer.writerow(columns)

        for i in range(10_000):
            print(i)
            csv_writer.writerow(
                [get_random_name() for _ in columns[:-2]] + [""] + [get_random_name()]
            )


def essais_copy():
    start = time.time()
    dict_to_test = {"l_00": "qpuizhoisvvakfqreoth","l_28": "klhexxgdclrgqvvqjurd","l_01": "eyhjiephgbizabtflzru","l_02": "ajnuypuzytcjzlonpetd","l_03": "aytwsxudinllmdawduse","l_05": "cvqflbaaztpaufmerend","l_06": "dmonjrqrqjbzywflingz","l_07": "vfsialaqgqbbrvxffizr","l_29": "","l_09": "alzdgqkkvicjkofxmajv","l_10": "tqzjcjitbsotqtwsgwxb","l_12": "konzpqbzcfkhvfufusvr","l_13": "pmzfpvlaplnfmxqwkaex","l_14": "mkqrflcwzfpsjapyihpd","l_15": "ivrvqrtyzhtpvxtxwgcp","l_16": "uynblkdzfghcsxaxpqyh","l_17": "swuvwifwdlhzpabxdrns","l_18": "nzikqqdhypjsxflsscnp","l_25": "wbueiyabgygvtjaizmtn","l_20": "mllcdtegjljjwzjjpqwk","l_21": "jdlvcpzqwdhrvglrkdds","l_22": "iokohrtepsdxguxllmij","l_24": "tjpqistkcpleuiovjjxp","l_27": "smfsdbwtvifmvdgqefpv","l_30": "fdtmvtlfgoobxwzpjzim",}
    now = datetime.now().isoformat()
    add_fields_dict = {
        "uuid_identification": (uuid.uuid4, {}),
        "created_date": now,
        "modified_date": now,
    }
    # columns_dict_none columns_dict_int    columns_dict_named
    with IterFileToInsert(
        file_to_iter=file,
        first_line=2,
        columns_dict=columns_dict_none,
        # add_fields_dict=add_fields_dict,
    ) as file_to_insert:
        print(file_to_insert.get_add_dict)
        print(file_to_insert.get_add_values)
        # print(file_to_insert.get_header())
        for i, row in enumerate(file_to_insert.chunk_dict(), 1):
            # print(i, row)
            if i == 1:
                print(i, row)
            if i == 8667:
                print(i, row)
                print(row == dict_to_test)
    print(f"temps de production des {i:,.0f} lignes : {(time.time()-start):.2f} s")


def add_file_attr(func, *args, **kwargs):
    return func(*args, **kwargs)


if __name__ == "__main__":
    # print(file, file.is_file())
    # lll = io.StringIO(newline="")
    # print(len(columns))
    # gen_csv()
    essais_copy()
    # start = time.time()
    # import timeit
    # timeit.timeit(essais_copy, number=1)
    # print(f"temps de production des 20 itérations : {(time.time() - start):.2f} s")
    # print([get_random_name() for _ in columns[:-2]] + [""] + [get_random_name()])
