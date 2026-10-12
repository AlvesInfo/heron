# pylint: disable=E0401,W0621,W0212
"""FR : Tests des traces de changement (ChangeTraceMixin, trace_mark_delete, trace_mark_bulk_delete,


     trace_form_change, _before_and_after) et du mixin de filtrage par centrale (ChildCenterMixin)
EN : Tests for change traces and the child center mixin

created at: 2026-10-11
created by: Paulo ALVES
"""

import logging
from typing import ClassVar

import pytest
from django import forms
from django.core.exceptions import ImproperlyConfigured
from django.test import RequestFactory
from django.views.generic import CreateView, DeleteView, UpdateView, View

from apps.book.forms import StatFamillyAxesForm
from apps.book.models import StatFamillyAxes
from apps.centers_purchasing.models import TypeFacture
from apps.core.bin.change_traces import (
    ChangeTraceMixin,
    _before_and_after,
    trace_form_change,
    trace_mark_bulk_delete,
    trace_mark_delete,
)
from apps.core.bin.mixins import ChildCenterMixin
from apps.core.models import ChangesTrace

pytestmark = pytest.mark.django_db


@pytest.fixture
def request_factory(make_user):
    """Fabrique de requêtes portant un utilisateur et une session"""
    user = make_user()

    def _factory(method: str = "post", data=None, **kwargs):
        request = getattr(RequestFactory(), method)("/", data or {}, **kwargs)
        request.user = user
        request.session = {}
        return request

    _factory.user = user
    return _factory


@pytest.fixture
def make_stat(db):  # pylint: disable=W0613
    def _factory(name: str = "ACUITIS", **kwargs):
        return StatFamillyAxes.objects.create(name=name, **kwargs)

    return _factory


# VUES D'ESSAI BASÉES SUR LE MIXIN =================================================================


class StatCreate(ChangeTraceMixin, CreateView):
    """Création tracée, avec traitement après validation"""

    model = StatFamillyAxes
    form_class = StatFamillyAxesForm
    success_url = "/ok/"
    updated: ClassVar[list] = []

    def form_updated(self):
        self.updated.append(self.object.name)


class StatUpdate(ChangeTraceMixin, UpdateView):
    """Modification tracée, avec traitement après erreur"""

    model = StatFamillyAxes
    form_class = StatFamillyAxesForm
    success_url = "/ok/"
    template_name = "heron/base_semantic.html"
    errors: ClassVar[list] = []

    def form_error(self):
        self.errors.append("erreur")


class StatMarkDelete(ChangeTraceMixin, UpdateView):
    """Modification qui marque l'objet supprimé"""

    model = StatFamillyAxes
    form_class = StatFamillyAxesForm
    success_url = "/ok/"
    mark_delete = True


def test_initialisation_et_action():
    mixin = ChangeTraceMixin()
    stat = StatFamillyAxes(name="X")

    mixin.initialisation(stat, mark_delete=True)
    mixin.action()

    assert (mixin.object, mixin.mark_delete, mixin.action_type) == (stat, True, "UNDIFINED")
    assert StatCreate().action() is None
    assert StatCreate().action_type is None

    create = StatCreate()
    create.action()
    update = StatUpdate()
    update.action()

    class StatDelete(ChangeTraceMixin, DeleteView):
        model = StatFamillyAxes

    delete = StatDelete()
    delete.action()
    preset = StatUpdate()
    preset.action_type = "CREATE"
    preset.action()

    assert (create.action_type, update.action_type, delete.action_type, preset.action_type) == (
        "CREATE",
        "UPDATE",
        "DELETE",
        "CREATE",
    )


def test_has_change():
    """Longueurs différentes, clé absente, valeur différente, vide contre None sur champ blank"""
    mixin = ChangeTraceMixin()
    mixin.object = StatFamillyAxes(name="X")

    assert mixin.has_change({"a": 1}, {"a": 1, "b": 2}) is True
    assert mixin.has_change({"a": 1, "b": 2}, {"a": 1, "c": 2}) is True
    assert mixin.has_change({"name": "X", "created_at": 1}, {"name": "Y", "created_at": 2}) is True
    assert (
        mixin.has_change({"name": "X", "modified_by": 1}, {"name": "X", "modified_by": 2}) is False
    )
    assert mixin.has_change({"description": None}, {"description": ""}) is False
    assert mixin.has_change({"name": None}, {"name": ""}) is True


def test_creation_tracee_et_traitement_apres_validation(request_factory):
    request = request_factory(data={"name": "ACUITIS", "description": "d"})
    StatCreate.updated.clear()

    response = StatCreate.as_view()(request)

    stat = StatFamillyAxes.objects.get(name="ACUITIS")
    trace = ChangesTrace.objects.get()
    assert response.status_code == 302
    assert request.session["level"] == 20
    assert stat.created_by == request_factory.user
    assert (trace.action_type, trace.model_name, trace.before) == (1, "statfamillyaxes", {})
    assert trace.after["name"] == "ACUITIS"
    assert StatCreate.updated == ["ACUITIS"]


def test_modification_tracee(request_factory, make_stat):
    stat = make_stat("ACUITIS", description="avant")

    response = StatUpdate.as_view()(
        request_factory(data={"name": "ACUITIS", "description": "après"}), pk=stat.pk
    )

    stat.refresh_from_db()
    trace = ChangesTrace.objects.get()
    assert response.status_code == 302
    assert (stat.description, stat.modified_by) == ("après", request_factory.user)
    assert trace.action_type == 2
    assert trace.difference["avant"]["description"] == "avant"
    assert trace.difference["après"]["description"] == "après"


def test_modification_sans_changement(request_factory, make_stat):
    stat = make_stat("ACUITIS", description="")

    response = StatUpdate.as_view()(
        request_factory(data={"name": "ACUITIS", "description": ""}), pk=stat.pk
    )

    assert response.status_code == 302
    assert ChangesTrace.objects.count() == 0


def test_modification_invalide_et_traitement_apres_erreur(request_factory, make_stat, caplog):
    stat = make_stat("ACUITIS")
    StatUpdate.errors.clear()

    with caplog.at_level(logging.ERROR, logger="error_views"):
        response = StatUpdate.as_view()(request_factory(data={"name": ""}), pk=stat.pk)

    assert response.status_code == 200
    assert "ChangeTraceMixin error" in caplog.text
    assert StatUpdate.errors == ["erreur"]


def test_marquage_supprime_a_la_validation(request_factory, make_stat):
    stat = make_stat("ACUITIS")

    response = StatMarkDelete.as_view()(
        request_factory(data={"name": "ACUITIS", "description": "x"}), pk=stat.pk
    )

    stat.refresh_from_db()
    assert response.status_code == 302
    assert (stat.delete, stat.modified_by) == (True, request_factory.user)
    assert ChangesTrace.objects.get().after["delete"] is True


# FONCTIONS DE TRACE ===============================================================================


def test_trace_mark_delete_marque_et_trace(request_factory, make_stat):
    stat = make_stat("ACUITIS")
    make_stat("BBGR")
    request = request_factory()

    trace_mark_delete(request, StatFamillyAxes, {"name": "ACUITIS"})

    stat.refresh_from_db()
    trace = ChangesTrace.objects.get()
    assert (stat.delete, stat.modified_by) == (True, request_factory.user)
    assert request.session["level"] == 20
    assert (trace.action_type, trace.db_table) == (0, "book_statfamillyaxes")
    assert trace.difference["après"]["delete"] is True
    assert StatFamillyAxes.objects.count() == 2


def test_trace_mark_delete_force_sur_un_modele_sans_drapeaux(request_factory, make_child_center):
    """Un modèle sans champ delete ni modified_by est tracé puis réellement supprimé"""
    facture = TypeFacture.objects.create(
        child_center=make_child_center("ACF"),
        invoice_type="380",
        purchase_type_facture="F",
        sale_type_facture="V",
    )
    request = request_factory()

    trace_mark_delete(request, TypeFacture, {"id": facture.pk}, force_delete=True)

    trace = ChangesTrace.objects.get()
    assert not TypeFacture.objects.filter(pk=facture.pk).exists()
    assert "delete" not in trace.after
    assert trace.model_name == "typefacture"


def test_trace_mark_delete_sans_resultat(request_factory, caplog):
    request = request_factory()

    with caplog.at_level(logging.ERROR, logger="error_views"):
        trace_mark_delete(request, StatFamillyAxes, {"name": "ABSENT"})

    assert request.session["level"] == 50
    assert "ne retournent aucuns résultats" in caplog.text
    assert ChangesTrace.objects.count() == 0


def test_trace_mark_bulk_delete(request_factory, make_stat):
    stat = make_stat("ACUITIS", description="d")
    request = request_factory()

    trace_mark_bulk_delete(
        request, StatFamillyAxes, {"description": "d"}, replacements=(("name", "ACUITIS"),)
    )

    stat.refresh_from_db()
    trace = ChangesTrace.objects.get()
    assert (stat.delete, stat.modified_by) == (True, request_factory.user)
    assert trace.before == {"description": "d", "name": "ACUITIS"}
    assert trace.after["modified_by"] == request_factory.user.pk
    assert trace.difference["après"] == {"delete": True, "modified_by": request_factory.user.pk}
    assert request.session["level"] == 20


def test_trace_mark_bulk_delete_force_et_sans_resultat(request_factory, make_stat, caplog):
    make_stat("ACUITIS")
    request = request_factory()

    trace_mark_bulk_delete(request, StatFamillyAxes, {"name": "ACUITIS"}, force_delete=True)
    assert StatFamillyAxes.objects.count() == 0

    with caplog.at_level(logging.ERROR, logger="error_views"):
        trace_mark_bulk_delete(request, StatFamillyAxes, {"name": "ABSENT"}, force_delete=True)

    assert "ne retournent aucuns résultats" in caplog.text
    assert ChangesTrace.objects.count() == 2


class StatIdForm(forms.ModelForm):
    """Formulaire portant l'instance dans le champ id (comme un formset)"""

    id = forms.ModelChoiceField(queryset=StatFamillyAxes.objects.all())

    class Meta:
        model = StatFamillyAxes
        fields = ("id", "description")


def test_trace_form_change(request_factory, make_stat):
    stat = make_stat("ACUITIS", description="avant")
    form = StatIdForm({"id": stat.pk, "description": "après"}, instance=stat)
    request = request_factory()
    assert form.is_valid(), form.errors

    trace_form_change(request, form)

    stat.refresh_from_db()
    trace = ChangesTrace.objects.get()
    assert (stat.description, stat.modified_by) == ("après", request_factory.user)
    assert trace.before["description"] == "avant"
    assert trace.after["description"] == "après"
    assert trace.model_name == "statfamillyaxes"
    assert request.session["level"] == 20


def test_before_and_after_instance_sur_un_champ_simple(make_stat):
    """Une instance passée sur un champ non relationnel est ramenée à sa clé primaire"""
    stat = make_stat("ACUITIS")

    assert _before_and_after(StatFamillyAxes, {"name": stat.pk}, "name", stat) is True
    assert _before_and_after(StatFamillyAxes, {"name": "ACUITIS"}, "name", "BBGR") is False


# MIXIN DE FILTRAGE PAR CENTRALE ===================================================================


class _CenterView(ChildCenterMixin, View):
    """Vue minimale exposant le queryset filtré"""


@pytest.fixture
def factures(make_child_center):
    for code in ("ACF", "GAF", "MAA"):
        TypeFacture.objects.create(
            child_center=make_child_center(code),
            invoice_type="380",
            purchase_type_facture="F",
            sale_type_facture="V",
        )


def _view(user_code, **attrs):
    view = _CenterView(**attrs)
    request = RequestFactory().get("/")
    request.user = type("U", (), {"code_child_center": user_code})()
    view.request = request
    return view


@pytest.mark.usefixtures("factures")
def test_queryset_filtre_par_centrales_de_l_utilisateur():
    base = TypeFacture.objects.all()

    assert [row.child_center_id for row in _view("GAF|MAA", queryset=base).get_queryset()] == [
        "GAF",
        "MAA",
    ]
    assert _view("*", queryset=base).get_queryset().count() == 3
    assert [row.child_center_id for row in _view("ACF", model=TypeFacture).get_queryset()] == [
        "ACF"
    ]
    assert _view("*", model=TypeFacture).get_queryset().count() == 3


@pytest.mark.usefixtures("factures")
def test_queryset_ordonne():
    assert [
        row.child_center_id
        for row in _view("*", model=TypeFacture, ordering="-child_center").get_queryset()
    ] == ["MAA", "GAF", "ACF"]
    assert [
        row.child_center_id
        for row in _view("*", model=TypeFacture, ordering=("-child_center", "pk")).get_queryset()
    ] == ["MAA", "GAF", "ACF"]


def test_queryset_non_configure():
    view = _view("*")

    with pytest.raises(ImproperlyConfigured, match="_CenterView is missing a QuerySet"):
        view.get_queryset()


def test_creation_invalide_sans_traitement_apres_erreur(request_factory, caplog):
    """Une vue sans méthode form_error se contente de journaliser l'erreur"""
    with caplog.at_level(logging.ERROR):
        response = StatCreate.as_view()(request_factory(data={"name": ""}))

    assert response.status_code == 200
    assert "ChangeTraceMixin error" in caplog.text
    assert StatFamillyAxes.objects.count() == 0


def test_queryset_non_requete_renvoye_tel_quel():
    """Un attribut queryset qui n'est pas un QuerySet (liste) est renvoyé sans .all()"""
    assert _view("*", queryset=[1, 2]).get_queryset() == [1, 2]
