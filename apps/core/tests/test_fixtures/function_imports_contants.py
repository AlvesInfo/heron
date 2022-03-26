# pylint: disable=
"""Module des constantes pour test du module function_imports

Commentaire:

created at: 2021-10-30
created by: Paulo ALVES

modified at: 2021-10-30
modified by: Paulo ALVES
"""
from uuid import UUID
from datetime import datetime
from pathlib import Path

from apps.core.functions.functions_setups import settings

COLUMNS = [
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

COLUMNS_DICT_NONE = {
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

COLUMNS_DICT_INT = {
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

COLUMNS_DICT_NAMED = {
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

DICT_TO_TEST = {
    "l_00": "brylpgokecmkcrwbcqwz",
    "l_01": "zoendkprthwslupzavoe",
    "l_02": "iafiejwdlbufxlzhkoos",
    "l_03": "tizumxngxtwffqbavemn",
    "l_05": "hplmfgukjvxpiyrcdktf",
    "l_06": "sxlbqblmanaxbwlnrxyg",
    "l_07": "anrucgozvgozzifaqqrj",
    "l_09": "akvvgbmanlerkhyyuwnn",
    "l_10": "fxsybylzlbtrukamjtdc",
    "l_12": "tfweqchfnfscflgcgogf",
    "l_13": "ddbmwuyiljxabcyhseal",
    "l_14": "vmfmclchamofbubbykio",
    "l_15": "paacuspbhvxfthywrjmp",
    "l_16": "ashdfvkyxroezwurtuoo",
    "l_17": "kpnubwvxydvmqylckcvg",
    "l_18": "iastmjhjqbkoiizymjao",
    "l_20": "aalybgnyzvpmashqsani",
    "l_21": "bipglrpilsgwxvdymvlx",
    "l_22": "eclwefcktuhrbvfzfjqo",
    "l_24": "aaihsksivddlgdbhdbfk",
    "l_25": "bxwauugvyeihxcrxvfeo",
    "l_27": "xgcfpmoratvepysrlcmn",
    "l_28": "cfizirlmrltglxwtfqng",
    "l_29": "",
    "l_30": "kmxrfnnxgqmsfdkmtfsd",
}

DICT_TO_TEST_AJOUTS = {
    "l_00": "brylpgokecmkcrwbcqwz",
    "l_01": "zoendkprthwslupzavoe",
    "l_02": "iafiejwdlbufxlzhkoos",
    "l_03": "tizumxngxtwffqbavemn",
    "l_05": "hplmfgukjvxpiyrcdktf",
    "l_06": "sxlbqblmanaxbwlnrxyg",
    "l_07": "anrucgozvgozzifaqqrj",
    "l_09": "akvvgbmanlerkhyyuwnn",
    "l_10": "fxsybylzlbtrukamjtdc",
    "l_12": "tfweqchfnfscflgcgogf",
    "l_13": "ddbmwuyiljxabcyhseal",
    "l_14": "vmfmclchamofbubbykio",
    "l_15": "paacuspbhvxfthywrjmp",
    "l_16": "ashdfvkyxroezwurtuoo",
    "l_17": "kpnubwvxydvmqylckcvg",
    "l_18": "iastmjhjqbkoiizymjao",
    "l_20": "aalybgnyzvpmashqsani",
    "l_21": "bipglrpilsgwxvdymvlx",
    "l_22": "eclwefcktuhrbvfzfjqo",
    "l_24": "aaihsksivddlgdbhdbfk",
    "l_25": "bxwauugvyeihxcrxvfeo",
    "l_27": "xgcfpmoratvepysrlcmn",
    "l_28": "cfizirlmrltglxwtfqng",
    "l_29": "",
    "l_30": "kmxrfnnxgqmsfdkmtfsd",
    "uuid_identification": UUID("ae931c24-531b-425b-8b98-496d7a816fe9"),
    "created_at": "2022-03-25T23:16:16.139984+00:00",
    "modified_at": "2022-03-25T23:16:16.139984+00:00",
}

POSITIONS_LIST = [
    0,
    22,
    1,
    2,
    3,
    4,
    5,
    6,
    23,
    7,
    8,
    9,
    10,
    11,
    12,
    13,
    14,
    15,
    20,
    16,
    17,
    18,
    19,
    21,
    24,
]


FISRT_LINE = (
    '"brylpgokecmkcrwbcqwz";"cfizirlmrltglxwtfqng";"zoendkprthwslupzavoe";"iafiejwdlbufxlzhkoos";'
    '"tizumxngxtwffqbavemn";"hplmfgukjvxpiyrcdktf";"sxlbqblmanaxbwlnrxyg";"anrucgozvgozzifaqqrj";'
    '"";"akvvgbmanlerkhyyuwnn";"fxsybylzlbtrukamjtdc";"tfweqchfnfscflgcgogf";'
    '"ddbmwuyiljxabcyhseal";"vmfmclchamofbubbykio";"paacuspbhvxfthywrjmp";"ashdfvkyxroezwurtuoo";'
    '"kpnubwvxydvmqylckcvg";"iastmjhjqbkoiizymjao";"bxwauugvyeihxcrxvfeo";"aalybgnyzvpmashqsani";'
    '"bipglrpilsgwxvdymvlx";"eclwefcktuhrbvfzfjqo";"aaihsksivddlgdbhdbfk";"xgcfpmoratvepysrlcmn";'''
    '"kmxrfnnxgqmsfdkmtfsd"\r\n'
)


FISRT_LINE_AJOUTS = (
    '"brylpgokecmkcrwbcqwz";"cfizirlmrltglxwtfqng";"zoendkprthwslupzavoe";"iafiejwdlbufxlzhkoos";'
    '"tizumxngxtwffqbavemn";"hplmfgukjvxpiyrcdktf";"sxlbqblmanaxbwlnrxyg";"anrucgozvgozzifaqqrj";'
    '"";"akvvgbmanlerkhyyuwnn";"fxsybylzlbtrukamjtdc";"tfweqchfnfscflgcgogf";'
    '"ddbmwuyiljxabcyhseal";"vmfmclchamofbubbykio";"paacuspbhvxfthywrjmp";"ashdfvkyxroezwurtuoo";'
    '"kpnubwvxydvmqylckcvg";"iastmjhjqbkoiizymjao";"bxwauugvyeihxcrxvfeo";"aalybgnyzvpmashqsani";'
    '"bipglrpilsgwxvdymvlx";"eclwefcktuhrbvfzfjqo";"aaihsksivddlgdbhdbfk";"xgcfpmoratvepysrlcmn";'''
    '"kmxrfnnxgqmsfdkmtfsd";"ae931c24-531b-425b-8b98-496d7a816fe9";'
    '"2022-03-25T23:16:16.139984+00:00";"2022-03-25T23:16:16.139984+00:00"\r\n'
)


def add_uuid():
    return UUID("ae931c24-531b-425b-8b98-496d7a816fe9")


ADD_FIELDS_DICT = {
    "uuid_identification": (add_uuid, {}),
    "created_at": "2022-03-25T23:16:16.139984+00:00",
    "modified_at": "2022-03-25T23:16:16.139984+00:00",
}

FILE = Path(settings.APPS_DIR) / "core/tests/test_fixtures/function_imports_fixtures.csv"
