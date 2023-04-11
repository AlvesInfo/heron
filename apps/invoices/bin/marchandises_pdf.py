# pylint: disable=E0401
"""
FR : Module de génération des factures de marchandises en pdf
EN : Module for generating invoices marchandises in pdf

Commentaire:

created at: 2023-04-11
created by: Paulo ALVES

modified at: 2023-04 -11
modified by: Paulo ALVES
"""
from typing import AnyStr


def summary_invoice_pdf(cct: AnyStr) -> None:
    """
    Generation de la page de resumé de facture
    :param cct: Maison facturée
    :return: None
    """


def marchandise_header_invoice_pdf(invoice_number: AnyStr) -> None:
    """
    Génération des entêtes de factures de marchandises
    :param invoice_number: N° de facture
    :return: None
    """


def marchandises_suppliers_invoice_pdf(invoice_number: AnyStr) -> None:
    """
    Génération des récapitulatifs par fournisseurs
    :param invoice_number: N° de facture
    :return:
    """


def marchandise_details_invoice_pdf(invoice_number: AnyStr) -> None:
    """
    Génération des pages de marchandises
    :param invoice_number: N° de facture
    :return: No
    """


def marchandise_sub_details_invoice_pdf(invoice_number: AnyStr) -> None:
    """
    Génération des pages de marchandises
    :param invoice_number: N° de facture
    :return: None
    """