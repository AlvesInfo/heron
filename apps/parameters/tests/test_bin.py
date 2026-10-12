# pylint: disable=E0401,W0621
"""FR : Tests des fonctions de paramétrage (bin/core, bin/exchanges, bin/generic_nums)


EN : Tests for parameters functions

created at: 2026-10-11
created by: Paulo ALVES
"""

import asyncio
import datetime
from decimal import Decimal

import pytest
from django.contrib.messages import get_messages
from django.test import RequestFactory
from django.utils import timezone
from django_celery_results.models import TaskResult

from apps.core.exceptions import LaunchDoesNotExistsError
from apps.parameters.bin import core
from apps.parameters.bin.core import (
    get_action,
    get_actions_in_progress,
    get_counter_num,
    get_in_progress,
    get_in_progress_async,
    get_object,
    have_action_in_progress,
    have_send_email_without_finalize,
    have_subscription,
    initial_counter_nums,
    set_message,
)
from apps.parameters.bin.exchanges import set_base_exchange_rate, set_exchanges_sales_cosium
from apps.parameters.bin.generic_nums import get_generic_cct_num
from apps.parameters.models import ActionInProgress, CounterNums, ExchangeRate

pytestmark = pytest.mark.django_db

MONTH = datetime.date(2026, 1, 1)


# ACTIONS EN COURS =================================================================================


def test_get_action_cree_puis_retrouve():
    action = get_action("import_edi_invoices")
    again = get_action("import_edi_invoices")
    other = get_action("inconnue")

    assert action.comment == "Executable pour l'import des fichiers edi des factures founisseurs"
    assert again == action
    assert (other.action, other.comment) == ("inconnue", "inconnue")


def test_get_in_progress():
    """Une action marquée en cours n'est confirmée que par une tâche celery démarrée récente"""
    assert get_in_progress() is False

    action = get_action()
    assert get_in_progress() is False

    action.in_progress = True
    action.save()
    assert get_in_progress() is False

    task = TaskResult.objects.create(task_id="t1", task_name="suppliers_import", status="STARTED")
    assert get_in_progress() is True
    assert get_in_progress(task_name="autre") is False

    TaskResult.objects.filter(pk=task.pk).update(
        date_created=timezone.now() - datetime.timedelta(hours=2)
    )
    assert get_in_progress() is False


def test_get_actions_in_progress():
    assert get_actions_in_progress() is False

    ActionInProgress.objects.create(action="x", in_progress=True)
    assert get_actions_in_progress() is False

    TaskResult.objects.create(task_id="t2", task_name="x", status="STARTED")
    assert get_actions_in_progress() is True

    TaskResult.objects.update(status="SUCCESS")
    assert get_actions_in_progress() is False


@pytest.mark.django_db(transaction=True)
def test_get_in_progress_async():
    """La version async s'exécute dans un autre thread : les données doivent être validées"""
    action = get_action()
    action.in_progress = True
    action.save()
    TaskResult.objects.create(task_id="t3", task_name="suppliers_import", status="STARTED")

    assert asyncio.run(get_in_progress_async()) is True


def test_have_action_in_progress():
    assert have_action_in_progress() is False

    TaskResult.objects.create(task_id="t4", task_name="x", status="STARTED")
    assert have_action_in_progress() is True

    TaskResult.objects.update(status="SUCCESS")
    ActionInProgress.objects.create(action="y", in_progress=True)
    assert have_action_in_progress() is True


def test_have_send_email_et_subscription(
    make_sale_invoice, make_maison, make_invoice_function, make_article, make_unit
):
    assert have_send_email_without_finalize() is False
    make_sale_invoice(third_party_num="CLI001", send_email=True, final=False)
    assert have_send_email_without_finalize() is True

    assert have_subscription("ABONNEMENT") is False
    from apps.centers_clients.models import MaisonSubcription  # pylint: disable=C0415

    MaisonSubcription.objects.create(
        maison=make_maison("AF0001"),
        article=make_article(),
        unit_weight=make_unit(),
        function=make_invoice_function("ABONNEMENT"),
    )
    assert have_subscription("ABONNEMENT") is True


def test_get_object(make_invoice_function):
    """La fonction paramétrée est résolue par son chemin pointé, sinon LaunchDoesNotExistsError"""
    make_invoice_function("CHECK", function="apps.parameters.bin.core.get_action")
    make_invoice_function("CASSEE", function="apps.parameters.bin.core.absente")

    assert get_object("CHECK") is get_action

    with pytest.raises(LaunchDoesNotExistsError):
        get_object("CASSEE")

    with pytest.raises(LaunchDoesNotExistsError):
        get_object("INCONNUE")


def test_set_message():
    request = RequestFactory().get("/")
    request.session = {}
    from django.contrib.messages.storage.fallback import FallbackStorage  # pylint: disable=C0415

    request._messages = FallbackStorage(request)  # pylint: disable=W0212

    set_message(request, 50, "Erreur")

    assert request.session["level"] == 50
    assert [m.message for m in get_messages(request)] == ["Erreur"]


# COMPTEURS ========================================================================================


def test_get_counter_num_prefixes_suffixes_et_separateur(make_counter, make_society):
    """Préfixe de date ou de tiers, suffixe, séparateur et remplissage ; compteur incrémenté"""
    make_society("TIERS01")
    counter = make_counter(
        "factures", num=7, prefix="AAAAMM", suffix="TIERS", lpad_num=4, separateur="-"
    )
    month = datetime.date.today().strftime("%Y%m")

    assert get_counter_num(counter, {"suffix": "TIERS01"}) == f"{month}-TIERS01-0007"
    assert get_counter_num(counter, {"suffix": "TIERS01"}) == f"{month}-TIERS01-0008"
    assert CounterNums.objects.get(counter=counter).num == 9

    plain = make_counter("simple", num=3, lpad_num=0)
    assert get_counter_num(plain) == "3"
    assert get_counter_num(plain, {"prefix": "AF0001", "separateur": "_"}) == "AF0001_4"


def test_initial_counter_nums(make_counter):
    counter = make_counter("x")
    CounterNums.objects.filter(counter=counter).delete()

    created = initial_counter_nums(counter)

    assert created.num == 1
    assert initial_counter_nums(counter) == created


def test_get_generic_cct_num(make_counter):
    make_counter("generic", num=12, lpad_num=5)

    assert get_generic_cct_num("AF0001") == "AF0001_00012"
    assert get_generic_cct_num("AF0002") == "AF0002_00013"


# TAUX DE CHANGE ===================================================================================


@pytest.fixture
def ventes_suisses(make_country, make_country_currency, make_maison, make_vente):
    """Deux ventes de janvier d'une maison suisse (devise CHF), une vente en euros"""
    make_country_currency("CHF", "Franc suisse")
    # Les pays sont créés avant les maisons (make_maison crée FR sans devise sinon)
    suisse = make_country("CH", "Suisse", currency_iso="CHF")
    france = make_country("FR", "France", currency_iso="EUR")
    maison = make_maison("AF0010", pays=suisse)
    first = make_vente(maison, MONTH)
    second = make_vente(maison, MONTH, ca_ht_ap_remise=Decimal(50))
    euro = make_vente(make_maison("AF0001", pays=france), MONTH)
    return {"maison": maison, "first": first, "second": second, "euro": euro}


def test_set_base_exchange_rate(ventes_suisses, make_country_currency):
    """Un taux à 0 est créé pour chaque devise des ventes du mois sans taux, EUR à 1"""
    make_country_currency("EUR", "Euro")

    set_base_exchange_rate(MONTH)

    rates = {rate.currency_change.code: rate for rate in ExchangeRate.objects.all()}
    assert set(rates) == {"CHF", "EUR"}
    assert (rates["CHF"].rate, rates["CHF"].rate_month) == (Decimal(0), MONTH)
    assert rates["EUR"].rate == Decimal(1)

    set_base_exchange_rate(MONTH)
    assert ExchangeRate.objects.count() == 2

    # Le mois suivant a ses propres taux par défaut, même si la devise a déjà un taux
    ventes_suisses["first"].__class__.objects.filter(pk=ventes_suisses["second"].pk).update(
        sale_month=datetime.date(2026, 2, 1)
    )
    set_base_exchange_rate(datetime.date(2026, 2, 1))
    assert ExchangeRate.objects.filter(
        rate_month=datetime.date(2026, 2, 1), currency_change="CHF"
    ).exists()


def test_set_base_exchange_rate_devise_inconnue(ventes_suisses):
    """Une devise absente de la table des devises est ignorée (seul l'EUR est créé)"""
    from apps.countries.models import Currency  # pylint: disable=C0415

    Currency.objects.filter(code="CHF").delete()

    set_base_exchange_rate(MONTH)

    assert [rate.currency_change.code for rate in ExchangeRate.objects.all()] == ["EUR"]


def test_set_exchanges_sales_cosium(ventes_suisses, make_exchange_rate):
    """Les montants en euros des ventes du mois sont recalculés avec 1 / taux"""
    make_exchange_rate("CHF", MONTH, "2")

    set_exchanges_sales_cosium(str(MONTH), "CHF")

    first = ventes_suisses["first"]
    first.refresh_from_db()
    euro = ventes_suisses["euro"]
    euro.refresh_from_db()
    assert first.taux_change_moyen == Decimal("0.5")
    assert first.ca_ht_ap_remise_eur == Decimal(50)
    assert first.px_vente_ttc_eur == Decimal(60)
    assert euro.taux_change_moyen is None


def test_module_core_expose_les_formats_de_date():
    assert core.DATE_FORMATS["AAAAMM"] == "YYYYMM"
    assert core.AFFIX_KINDS == ("TIERS", "CCT")
