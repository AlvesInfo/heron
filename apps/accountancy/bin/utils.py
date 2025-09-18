import datetime

import pendulum

from apps.accountancy.models import PaymentCondition


def due_date_calculate(invoice_date: datetime, condition: PaymentCondition):
    """Calcul de la date d'échéance
    :param invoice_date: date de la facture
    :param condition: Instance du modèle de la condition de paiement
    :return: pendulum.date humanize
    """
    calculate_date = pendulum.date(invoice_date.year, invoice_date.month, invoice_date.day)

    if condition.end_month == "2":
        calculate_date = calculate_date.end_of("month")

    elif condition.end_month == "3":
        calculate_date = calculate_date.subtract(months=1).end_of("month")

    months = int(condition.offset_month or 0)

    if months != 0:
        calculate_date = calculate_date.add(months=months).end_of("month")

    days = int(condition.offset_days or 0)

    if days != 0:
        calculate_date = calculate_date.add(days=days)

    return calculate_date.format("DD/MM/YYYY", locale="fr")


def get_str_echeances(invoice_date: datetime, code: str):
    """Calcul des Echéances
    :param invoice_date: date de la facture
    :param code: uuid de la condition de paiement
    :return: Retourne l'échéance textuelle
    """
    due_dates_list = []

    for due_date in PaymentCondition.objects.filter(code=code).order_by(
        "offset_month", "offset_days"
    ):
        percent_at_term = int(due_date.percent_at_term)
        pourcent = (
            f"{percent_at_term} % le " if percent_at_term and percent_at_term != 100 else ""
        )
        due_dates_list.append("".join([pourcent, due_date_calculate(invoice_date, due_date)]))

    return ", ".join(due_dates_list)
