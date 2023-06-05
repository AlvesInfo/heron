# pylint: disable=E0401,W0718,W1203,W0612,W0613
"""
Views des Paramètres des Taux de change
"""
import pendulum
from django.shortcuts import redirect, reverse, render
from django.contrib.messages.views import SuccessMessageMixin
from django.views.generic import ListView, CreateView, UpdateView

from heron.loggers import LOGGER_VIEWS
from apps.core.bin.change_traces import ChangeTraceMixin
from apps.parameters.bin.exchanges import set_base_exchange_rate
from apps.parameters.models import ExchangeRate
from apps.periods.forms import MonthForm
from apps.parameters.forms import ExchangeRateForm


# ECRANS DES TAUX DE CHANGE MOYEN ==================================================================


def period_select_exchange(request):
    """
    Vue de la selection des taux de change
    :param request: request au sens django
    :return: view
    """

    form = MonthForm(request.POST or None)
    context = {
        "titre_table": "PERIODE TAUX DE CHANGE MOYEN",
        "form": form,
    }

    try:
        if request.method == "POST" and form.is_valid():
            dte_d, _ = form.cleaned_data.get("periode").split("_")
            set_base_exchange_rate(month=dte_d)
            return redirect(reverse("parameters:exchanges_list", kwargs={"month": dte_d}))

    except Exception as error:
        print(error)
        LOGGER_VIEWS.exception(f"erreur form : {str(form.data)!r}")

    return render(request, "parameters/month_exchange.html", context=context)


class ExchangesList(ListView):
    """View de la liste des Taux de change"""

    model = ExchangeRate
    context_object_name = "exchanges"
    template_name = "parameters/exchange_list.html"
    extra_context = {}

    def get(self, request, *args, **kwargs):
        """add context in get request"""
        self.extra_context.update(kwargs)
        month = self.kwargs.get("month")
        mois = pendulum.parse(month).format("MMMM YYYY", locale="fr").upper()
        self.extra_context["titre_table"] = f"TAUX DE CHANGE MOYEN DU MOIS : {mois}"
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        """
        Return the list of items for this view.
        The return value must be an iterable and may be an instance of
        `QuerySet` in which case `QuerySet` specific behavior will be enabled.
        """
        queryset = ExchangeRate.objects.filter(rate_month=self.kwargs.get("month"))
        ordering = self.get_ordering()

        if ordering:
            if isinstance(ordering, str):
                ordering = (ordering,)
            queryset = queryset.order_by(*ordering)

        return queryset


class ExchangeCreate(ChangeTraceMixin, SuccessMessageMixin, CreateView):
    """CreateView de création des Taux de change"""

    model = ExchangeRate
    form_class = ExchangeRateForm
    form_class.use_required_attribute = False
    template_name = "parameters/exchange_update_table.html"
    success_message = "Le Taux de change %(currency_change)s a été créé avec success"
    error_message = (
        "Le Taux de change %(currency_change)s n'a pu être créé, une erreur c'est produite"
    )

    def get_context_data(self, **kwargs):
        """On surcharge la méthode get_context_data, pour ajouter du contexte au template"""
        context = super().get_context_data(**kwargs)
        context["create"] = True
        context["chevron_retour"] = reverse("parameters:natures_list")
        context["titre_table"] = "Création d'un nouveau taux de change"

        return context

    def form_valid(self, form):
        """Ajout de l'user à la sauvegarde du formulaire"""
        form.instance.created_by = self.request.user
        self.request.session["level"] = 20

        return super().form_valid(form)


class ExchangeUpdate(ChangeTraceMixin, SuccessMessageMixin, UpdateView):
    """UpdateView pour modification des Taux de change"""

    model = ExchangeRate
    form_class = ExchangeRateForm
    form_class.use_required_attribute = False
    template_name = "parameters/exchange_update_table.html"
    success_message = "Le Taux de change %(currency_change)s a été modifiée avec success"
    error_message = (
        "Le Taux de change %(currency_change)s n'a pu être modifiée, une erreur c'est produite"
    )

    def get_context_data(self, **kwargs):
        """On surcharge la méthode get_context_data, pour ajouter du contexte au template"""
        context = super().get_context_data(**kwargs)
        context["titre_table"] = "Mise à jour taux de change"
        context["chevron_retour"] = reverse("parameters:natures_list")

        return super().get_context_data(**context)

    def form_valid(self, form, **kwargs):
        """Ajout de l'user à la sauvegarde du formulaire"""
        form.instance.modified_by = self.request.user
        self.request.session["level"] = 20

        return super().form_valid(form)
