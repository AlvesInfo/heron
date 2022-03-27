# pylint: disable=E0401,R0201,R0902,R0913,W0212,W0105
"""Module pour les tests des fonction_imports

Commentaire:

created at: 2021-10-30
created by: Paulo ALVES

modified at: 2021-10-30
modified by: Paulo ALVES
"""
from uuid import UUID

from apps.core.modules.data_flux.test_fixtures.loaders_contants import (
    COLUMNS_DICT_NONE,
    COLUMNS_DICT_INT,
    COLUMNS_DICT_NAMED,
    DICT_TO_TEST,
    DICT_TO_TEST_AJOUTS,
    PARAMS_DICT,
    POSITIONS_LIST,
    FISRT_LINE,
    FISRT_LINE_AJOUTS,
    FILE,
)
from apps.core.modules.data_flux.loaders import FileLoader

"""
méthodes pour la class FileLoader à tester :
    close_buffer
    get_positons_for_none_columns
    get_positions_if_columns_named
    get_header
    get_add_dict
    get_add_values
    read_dict
    write_io
"""
# TODO : finaliser les test complets de FileLoader, car il y a des méthodes
#  dont tous les paramètres n'ont pas été testés


class TestFileLoader:
    """Test de la class FileLoader du module function_imports"""

    def test_get_positons_for_none_columns(self):
        """Test de récupération de la postions des colonnes à récupérer"""
        with FileLoader(
            source=FILE,
            columns_dict=COLUMNS_DICT_NONE,
            first_line=2,
        ) as file_to_insert:
            assert file_to_insert.get_positons_for_none_columns() == list(range(25))

    def test_get_positions_if_columns_named(self):
        """Test de récupération de la postions des colonnes à récupérer"""
        with FileLoader(
            source=FILE,
            columns_dict=COLUMNS_DICT_NAMED,
            first_line=1,
        ) as file_to_insert:
            assert file_to_insert.get_positions_if_columns_named() == POSITIONS_LIST

    def test_get_header(self):
        """Test de récupération de la postions des colonnes à récupérer"""
        with FileLoader(
            source=FILE,
            first_line=2,
            columns_dict=COLUMNS_DICT_NONE,
        ) as file_to_insert:
            assert file_to_insert.get_header() == list(range(25))

    def test_get_header_int(self):
        """Test de récupération de la postions des colonnes à récupérer"""
        with FileLoader(
            source=FILE,
            first_line=2,
            columns_dict=COLUMNS_DICT_INT,
        ) as file_to_insert:
            assert file_to_insert.get_header() == POSITIONS_LIST

    def test_get_header_name(self):
        """Test de récupération de la postions des colonnes à récupérer"""
        with FileLoader(
            source=FILE,
            first_line=1,
            columns_dict=COLUMNS_DICT_NAMED,
        ) as file_to_insert:
            assert file_to_insert.get_header() == POSITIONS_LIST

    def test_get_add_dict(self):
        """Test si l'on fait un ajout d'attribus à chaques lignes"""
        with FileLoader(
            source=FILE,
            first_line=2,
            columns_dict=COLUMNS_DICT_NONE,
            params_dict=PARAMS_DICT,
        ) as file_to_insert:

            assert file_to_insert.get_add_dict == {
                "uuid_identification": UUID("ae931c24-531b-425b-8b98-496d7a816fe9"),
                "created_at": "2022-03-25T23:16:16.139984+00:00",
                "modified_at": "2022-03-25T23:16:16.139984+00:00",
            }

    def test_get_add_values(self):
        """Test si l'on fait un ajout d'attribus à chaques lignes"""
        with FileLoader(
            source=FILE,
            first_line=2,
            columns_dict=COLUMNS_DICT_NONE,
            params_dict=PARAMS_DICT,
        ) as file_to_insert:

            assert file_to_insert.get_add_values == [
                UUID("ae931c24-531b-425b-8b98-496d7a816fe9"),
                "2022-03-25T23:16:16.139984+00:00",
                "2022-03-25T23:16:16.139984+00:00",
            ]

    def test_chunk_dict(self):
        """Test avec COLUMNS_DICT_NONE sans ajouts"""
        with FileLoader(
            source=FILE,
            first_line=2,
            columns_dict=COLUMNS_DICT_NONE,
        ) as file_to_insert:
            for row in file_to_insert.read_dict():
                assert row == DICT_TO_TEST

    def test_chunk_dict_avec_ajouts(self):
        """Test avec COLUMNS_DICT_NONE avec ajouts"""
        with FileLoader(
            source=FILE,
            first_line=2,
            columns_dict=COLUMNS_DICT_NONE,
            params_dict=PARAMS_DICT,
        ) as file_to_insert:
            for row in file_to_insert.read_dict():
                assert row == DICT_TO_TEST_AJOUTS

    def test_chunk_dict_int(self):
        """Test avec COLUMNS_DICT_INT"""
        with FileLoader(
            source=FILE,
            first_line=2,
            columns_dict=COLUMNS_DICT_INT,
        ) as file_to_insert:
            for row in file_to_insert.read_dict():
                assert row == DICT_TO_TEST

    def test_chunk_dict_name(self):
        """Test avec COLUMNS_DICT_INT"""
        with FileLoader(
            source=FILE,
            first_line=1,
            columns_dict=COLUMNS_DICT_NAMED,
        ) as file_to_insert:
            for row in file_to_insert.load(read_methode="data_dict"):
                assert row == DICT_TO_TEST

    def test_write_io(self):
        """Test de lecture ligne à ligne des données cleanées"""
        with FileLoader(
            source=FILE,
            first_line=1,
            columns_dict=COLUMNS_DICT_NAMED,
        ) as file_to_insert:
            for row in file_to_insert.load(read_methode="data"):
                assert row == FISRT_LINE

    def test_write_io_ajouts(self):
        """Test de lecture ligne à ligne des données cleanées"""
        with FileLoader(
            source=FILE,
            first_line=1,
            columns_dict=COLUMNS_DICT_NAMED,
            params_dict=PARAMS_DICT,
        ) as file_to_insert:
            for row in file_to_insert.load(read_methode="data"):
                assert row == FISRT_LINE_AJOUTS


def test_excel_file_to_csv_string_io():
    """Test de la transformation d'un fichier Excel en csv"""
    # TODO : Ecrire la fonction de test complète : test_excel_file_to_csv_string_io
    assert 1 == int("1")
