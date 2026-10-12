"""Views des Paramètres des Taux de change."""

import pendulum
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.generic import CreateView, ListView, UpdateView

from apps.core.bin.change_traces import ChangeTraceMixin
from apps.parameters.bin.exchanges import (
    set_base_exchange_rate,
    set_exchanges_sales_cosium,
)
from apps.parameters.forms import ExchangeRateForm
from apps.parameters.models import ExchangeRate
from apps.periods.forms import MonthForm
from heron.loggers import LOGGER_VIEWS

# ECRANS DES TAUX DE CHANGE MOYEN ==================================================================


def period_select_exchange(request):
    """Vue de la selection des taux de change.

    :param request: request au sens django
    :return: view.
    """
    form = MonthForm(request.POST or None)
    context = {
        "titre_table": "PERIODE TAUX DE CHANGE MOYEN",
        "form": form,
    }

    try:
        if request.method == "POST" and form.is_valid():
            dte_d, _ = form.cleaned_data["periode"].split("_")
            set_base_exchange_rate(month=dte_d)
            return redirect(reverse("parameters:exchanges_list", kwargs={"month": dte_d}))

    except Exception:
        LOGGER_VIEWS.exception("erreur form : %r", str(form.data))

    return render(request, "parameters/exchange_month.html", context=context)


class ExchangesList(ListView):
    """View de la liste des Taux de change."""

    model = ExchangeRate
    context_object_name = "exchanges"
    template_name = "parameters/exchange_list.html"
    extra_context: dict = {}

    def get(self, request, *args, **kwargs):
        """Add context in get request."""
        self.extra_context.update(kwargs)
        month = self.kwargs.get("month")
        mois = pendulum.parse(month).format("MMMM YYYY", locale="fr").upper()
        self.extra_context["titre_table"] = f"TAUX DE CHANGE MOYEN DU MOIS : {mois}"

        # Si dans le mois demandé le taux de change EUR/EUR n'existe pas, on le crée
        ExchangeRate.objects.get_or_create(
            rate_month=month,
            curency_base="EUR",
            currency_change_id="EUR",
            defaults={"rate": 1, "created_by": request.user},
        )

        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        """Taux de change du mois demandé (tri éventuel délégué à ListView)."""
        return super().get_queryset().filter(rate_month=self.kwargs.get("month"))


class ExchangeCreate(ChangeTraceMixin, SuccessMessageMixin, CreateView):
    """CreateView de création des Taux de change."""

    model = ExchangeRate
    form_class = ExchangeRateForm
    template_name = "parameters/exchange_update.html"
    success_message = "Le Taux de change %(currency_change)s a été créé avec succès"
    error_message = (
        "Le Taux de change %(currency_change)s n'a pu être créé, une erreur c'est produite"
    )

    def get_context_data(self, **kwargs):
        """On surcharge la méthode get_context_data, pour ajouter du contexte au template."""
        context = super().get_context_data(**kwargs)
        mois = str(self.kwargs.get("month"))
        mois_change = (
            pendulum.parse(str(self.kwargs.get("month"))).format("MMMM YYYY", locale="fr").upper()
        )
        context["chevron_retour"] = reverse("parameters:exchanges_list", kwargs={"month": mois})
        context["titre_table"] = f"Nouveau taux de change: {mois_change}"

        return context

    def get_success_url(self):
        """Return the URL to redirect to after processing a valid form."""
        return reverse("parameters:exchanges_list", kwargs={"month": self.kwargs.get("month")})

    def form_valid(self, form):
        """Ajout de l'user à la sauvegarde du formulaire."""
        existing = ExchangeRate.objects.filter(
            rate_month=self.kwargs.get("month"),
            curency_base="EUR",
            currency_change=form.cleaned_data.get("currency_change"),
        ).first()

        if existing:
            # Même devise déjà saisie pour ce mois : on modifie le taux existant
            form = ExchangeRateForm(self.request.POST, instance=existing)
            form.is_valid()
            self.success_message = "Le Taux de change %(currency_change)s a été modifié avec succès"

        # Les attributs sont fixés après validation (construct_instance les écraserait sinon)
        form.instance.created_by = self.request.user
        form.instance.curency_base = "EUR"
        form.instance.rate_month = self.kwargs.get("month")
        form.instance.rate = form.instance.rate or 1
        self.request.session["level"] = 20
        return super().form_valid(form)

    def form_updated(self):
        """Action à faire après form_valid save."""
        set_exchanges_sales_cosium(str(self.object.rate_month), self.object.currency_change.code)


class ExchangeUpdate(ChangeTraceMixin, SuccessMessageMixin, UpdateView):
    """UpdateView pour modification des Taux de change."""

    model = ExchangeRate
    form_class = ExchangeRateForm
    template_name = "parameters/exchange_update.html"
    success_message = "Le Taux de change %(currency_change)s a été modifiée avec success"
    error_message = (
        "Le Taux de change %(currency_change)s n'a pu être modifiée, une erreur c'est produite"
    )

    def get_context_data(self, **kwargs):
        """On surcharge la méthode get_context_data, pour ajouter du contexte au template."""
        context = super().get_context_data(**kwargs)
        mois = pendulum.parse(str(self.object.rate_month)).format("MMMM YYYY", locale="fr").upper()
        context["titre_table"] = f"Mise à jour taux de change: {mois}"
        context["chevron_retour"] = reverse(
            "parameters:exchanges_list", kwargs={"month": self.object.rate_month}
        )

        return super().get_context_data(**context)

    def get_success_url(self):
        """Return the URL to redirect to after processing a valid form."""
        return reverse("parameters:exchanges_list", kwargs={"month": self.object.rate_month})

    def form_valid(self, form):
        """Ajout de l'user à la sauvegarde du formulaire."""
        form.instance.modified_by = self.request.user
        form.instance.curency_base = "EUR"
        form.instance.rate_month = self.object.rate_month
        self.request.session["level"] = 20

        return super().form_valid(form)

    def form_updated(self):
        """Action à faire après form_valid save."""
        set_exchanges_sales_cosium(str(self.object.rate_month), self.object.currency_change.code)
