# pylint: disable=E0401,W0621
"""
FR : Tests du module d'essai de validation djantic (apps/accountancy/validations/djantic_sage.py)
EN : Tests for djantic validation trial module

created at: 2026-10-10
created by: Paulo ALVES
"""
import logging

import pytest
from pydantic import BaseModel, ValidationError
from pydantic.error_wrappers import ErrorWrapper

from apps.accountancy.forms.forms_djantic.sage import TabDivSageSchema
from apps.accountancy.models import SectionSage, TabDivSage
from apps.accountancy.validations import djantic_sage
from conftest import patched_attrs


def test_main_valide_en_boucle(caplog, monkeypatch):
    """main() valide TabDivSageSchema en boucle et affiche le temps (boucle réduite à 3 itérations)"""
    caplog.set_level(logging.INFO, logger="validation")
    with patched_attrs(monkeypatch, djantic_sage, range=lambda _n: iter(range(3))):
        djantic_sage.main()

    out = caplog.text

    assert out.count("'num_table': 6100") == 3
    assert "3 {" in out
    assert "validation par djantic en" in out


def test_main_affiche_les_erreurs_de_validation(caplog, monkeypatch):
    """Si le schéma lève une ValidationError, main() l'affiche sans interrompre la boucle"""
    caplog.set_level(logging.INFO, logger="validation")

    def _raise(**_kwargs):
        raise ValidationError([ErrorWrapper(ValueError("boom"), loc="code")], TabDivSageSchema)

    with patched_attrs(monkeypatch, djantic_sage, range=lambda _n: iter(range(2)), TabDivSageSchema=_raise):
        djantic_sage.main()

    out = caplog.text

    assert sum("boom" in record.getMessage() for record in caplog.records) == 2
    assert "validation par djantic en" in out


def test_essai_section_sage_schema_affiche_les_erreurs(caplog):
    """chargeable="zzz" n'est pas un booléen : l'erreur est reformatée avec la valeur reçue"""
    caplog.set_level(logging.INFO, logger="validation")
    djantic_sage.essai_SectionSagechema()

    out = caplog.text

    assert out.count("isinstance :  True") == 2
    assert "'type': 'type_error.bool'" in out
    assert (
        "{'chargeable': [{'message': 'value could not be parsed to a boolean', "
        "'data_received': 'zzzzzzzzzzzz'}]}"
    ) in out
    assert str(TabDivSage.get_columns_import()) in out
    assert "validation par djantic en" in out


def test_essai_section_sage_schema_sans_erreur(caplog, monkeypatch):
    """Si la validation passe, seul le temps et les colonnes sont affichés"""
    caplog.set_level(logging.INFO, logger="validation")
    with patched_attrs(monkeypatch, djantic_sage, SectionSageDjanticSchema=lambda **_kwargs: None):
        djantic_sage.essai_SectionSagechema()

    out = caplog.text

    assert "type_error.bool" not in out
    assert "validation par djantic en" in out


def test_schemas_d_essai():
    """Les deux schémas d'essai : pydantic pur, et djantic dont le champ `test` hors include est ignoré"""
    assert issubclass(djantic_sage.SectionSagePydanticSchema, BaseModel)
    assert list(djantic_sage.SectionSagePydanticSchema.__fields__) == ["axe", "section", "name", "short_name", "chargeable"]
    assert djantic_sage.SectionSageDjanticSchema.Config.model is SectionSage
    assert djantic_sage.SectionSageDjanticSchema.Config.include == list(SectionSage.get_columns_import())
    assert "test" not in djantic_sage.SectionSageDjanticSchema.__fields__
    # axe est une FK : djantic attend la clé primaire entière ("001" du script est parsé en 1)
    assert djantic_sage.SectionSageDjanticSchema(axe="001", section="S1").axe == 1

    with pytest.raises(ValidationError):
        djantic_sage.SectionSageDjanticSchema(axe="001", section="S1", chargeable="zzz")
