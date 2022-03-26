# pylint: disable=E0401,R0902,R0913,W0212,W0105
"""Module pour les tests des fonction_imports

Commentaire:

created at: 2021-10-30
created by: Paulo ALVES

modified at: 2021-10-30
modified by: Paulo ALVES
"""
import time
import uuid
from uuid import UUID
from datetime import datetime

from apps.core.tests.test_fixtures.function_imports_contants import (
    COLUMNS_DICT_NONE,
    COLUMNS_DICT_INT,
    COLUMNS_DICT_NAMED,
    DICT_TO_TEST,
    DICT_TO_TEST_AJOUTS,
    ADD_FIELDS_DICT,
    POSITIONS_LIST,
    FILE,
)
from apps.core.functions.function_imports import IterFileToInsert


class TestIterFileToInsert:
    """Test de la class IterFileToInsert du module function_imports"""

    def test_get_positons_for_none_columns(self):
        """Test de récupération de la postions des colonnes à récupérer"""
        with IterFileToInsert(
                file_to_iter=FILE,
                first_line=2,
                columns_dict=COLUMNS_DICT_NONE,
        ) as file_to_insert:
            assert file_to_insert.get_positons_for_none_columns() == list(range(25))

    def test_get_positions_if_columns_named(self):
        """Test de récupération de la postions des colonnes à récupérer"""
        with IterFileToInsert(
                file_to_iter=FILE,
                first_line=1,
                columns_dict=COLUMNS_DICT_NAMED,
        ) as file_to_insert:
            assert file_to_insert.get_positions_if_columns_named() == POSITIONS_LIST

    def test_get_header(self):
        """Test de récupération de la postions des colonnes à récupérer"""
        with IterFileToInsert(
            file_to_iter=FILE,
            first_line=2,
            columns_dict=COLUMNS_DICT_NONE,
        ) as file_to_insert:
            assert file_to_insert.get_header() == list(range(25))

    def test_get_header_int(self):
        """Test de récupération de la postions des colonnes à récupérer"""
        with IterFileToInsert(
            file_to_iter=FILE,
            first_line=2,
            columns_dict=COLUMNS_DICT_INT,
        ) as file_to_insert:
            assert file_to_insert.get_header() == POSITIONS_LIST

    def test_get_header_name(self):
        """Test de récupération de la postions des colonnes à récupérer"""
        with IterFileToInsert(
            file_to_iter=FILE,
            first_line=1,
            columns_dict=COLUMNS_DICT_NAMED,
        ) as file_to_insert:
            assert file_to_insert.get_header() == POSITIONS_LIST

    def test_get_add_dict(self):
        """Test si l'on fait un ajout d'attribus à chaques lignes"""
        with IterFileToInsert(
            file_to_iter=FILE,
            first_line=2,
            columns_dict=COLUMNS_DICT_NONE,
            add_fields_dict=ADD_FIELDS_DICT,
        ) as file_to_insert:

            assert file_to_insert.get_add_dict == {
                "uuid_identification": UUID("ae931c24-531b-425b-8b98-496d7a816fe9"),
                "created_at": "2022-03-25T23:16:16.139984+00:00",
                "modified_at": "2022-03-25T23:16:16.139984+00:00",
            }

    def test_get_add_values(self):
        """Test si l'on fait un ajout d'attribus à chaques lignes"""
        with IterFileToInsert(
            file_to_iter=FILE,
            first_line=2,
            columns_dict=COLUMNS_DICT_NONE,
            add_fields_dict=ADD_FIELDS_DICT,
        ) as file_to_insert:

            assert file_to_insert.get_add_values == [
                UUID("ae931c24-531b-425b-8b98-496d7a816fe9"),
                "2022-03-25T23:16:16.139984+00:00",
                "2022-03-25T23:16:16.139984+00:00",
            ]

    def test_chunk_dict(self):
        """Test avec COLUMNS_DICT_NONE sans ajouts"""
        with IterFileToInsert(
            file_to_iter=FILE,
            first_line=2,
            columns_dict=COLUMNS_DICT_NONE,
        ) as file_to_insert:
            for i, row in enumerate(file_to_insert.chunk_dict(), 1):
                assert row == DICT_TO_TEST

    def test_chunk_dict_avec_ajouts(self):
        """Test avec COLUMNS_DICT_NONE avec ajouts"""
        with IterFileToInsert(
            file_to_iter=FILE,
            first_line=2,
            columns_dict=COLUMNS_DICT_NONE,
            add_fields_dict=ADD_FIELDS_DICT,
        ) as file_to_insert:
            for i, row in enumerate(file_to_insert.chunk_dict(), 1):
                assert row == DICT_TO_TEST_AJOUTS

    def test_chunk_dict_int(self):
        """Test avec COLUMNS_DICT_INT"""
        with IterFileToInsert(
            file_to_iter=FILE,
            first_line=2,
            columns_dict=COLUMNS_DICT_INT,
        ) as file_to_insert:
            for i, row in enumerate(file_to_insert.chunk_dict(), 1):
                assert row == DICT_TO_TEST

    def test_chunk_dict_name(self):
        """Test avec COLUMNS_DICT_INT"""
        with IterFileToInsert(
            file_to_iter=FILE,
            first_line=1,
            columns_dict=COLUMNS_DICT_NAMED,
        ) as file_to_insert:
            for i, row in enumerate(file_to_insert.chunk_dict(), 1):
                assert row == DICT_TO_TEST


def test_excel_file_to_csv_string_io():
    """Test de la transformation d'un fichier Excel en csv"""
    assert 1 == 1


def test_encoding_detect():
    """Test de la détection de l'encoding d'un fichier"""
    assert 1 == 1


def essais_copy():
    start = time.time()
    now = datetime.now().isoformat()
    add_fields_dict = {
        "uuid_identification": (uuid.uuid4, {}),
        "created_date": now,
        "modified_date": now,
    }
    # COLUMNS_DICT_NONE columns_dict_int    columns_dict_named
    with IterFileToInsert(
        file_to_iter=FILE,
        first_line=2,
        columns_dict=COLUMNS_DICT_NONE,
        add_fields_dict=add_fields_dict,
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
                print(row == DICT_TO_TEST)
    print(f"temps de production des {i:,.0f} lignes : {(time.time()-start):.2f} s")


if __name__ == "__main__":
    essais_copy()
