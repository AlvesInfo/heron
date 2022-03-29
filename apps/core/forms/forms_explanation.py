import datetime

from django import forms

from apps.core.functions.functions_setups import settings
from apps.core.validations.forms_base import SageNullBooleanField, TildeTextField
from apps.accountancy.models import (
    SectionSage,
)


class SectionSageForm(forms.ModelForm):
    """Validation de l'import ZBICCE des Sections Sage X3"""

    chargeable = SageNullBooleanField()
    name = TildeTextField()
    short_name = TildeTextField()

    class Meta:
        """class Meta du forms.ModelForm django"""

        model = SectionSage
        fields = [
            "axe",
            "section",
            "name",
            "short_name",
            "chargeable",
            "regroup_01",
            "regroup_02",
        ]


class SectionSageFormForm(forms.Form):
    """Validation de l'import ZBICCE des Sections Sage X3"""

    chargeable = SageNullBooleanField()
    name = TildeTextField()
    short_name = TildeTextField()


def forms_django():
    """Les erreurs dans un form:
    form.errors.as_data()  -> Dictionnaire avec une instance de ValidationError
        ex. : {
                'axe': [ValidationError([
                                        'Sélectionnez un choix valide.
                                        Ce choix ne fait pas partie de ceux disponibles.'
                            ])
                        ],
                'section': [ValidationError(['Ce champ est obligatoire.'])],
                'chargeable': [ValidationError(['Ce champ est obligatoire.'])],
                'name': [ValidationError([
                                        'Assurez-vous que cette valeur
                                        comporte au plus 30 caractères (actuellement 78).'
                            ])
                        ],
                }

    form.errors.get_json_data() -> Dictionnaire
        ex. : {
                'axe': [{
                            'message': 'Sélectionnez un choix valide.
                                        Ce choix ne fait pas partie de ceux disponibles.',
                            'code': 'invalid_choice'
                        }],
                'section': [{
                            'message': 'Ce champ est obligatoire.',
                            'code': 'required'
                            }],
                'chargeable': [{
                                'message': 'Ce champ est obligatoire.',
                                'code': 'required'
                            }],
                'name': [{
                            'message': 'Assurez-vous que cette valeur
                                        comporte au plus 30 caractères (actuellement 78).',
                            'code': 'max_length'
                        }],
                }

    form.errors.get_json_data() -> Json formaté avec des charactères html comme é = \u00e9

    form.errors.as_ul() -> c'est un format HTML l'erreur dans des balises ul et li,
                           format par défaut, __str__ de la class ErrorDict
                           de django fichier : Lib/site-packages/django/forms/utils.py
    """

    a_dict = {
        "axe": datetime.datetime.today().isoformat(),
        "name": "zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz",
        "short_name": "short_name",
    }
    f = SectionSageForm(a_dict)
    error_dict = {
        key: [
            {
                "message": str(value),
                "data_received": "aucune valeur reçue"
                if f.data.get(key) is None
                else f.data.get(key),
            }
            for value in row
        ]
        for key, row in f.errors.items()
    }
    print(f.errors.items())
    print(error_dict)
    # print("f.is_valid() : ", f.is_valid())
    # errors = f.errors
    # print(f"errors.get_json_data() : {errors.get_json_data()}")
    # print(f"f.data : {f.data}")
    #
    # print("zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz")
    #
    # f = SectionSageFormForm(a_dict)
    # print("f.is_valid() : ", f.is_valid())
    # errors = f.errors
    # print(f"errors.get_json_data() : {errors.get_json_data()}")


if __name__ == "__main__":
    forms_django()
    # from apps.data_flux.models import Trace, Line, Error
    # num_line = None
    # e_dict = {
    #     "champ_00": [
    #         {
    #             "message": "message_01",
    #             "data_expexted": "donnée_01 attendue",
    #             "data_received": "donnée_01 reçue",
    #         },
    #         {
    #             "message": "message_02",
    #             "data_expexted": "donnée_02 attendue",
    #             "data_received": "donnée_02 reçue",
    #         },
    #     ],
    #     "champ_02": [
    #         {
    #             "message": "message_01",
    #             "data_expexted": "donnée_01 attendue",
    #             "data_received": "donnée_01 reçue",
    #         },
    #     ],
    # }
    # trace = Trace.objects.get(pk=1)
    # line_object = Line.objects.create(
    #     trace=trace,
    #     insertion_type="Errors",
    #     line=num_line,
    #     designation="une erreur c'est produite"
    # )
    #
    # Error.objects.bulk_create(
    #     [
    #         Error(
    #             line=line_object,
    #             attribute=attribute,
    #             message=messages_dict.get("message"),
    #             data_expected=messages_dict.get("data_expected"),
    #             data_received=messages_dict.get("data_received"),
    #         )
    #         for attribute, errors_list in e_dict.items()
    #         for messages_dict in errors_list
    #     ]
    # )
