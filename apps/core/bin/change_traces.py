# pylint: disable=C0411,E0401,W0105,W0212
"""Module d'enregistrement de tous les changement en opération CRUD de l'application

Commentaire:

created at: 2022-03-22
created by: Paulo ALVES

modified at:
modified by:
"""
from copy import deepcopy

from django.utils import timezone
from django.views.generic import CreateView, UpdateView, DeleteView
from django.db.models.fields.files import ImageFieldFile

from apps.core.models import ChangesTrace


class ChangeTraceMixin:
    """
    Decorator qui sauvegarde les changements dans les données.

        class Classe(ChangeTraceMixin):
            ....
    """

    request = None
    object_before = {}
    object = None
    action_type = None
    ACTION_DICT = {
        "DELETE": 0,
        "CREATE": 1,
        "UPDATE": 2,
        "UNDIFINED": 9,
    }

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

        if self.action_type is None:

            if isinstance(self, (DeleteView,)):
                self.action_type = "DELETE"
            elif isinstance(self, (CreateView,)):
                self.action_type = "CREATE"
            elif isinstance(self, (UpdateView,)):
                self.action_type = "UPDATE"
            else:
                self.action_type = "UNDIFINED"

    def form_valid(self, form):
        """
        Surcharge de la méthode form_valid, pour enregistrer les données Avant/Après
        et ajouter le niveau de message et sa couleur.
        """
        self.request.session["level"] = 20
        self.object = form.save()

        before = {key: value for key, value in self.object_before.items() if key != "_state"}
        before_to_test = {
            key: str(value) if isinstance(value, (ImageFieldFile,)) else value
            for key, value in before.items()
            if key not in {"created_at", "modified_at"}
        }

        after = {key: value for key, value in self.object.__dict__.items() if key != "_state"}
        after_to_test = {
            key: str(value) if isinstance(value, (ImageFieldFile,)) else value
            for key, value in after.items()
            if key not in {"created_at", "modified_at"}
        }

        if before_to_test == after_to_test:
            self.success_message = "Vous n'avez rien modifié!"
            return super().form_valid(form)

        self.action()
        user = self.request.user

        if self.object_before:
            self.object.modified_by = user
        else:
            self.object.created_by = user

        self.object.save()

        ChangesTrace.objects.create(
            action_datetime=timezone.now(),
            action_type=self.ACTION_DICT.get(self.action_type, 9),
            function_name=self.__class__,
            action_by=user,
            before=before,
            after=after,
            model_name=self.object._meta.model_name,
            model=self.object._meta.model,
            db_table=self.object._meta.db_table,
        )
        return super().form_valid(form)

    def form_invalid(self, form):
        """On surcharge la méthode form_invalid, pour ajouter le niveau de message et sa couleur."""
        self.request.session["level"] = 50
        return super().form_invalid(form)
