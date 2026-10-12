# pylint: disable=E0401,W0621,W0212
"""
FR : Tests de la validation des flux (apps/data_flux/validation.py) : traces d'erreurs par type de
     validateur, gabarits de validation Django / DRF / Pydantic et classe Validation
EN : Tests for flux validation module

created at: 2026-10-11
created by: Paulo ALVES
"""
import io
import uuid

import pytest
from django import forms
from pydantic import BaseModel, validator
from rest_framework import serializers

from apps.data_flux.exceptions import FluxtypeError, IsValidError, ValidationError, ValidationFormError
from apps.data_flux.models import Error, EssaisZ, Line, Trace
from apps.data_flux.validation import (
    DjangoTrace,
    DjangoValidation,
    DrfTrace,
    DrfValidation,
    PydanticTrace,
    PydanticValidation,
    TraceTemplate,
    Validation,
    ValidationTemplate,
    get_columns,
)

pytestmark = pytest.mark.django_db


class EssaisForm(forms.ModelForm):
    """Formulaire Django d'essai"""

    class Meta:
        model = EssaisZ
        fields = ("col_texte", "col_int")


class EssaisSerializer(serializers.ModelSerializer):
    """Sérialiseur DRF d'essai"""

    class Meta:
        model = EssaisZ
        fields = ("col_texte", "col_int")


class EssaisSchema(BaseModel):
    """Schéma pydantic d'essai, avec les colonnes à écrire comme un schéma djantic"""

    col_texte: str
    col_int: int

    class Config:
        include = ("col_texte", "col_int")


class RefusingSchema(BaseModel):
    """Schéma dont le validateur lève la ValidationError du module (pas celle de pydantic)"""

    col_texte: str

    @validator("col_texte")
    def refuse(cls, value):  # noqa: N805  pylint: disable=E0213
        raise ValidationError(f"{value} refusé")


class CrashingSchema(BaseModel):
    """Schéma dont le validateur lève une erreur inattendue (ni pydantic ni module)"""

    col_texte: str

    @validator("col_texte")
    def crash(cls, value):  # noqa: N805  pylint: disable=E0213
        raise RuntimeError(f"{value} imprévu")


PARAMS = {"trace_name": "Test", "file_name": "essai.csv", "application_name": "tests", "flow_name": "essais"}


def _params(**extra):
    return {**PARAMS, "file_io": io.StringIO(), **extra}


# TRACES ===========================================================================================


def test_trace_template_initialise_ou_reprend_une_trace(make_trace):
    created = TraceTemplate({**PARAMS, "comment": "c"})
    existing = make_trace()
    reused = TraceTemplate({"trace": existing, "trace_uuid": existing.uuid_identification})

    assert Trace.objects.get(pk=created.trace.pk).trace_name == "Test"
    assert created.trace.uuid_identification == created.trace_number
    assert created.errors is False
    assert reused.trace == existing
    assert reused.trace_number == existing.uuid_identification

    with pytest.raises(NotImplementedError):
        created.get_formatted_error(None)


def test_trace_template_lignes_et_erreur_brute():
    """Lignes typées avec désignation par défaut, erreur brute (message) tracée sans validateur"""
    trace = TraceTemplate(PARAMS)
    line = trace.add_line("Create", 3)
    custom = trace.add_line("Passed", 4, "sautée")
    trace.add_error(5, "flux invalide")

    errors = Error.objects.get()
    assert (line.insertion_type, line.num_line, line.designation) == ("Create", 3, "cette ligne à bien été créée")
    assert custom.designation == "sautée"
    assert trace.errors is True
    assert (errors.line.insertion_type, errors.line.num_line) == ("Errors", 5)
    assert (errors.attr_name, errors.message, errors.data_received) == ("validation", "flux invalide", "aucune valeur reçue")


def test_trace_template_save_compte_les_lignes():
    trace = TraceTemplate(PARAMS)
    for insertion_type in ("Create", "Create", "Update", "Passed", "Unknown"):
        trace.add_line(insertion_type)
    trace.add_error(1, "erreur")

    trace.save()

    saved = Trace.objects.get(pk=trace.trace.pk)
    assert (saved.created_numbers_records, saved.updated_numbers_records, saved.errors_numbers_records, saved.unknown_numbers_records) == (2, 1, 1, 1)
    assert saved.errors is True
    assert saved.final_at is not None


def test_django_trace_formate_les_erreurs_du_formulaire():
    form = EssaisForm(data={"col_texte": "x" * 20, "col_int": ""})
    form.is_valid()

    formatted = DjangoTrace(PARAMS).get_formatted_error(form)

    assert formatted["col_int"] == [{"message": "Ce champ est obligatoire.", "data_received": "aucune valeur reçue"}]
    assert formatted["col_texte"][0]["data_received"] == "x" * 20
    assert "12 caractères" in formatted["col_texte"][0]["message"]


def test_drf_trace_formate_les_erreurs_du_serialiseur():
    serializer = EssaisSerializer(data={"col_texte": "x" * 20})
    serializer.is_valid()

    formatted = DrfTrace(PARAMS).get_formatted_error(serializer)

    assert formatted["col_int"] == [{"message": "Ce champ est obligatoire.", "data_received": "aucune valeur reçue"}]
    assert formatted["col_texte"][0]["data_received"] == "x" * 20

    trace = DrfTrace(PARAMS)
    serializer = EssaisSerializer(data={})

    with pytest.raises(IsValidError):
        trace.get_formatted_error(serializer)


def test_pydantic_trace_formate_les_erreurs():
    errors = [{"loc": ("col_int",), "msg": "value is not a valid integer"}, {"loc": ("col_texte",), "msg": "field required"}]

    formatted = PydanticTrace(PARAMS).get_formatted_error((errors, {"col_int": "abc"}))

    assert formatted == {
        "col_int": [{"message": "value is not a valid integer", "data_received": "abc"}],
        "col_texte": [{"message": "field required", "data_received": "aucune valeur reçue"}],
    }


# GABARITS DE VALIDATION ===========================================================================


def test_get_columns():
    assert get_columns(EssaisSchema, ["autre"]) == ["col_texte", "col_int"]
    assert get_columns(EssaisForm, {"col_int": 1, "col_texte": "a"}) == ["col_int", "col_texte"]


def test_validation_template_methodes_abstraites():
    """Lignes et sauvegarde déléguées à la trace, validation unitaire abstraite"""
    template = ValidationTemplate((EssaisSchema, PydanticTrace), iter([{"col_texte": "a"}]), _params())
    template._add_line("Passed", 2, "sautée")
    template._save_errors_trace()

    assert template.first_element == {"col_texte": "a"}
    assert Line.objects.get().designation == "sautée"
    assert Trace.objects.get().final_at is not None

    with pytest.raises(NotImplementedError):
        template.is_valid(EssaisSchema, {}, None)


def test_validate_flux_qui_n_est_pas_un_dictionnaire():
    """Un flux de listes est refusé et tracé, la trace est sauvegardée"""
    validation = PydanticValidation((EssaisSchema, PydanticTrace), iter([["a", 1]]), _params())

    with pytest.raises(FluxtypeError):
        validation.validate()

    error = Error.objects.get()
    assert error.line.num_line == 0
    assert "La validation n'a pu avoir lieu" in error.message
    assert Trace.objects.get().errors is True


def test_validate_erreur_inattendue_dans_la_validation(caplog):
    """Une exception du validateur est tracée en ligne 0 puis remontée en ValidationFormError"""
    validation = PydanticValidation((CrashingSchema, PydanticTrace), iter([{"col_texte": "a"}]), _params())

    with pytest.raises(ValidationFormError):
        validation.validate()

    assert "Une erreur c'est produite à l'appel de validate" in Error.objects.get().message
    assert "Erreur sur ValidationTemplate.validate" in caplog.text


def test_validate_pydantic_lignes_en_erreur_et_limite():
    """Les lignes valides sont écrites, les lignes en erreur tracées, arrêt au maximum d'erreurs"""
    rows = [{"col_texte": "ok", "col_int": 1}, {"col_texte": "ko", "col_int": "x"}, {"col_texte": "ko2", "col_int": "y"}, {"col_texte": "jamais", "col_int": "z"}]
    params = _params(nb_errors_max=2)
    validation = PydanticValidation((EssaisSchema, PydanticTrace), iter(rows), params)

    error_lines = validation.validate()

    assert error_lines == {2, 3}
    assert params["file_io"].getvalue() == '"ok";"1"\n'
    assert Line.objects.filter(insertion_type="Errors").count() == 2
    assert Error.objects.filter(attr_name="col_int").count() == 2
    assert Trace.objects.get().errors_numbers_records == 2


def test_validate_pydantic_sans_limite_d_erreurs():
    params = _params(nb_errors_max=0)
    validation = PydanticValidation((EssaisSchema, PydanticTrace), iter([{"col_texte": "ko", "col_int": "x"}] * 3), params)

    assert validation.validate() == {1, 2, 3}


def test_pydantic_is_valid_avec_la_validation_error_du_module():
    """Une ValidationError du module (sans méthode errors) est formatée sur le champ global"""
    buffer = io.StringIO()
    validation = PydanticValidation((RefusingSchema, PydanticTrace), iter([{"col_texte": "a"}]), _params())

    assert validation.is_valid(RefusingSchema, {"col_texte": "a"}, None) == ([{"loc": ("__all__",), "msg": "a refusé"}], {"col_texte": "a"})
    assert validation.is_valid(EssaisSchema, {"col_texte": "a", "col_int": 2}, __import__("csv").writer(buffer)) is False
    assert buffer.getvalue().strip() == "a,2"


def test_django_validation():
    """Formulaire Django : ligne valide écrite (champs nettoyés), erreurs renvoyées sinon"""
    params = _params()
    validation = DjangoValidation((EssaisForm, DjangoTrace), iter([{"col_texte": "ok", "col_int": "7"}, {"col_texte": "", "col_int": "x"}]), params)

    assert validation.validate() == {2}
    assert params["file_io"].getvalue() == '"ok";"7"\n'
    assert set(Error.objects.values_list("attr_name", flat=True)) == {"col_texte", "col_int"}


def test_drf_validation():
    """Sérialiseur DRF : ligne valide écrite depuis les données, erreurs renvoyées sinon"""
    params = _params()
    validation = DrfValidation((EssaisSerializer, DrfTrace), iter([{"col_texte": "ok", "col_int": 7}, {"col_texte": "x" * 20, "col_int": 1}]), params)

    assert validation.validate() == {2}
    assert params["file_io"].getvalue() == '"ok";"7"\n'
    assert Error.objects.get().attr_name == "col_texte"


# CLASSE VALIDATION ================================================================================


def test_validation_parametres_par_defaut_et_dispatch():
    """Valeurs par défaut posées, gabarit choisi selon le type du validateur"""
    params = _params()
    del params["application_name"]
    del params["flow_name"]
    pydantic_validation = Validation(iter([{"col_texte": "a", "col_int": 1}]), EssaisZ, EssaisSchema, params)

    assert params["application_name"] == "unkown"
    assert params["flow_name"] == "unkown"
    assert params["nb_errors_max"] == 100
    assert params["insert_method"] == "insert"
    assert isinstance(pydantic_validation.to_validate, PydanticValidation)
    assert isinstance(pydantic_validation.to_validate.trace_instance, PydanticTrace)
    assert isinstance(Validation(iter([{}]), EssaisZ, EssaisForm, _params()).to_validate, DjangoValidation)
    assert isinstance(Validation(iter([{}]), EssaisZ, EssaisSerializer, _params()).to_validate, DrfValidation)


def test_validation_avec_le_couple_de_classes_explicite():
    """Paramètres déjà renseignés conservés, couple de classes explicite respecté"""
    explicit = Validation(iter([{}]), EssaisZ, None, _params(validation=(DjangoValidation, DjangoTrace), nb_errors_max=5, insert_method="upsert"))

    assert isinstance(explicit.to_validate, DjangoValidation)
    assert explicit.to_validate.validator_class is None
    assert (explicit.params_dict["nb_errors_max"], explicit.params_dict["insert_method"]) == (5, "upsert")


@pytest.mark.parametrize(
    ("params", "message"),
    [
        ({}, "doit être un tuple ou une liste"),
        ({"validation": (DjangoValidation,)}, "doit être un tuple ou une liste"),
        ({"validation": (str, DjangoTrace)}, "sous-classe de ValidationTemplate"),
        ({"validation": (DjangoValidation, "trace")}, "sous-classe de TraceTemplate"),
    ],
)
def test_validation_couple_de_classes_invalide(params, message):
    rows = iter([{}])
    validation_params = _params(**params)

    with pytest.raises(ValidationFormError, match=message):
        Validation(rows, EssaisZ, None, validation_params)


def test_validation_type_de_validateur_inconnu():
    rows = iter([{}])
    validator = uuid.uuid4()
    validation_params = _params()

    with pytest.raises(ValidationFormError, match="est inconnu"):
        Validation(rows, EssaisZ, validator, validation_params)


def test_validation_validate_de_bout_en_bout():
    params = _params()
    params["file_io"].write("ancien contenu")
    validation = Validation(iter([{"col_texte": "ok", "col_int": 1}, {"col_texte": "ko", "col_int": "x"}]), EssaisZ, EssaisSchema, params)

    assert validation.validate() == {2}
    assert params["file_io"].getvalue().startswith('"ok";"1"\n')
    assert Trace.objects.get().errors_numbers_records == 1
