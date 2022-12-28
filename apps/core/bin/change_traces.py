# pylint: disable=C0411,E0401,W0105,W0212,E1101,W1203
"""Module d'enregistrement de tous les changement en opération CRUD de l'application

Commentaire:

created at: 2022-03-22
created by: Paulo ALVES

modified at:
modified by:
"""
import inspect
from copy import deepcopy

from django import forms
from django.forms import model_to_dict
from django.utils import timezone
from django.views.generic import CreateView, UpdateView, DeleteView
from django.db import models

from heron.loggers import LOGGER_VIEWS
from apps.core.models import ChangesTrace

ACTION_DICT = {
    "DELETE": 0,
    "CREATE": 1,
    "UPDATE": 2,
    "UNDIFINED": 9,
}


def get_difference_dict(before, after):
    """Retourne seulement des differences
    :param before: avant changement
    :param after: après changement
    :return:
    """
    before_set = set(before.items())
    after_set = set(after.items())

    return {
        "avant": dict(sorted(before_set - after_set)),
        "après": dict(sorted(after_set - before_set)),
    }


class ChangeTraceMixin:
    """
    Decorator qui sauvegarde les changements dans les données.

        class Classe(ChangeTraceMixin):
            ....
    """

    request = None
    object_before = {}
    object = None
    mark_delete = None
    action_type = None

    def initialisation(self, object_model, mark_delete: bool = None):
        """Surcharge pour l'instanciation quand cette class mixin, est utilisée directement.
        :param object_model: surcharge de l'attribut, lors d'une instanciation
        :param mark_delete: surcharge de l'attribut, lors d'une instanciation
        """
        self.object = object_model
        self.mark_delete = mark_delete

    def post(self, request, *args, **kwargs):
        """Surcharge de la méthode post, pour avoir les données avant changement"""
        try:
            self.object_before = deepcopy(self.get_object().__dict__)
        except AttributeError:
            """
            Si l'on a une erreur AttributeError, c'est que c'est en création
            et qu'il n'y a donc pas d'attirbut de méthode de class get_object
            """
        return super().post(request, *args, **kwargs)

    def action(self):
        """Renvoie le type d'action réalisée"""

        if self.action_type is None:

            if isinstance(self, (DeleteView,)):
                self.action_type = "DELETE"
            elif isinstance(self, (CreateView,)):
                self.action_type = "CREATE"
            elif isinstance(self, (UpdateView,)):
                self.action_type = "UPDATE"
            else:
                self.action_type = "UNDIFINED"

    def has_change(self, before: dict, after: dict):
        """
        Fonction qui vérifie si le formulaire a changé un élément de l'objet
        :param before: instance du formulaire d'avant
        :param after: instance du formulaire au post
        :return: boolean
        """
        before_to_test = {
            key: str(value) if isinstance(value, (models.fields.files.ImageFieldFile,)) else value
            for key, value in before.items()
            if key not in {"created_at", "modified_at"}
        }
        after_to_test = {
            key: str(value) if isinstance(value, (models.fields.files.ImageFieldFile,)) else value
            for key, value in after.items()
            if key not in {"created_at", "modified_at"}
        }

        # Si les dictionnaires avant et après on des longueurs différentes alors on renvoie True
        if len(before_to_test) != len(after_to_test):
            return True

        # On boucle sur le dictionnaire avant changement pour repérer si il y a eu changement
        for key, value in before_to_test.items():
            test_after_value = after_to_test.get(key, "$,:!cnjEfegvfkgqe")

            # Si la valeur correspondant à la clé est réellement différente ont break
            if test_after_value == "$,:!cnjEfegvfkgqe":
                break

            if test_after_value != value:
                # Si les valeurs sont différentes on va tester si dans la définition du champ,
                # il y a l'attribut blank= True, si c'est le cas et que la différence est
                # entre '' et None c'est qu'il n'y a pas de différences
                # sinon ont break la boucle.
                if not (
                    test_after_value in {"", None}
                    and value in {"", None}
                    and self.object._meta.get_field(key).blank
                ):
                    break

        # S'il n'y a pas eu de break dans la boucle alors cela n'a pas changé
        else:
            return False

        # S'il n'y eu un break dans la boucle alors cela a changé
        return True

    def form_valid(self, form):
        """
        Surcharge de la méthode form_valid, pour enregistrer les données Avant/Après
        et ajouter le niveau de message et sa couleur.
        """
        self.request.session["level"] = 20
        self.object = form.save()
        user = self.request.user

        if self.mark_delete is not None:
            self.object.delete = True
            self.object.delete_by_id = user
            self.object.save()

        before = {key: value for key, value in self.object_before.items() if key != "_state"}
        after = {key: value for key, value in self.object.__dict__.items() if key != "_state"}

        if not self.has_change(before, after):
            self.success_message = "Vous n'avez rien modifié!"
            return super().form_valid(form)

        self.action()

        if self.object_before:
            self.object.modified_by = user
        else:
            self.object.created_by = user

        self.object.save()

        ChangesTrace.objects.create(
            action_datetime=timezone.now(),
            action_type=ACTION_DICT.get(self.action_type, 9),
            function_name=self.__class__,
            action_by=user,
            before=before,
            after=after,
            difference=get_difference_dict(before, after),
            model_name=self.object._meta.model_name,
            model=self.object._meta.model,
            db_table=self.object._meta.db_table,
        )
        return super().form_valid(form)

    def form_invalid(self, form):
        """On surcharge la méthode form_invalid, pour ajouter le niveau de message et sa couleur."""
        self.request.session["level"] = 50
        LOGGER_VIEWS.exception(f"ChangeTraceMixin error : {form.errors!r}")
        return super().form_invalid(form)


def trace_mark_delete(
    request,
    django_model: models.Model,
    data_dict: dict,
    force_delete=False,
):
    """Fonction trace des changements de données, pour views functions flag delete à True
    :param request: request au sens Django
    :param django_model: Model au sens Django
    :param data_dict: données validées, pour le filtre
    :param force_delete: True si l'on souhaite éffacé definitivement
    """
    function_call = str(inspect.currentframe().f_back)[:255]
    model_object = django_model.objects.filter(**data_dict)

    if not model_object:
        LOGGER_VIEWS.exception(
            f"{function_call} error : les données ne retournent aucuns résultats :\n"
            f"{str(data_dict)}"
        )
        request.session["level"] = 50

    user = request.user
    action_datetime = timezone.now()

    for row in model_object:
        request.session["level"] = 20
        before = {key: value for key, value in row.__dict__.items() if key != "_state"}
        row.delete = True
        row.modified_by = user
        row.save()
        after = {key: value for key, value in row.__dict__.items() if key != "_state"}
        ChangesTrace.objects.create(
            action_datetime=action_datetime,
            action_type=0,
            function_name=function_call,
            action_by=user,
            before=before,
            after=after,
            difference=get_difference_dict(before, after),
            model_name=django_model._meta.model_name,
            model=django_model._meta.model,
            db_table=django_model._meta.db_table,
        )

    if force_delete:
        model_object.delete()


def trace_mark_bulk_delete(
    request,
    django_model: models.Model,
    data_dict: dict,
    replacements: tuple = (),
    force_delete=False,
):
    """Fonction trace des changements de données, pour views functions flag delete à True
    :param request: request au sens Django
    :param django_model: Model au sens Django
    :param data_dict: données validées, pour le filtre
    :param replacements: Tuple des varaibles à remplacer
    :param force_delete: True si l'on souhaite éffacé definitivement
    """
    function_call = str(inspect.currentframe().f_back)[:255]
    model_object = django_model.objects.filter(**data_dict)

    if not model_object:
        LOGGER_VIEWS.exception(
            f"{function_call} error : les données ne retournent aucuns résultats :\n"
            f"{str(data_dict)}"
        )
        request.session["level"] = 50

    user = request.user
    action_datetime = timezone.now()

    before = dict(data_dict.items())
    after = {
        **dict(deepcopy(before).items()),
        **{"modified_by": user.pk, "delete": True},
    }

    for replacement in replacements:
        key, value = replacement
        before[key] = value
        after[key] = value

    ChangesTrace.objects.create(
        action_datetime=action_datetime,
        action_type=0,
        function_name=function_call,
        action_by=user,
        before=before,
        after=after,
        difference=get_difference_dict(before, after),
        model_name=django_model._meta.model_name,
        model=django_model._meta.model,
        db_table=django_model._meta.db_table,
    )

    if force_delete:
        model_object.delete()
    else:
        model_object.update(modified_by=user, delete=True)

    request.session["level"] = 20


def trace_form_change(request, form: forms.ModelForm):
    """Fonction trace des changements de données, pour views functions flag delete à True
    :param request: request au sens Django
    :param form: données validées, pour le filtre
    """
    function_call = str(inspect.currentframe().f_back)[:255]

    user = request.user
    action_datetime = timezone.now()
    before = model_to_dict(form.cleaned_data.get("id"))
    instance = form.save()
    instance.modified_by = user
    instance.save()
    after = model_to_dict(instance)
    model = form.Meta.model

    ChangesTrace.objects.create(
        action_datetime=action_datetime,
        action_type=0,
        function_name=function_call,
        action_by=user,
        before=before,
        after=after,
        difference=get_difference_dict(before, after),
        model_name=model._meta.model_name,
        model=model,
        db_table=model._meta.db_table,
    )
    request.session["level"] = 20
