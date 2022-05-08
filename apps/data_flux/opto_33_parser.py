# pylint: disable=
# E0401,C0303
"""
FR : Module de parsing des fichiers OPTO 33 (https://edi-optique.org/standards-opto/facture/)
EN : Parsing module for OPTO 33 (https://edi-optique.org/standards-opto/facture/)

Commentaire:

created at: 2022-04-20
created by: Paulo ALVES

modified at: 2022-04-20
modified by: Paulo ALVES
"""
import io
import re
from datetime import datetime
from typing import AnyStr, Callable
from pathlib import Path
from copy import deepcopy
import time
from functools import wraps
from memory_profiler import memory_usage

import sys
import platform

BASE_DIR = r"C:\\SitesWeb\\heron"

if platform.uname().node not in ["PauloMSI", "MSI"]:
    BASE_DIR = "/home/paulo/heron"

sys.path.insert(0, BASE_DIR)

from apps.data_flux.utilities import encoding_detect
from apps.data_flux.exceptions import (
    OptoDateError,
    OptoLinesError,
    OptoQualifierError,
    OptoParserError,
    PathTypeError,
    PathFileTypeError,
    PathUnzipError,
)


def profile(fn):
    @wraps(fn)
    def inner(*args, **kwargs):
        # Measure time
        t = time.perf_counter()
        # Measure memory
        mem, retval = memory_usage((fn, args, kwargs), retval=True, timeout=2000, interval=1e-7)
        elapsed = time.perf_counter() - t
        print(f"Time   {elapsed:0.04}")
        print(f"Memory : {min(mem)} -- {max(mem)}")
        return retval

    return inner


INVOICE_QUALIFIER_MAPPING = {
    ("NAD", "SU"): "supplier",
    ("NAD", "SU"): "supplier_ident",
    ("NAD", "PR"): "siret_payeur",
    ("NAD", "BY"): "code_fournisseur",
    ("NAD", "BY"): "code_maison",
    ("NAD", "BY"): "maison",
    ("RFF", "ON"): "acuitis_order_number",
    ("DTM", "4"): "acuitis_order_date",
    ("RFF", "AAK"): "delivery_number",
    ("DTM", "35"): "delivery_date",
    ("BGM", 2): "invoice_number",
    ("DTM", "3"): "invoice_date",
    ("BGM", 1): "invoice_type",
    ("CUX", 2): "devise",
    ("", ""): "reference_article",
    ("", ""): "ean_code",
    ("", ""): "libelle",
    ("", ""): "famille",
    ("QTY", "47"): "qty",
    ("AAB", "GRP"): "gross_unit_price",
    ("AAA", "NTP"): "net_unit_price",
    ("", ""): "packaging_amount",
    ("MOA", "8"): "transport_amount",
    ("MOA", "98"): "gross_price",
    ("MOA", "125"): "net_amount",
    ("", ""): "vat_rate",
    ("", ""): "vat_amount",
    ("", ""): "amount_with_vat",
    ("RFF", "AEG"): "client_name",
    ("", ""): "serial_number",
    ("", ""): "comment",
    ("MOA", "125"): "montant_facture_HT",
    ("MOA", "150"): "montant_facture_TVA",
    ("MOA", "128"): "montant_facture_TTC",
}

INVOICE_DICT = {
    "supplier": "",
    "supplier_ident": "",
    "siret_payeur": "",
    "code_fournisseur": "",
    "code_maison": "",
    "maison": "",
    "acuitis_order_number": "",
    "acuitis_order_date": "",
    "delivery_number": "",
    "delivery_date": "",
    "invoice_number": "",
    "invoice_date": "",
    "invoice_type": "380",
    "devise": "EUR",
    "reference_article": "",
    "ean_code": "",
    "libelle": "",
    "famille": "",
    "qty": "1",
    "gross_unit_price": "0",
    "net_unit_price": "0",
    "packaging_amount": "0",
    "transport_amount": "0",
    "gross_price": "0",
    "net_amount": "0",
    "vat_rate": "0",
    "vat_amount": "0",
    "amount_with_vat": "0",
    "client_name": "",
    "serial_number": "",
    "comment": "",
    "montant_facture_HT": "0",
    "montant_facture_TVA": "0",
    "montant_facture_TTC": "0",
}


def edi_date_format(qualifier_date: str, date_value: AnyStr) -> str:
    """
    FR: Fonction pour parser la date au format edi vers un format iso_date
    EN: Function to parse the date in edi format to an iso_date format
        :param qualifier_date: qualifiant de la date
        :param date_value: date arrivée du fichier
        :return: date au format iso_date "2022-12-25"

    """
    try:
        dict_format_dates = {
            "2": "%d%m%y",
            "3": "%m%d%y",
            "101": "%y%m%d",
            "102": "%Y%m%d",
            "201": "%y%m%d%H%M",
            "202": "%y%m%d%H%M%S",
            "203": "%Y%m%d%H%M",
            "204": "%Y%m%d%H%M%S",
            "301": "%y%m%d%H%M%z",
            "302": "%y%m%d%H%M%S%z",
            "303": "%Y%m%d%H%M%z",
            "304": "%Y%m%d%H%M%S%z",
        }
        date_format = dict_format_dates.get(qualifier_date.replace("'", ""))

        if date_format is None:
            raise ValueError

        iso_date = datetime.strptime(date_value, date_format).date().isoformat()

    except ValueError:
        raise OptoDateError(f"{date_value} is not in edi date format dictionnary")

    return iso_date


class EDIQualifierParser:
    def parse_qualifier(self, qualifier, data):
        try:
            method = getattr(self, f"cmd_{qualifier.lower()}")
            return method(data)
        except AttributeError:
            pass

    @staticmethod
    def cmd_unh(data):
        """
        Parsing du qualifier UNH, contenant l'en-tête financial_document
            Example:
                 UNH+426914+INVOIC:D:96B:UN:OPTO33 =>
                data = "('426914', 'INVOIC:D:96B:UN:OPTO3')"
                # 426914 = financial_document number
                # INVOIC:D:96B:UN: = unknow, and not used. Maybe a constant ?
                # OPTO33 = financial_document format standard
                => {
                    'financial_document_number':  '426914',
                    'metadata': ('INVOIC', 'D', '96B', 'UN')
                    'format': 'OPTO33'
                }
        :param data: ligne UNH à parser
        """
        try:
            num, metadata = data
            *unknown, financial_document_format = metadata.split(":")
        except ValueError:
            raise OptoParserError(
                f"Impossible d'extraire les données UNH de l'en-tête financial_document: {data!r}"
            )

        return {
            "financial_document_number": num,
            "metadata": unknown,
            "format": financial_document_format,
        }

    @staticmethod
    def cmd_bgm(data):
        """
        PARSE BGM : num and invoice type
        :param data: list of values
        """
        invoice_type, invoice_number, _ = data
        return {
            "invoice_type": invoice_type.replace("'", ""),
            "invoice_number": invoice_number.replace("'", ""),
        }

    @staticmethod
    def cmd_dtm(data):
        """
        PARSE DTM : balise EDI pour les Dates
        :param data: list of values
        """
        dtm_dict = {
            "4": "acuitis_order_date",
            "35": "delivery_date",
            "3": "invoice_date",
        }
        dtm, dte, dtm_qualifier = data

        test_dtm = dtm_dict.get(dtm)

        return {test_dtm: edi_date_format(dtm_qualifier, dte.replace("'", ""))} if test_dtm else ""

    @staticmethod
    def cmd_nad(data):
        """
        PASE NAD : balise EDI pour l'indication des acteurs de la facture
        :param data: list of values
        """

        if data[0] not in ["BY", "SU", "PR", "II"]:
            return ""

        try:
            nad_qualifier, ident, qualifier_ident, _, name, *elements = data
        except ValueError:
            raise ValueError("value Error")

        partner_dict = {}

        if nad_qualifier == "PR":
            partner_dict["siret_payeur"] = ident.replace("'", "")

        if nad_qualifier in {"SU", "II"}:
            partner_dict["supplier"] = name[:35].replace("'", " ")
            partner_dict["supplier_ident"] = ident.replace("'", "")

        if nad_qualifier == "BY":
            partner_dict["maison"] = " ".join(
                [name] + [element.replace("'", " ") for element in elements if element]
            )[:80]

            if qualifier_ident == "160":
                partner_dict["code_maison"] = ident.replace("'", "")
            else:
                partner_dict["code_fournisseur"] = ident.replace("'", "")

        return partner_dict

    @staticmethod
    def cmd_moa(data):
        """
        PARSE MOA : balise EDI pour les Montants du resume
        :param data: list of values
        """
        moa_dict = {
            "125": "montant_facture_HT",
            "128": "montant_facture_TTC",
        }
        moa_qualifier, amount = data

        test_moa = moa_dict.get(moa_qualifier)

        return {test_moa: amount.replace("'", "")} if test_moa else ""

    @staticmethod
    def cmd_moal(data):
        """
        PARSE MOA : balise EDI pour les Montants des lignes
        :param data: list of values
        """
        moa_dict = {
            "98": "gross_price",
            "125": "net_amount",
            "128": "amount_with_vat",
        }
        moa_qualifier, amount = data

        amount = amount.replace("'", "")

        if moa_qualifier == "8":
            return {
                "gross_unit_price": amount,
                "net_unit_price": amount,
                "gross_price": amount,
                "net_amount": amount,
                "emb_port_price": amount,
            }

        test_moa = moa_dict.get(moa_qualifier)

        return {test_moa: amount} if test_moa else ""

    @staticmethod
    def cmd_lin(data):
        """
        PARSE LIN : balise EDI pour les lignes
        :param data: list of values
        """
        *_, code_article, type_code, _, line_type, _ = data

        if line_type != "20":

            if type_code in {"EN", "EAN"}:
                return {"ean_code": code_article.replace("'", "")}

            return {"reference_article": code_article.replace("'", "")}

        return None

    @staticmethod
    def cmd_rff(data):
        """
        PARSE RFF : balise EDI pour les références de livraison ou commande
        :param data: list of values
        """
        moa_dict = {
            "AAK": "delivery_number",
            "ON": "acuitis_order_number",
            "AEG": "client_name",
            "ACD": "comment",
        }
        rff_qualifier, reference, *_ = data

        test_rff = moa_dict.get(rff_qualifier)

        return {test_rff: reference} if test_rff else ""

    @staticmethod
    def cmd_imd(data):
        """
        PARSE IMD : balise EDI pour les statistiques et libellés des articles
        :param data: list of values
        """

        imd_qualifier, _, stat, *libelle = data

        if imd_qualifier != "F":
            return ""

        return {
            "libelle": "".join(libelle),
            "famille": stat,
        }

    @staticmethod
    def cmd_qty(data):
        """
        PARSE QTY : balise EDI pour quantités
        :param data: list of values
        """

        qty_qualifier, qty, *_ = data

        if qty_qualifier != "47":
            return ""

        return {
            "qty": qty.replace("'", ""),
        }

    @staticmethod
    def cmd_pri(data):
        """
        PARSE PRI : balise EDI pour les prix de référence de l'article
        :param data: list of values
        """
        pri_dict = {
            "AAB": "gross_unit_price",
            "AAA": "net_unit_price",
        }
        pri_qualifier, price, _, qualifier = data

        test_pri = pri_dict.get(pri_qualifier)

        if (pri_qualifier == "AAB" and qualifier == "GRP") or (
            pri_qualifier == "AAA" and qualifier == "NTP"
        ):
            return {test_pri: price.replace("'", "")}

        return ""

    @staticmethod
    def cmd_tax(data):
        """
        PARSE TAX : balise EDI pour le taux de tva
        :param data: list of values
        """

        tax_qualifier, *_, tax = data

        if tax_qualifier != "7":
            return ""

        return {
            "vat_rate": tax.replace("'", ""),
        }

    @staticmethod
    def cmd_footer(data):
        """Parse the DOCUMENT footer

        Args:
            data: the string of + concatenated data

        Example:

            UNZ+25+1863 =>

            data = "('25', '1863')"

            # 25 = number of financial_documents in file
            # 1863 = recall of DOCUMENT ID number from header

            => {
                'document_id': '1863',
                'financial_documents_count': 25,
            }
        """

        try:
            count, doc_id = data
        except ValueError:
            raise OptoParserError(f"Unable to extract data from the footer: '{data!r}'")

        try:
            count = int(count)
        except (TypeError, ValueError):
            raise OptoParserError(f"financial_document count should an int: '{count!r}'")

        return {"document_id": doc_id, "financial_documents_count": count}


class EdiOpoto33Parser:
    """Parser des fichiers de type EDI optique Opto33"""

    def __init__(
        self,
        edi_file: Path,
        cleaner: Callable = (lambda x: x.replace("?", "").replace("  ", "")),
    ):
        """
        Instanciation de la classe
            :param edi_file: Path du fichier edi à intégrer
            :param cleaner: fonction de nettoyage du texte
        """
        if not isinstance(edi_file, (Path, io.BytesIO, io.StringIO)):
            raise PathTypeError(
                "EdiOpoto33Parser - edi_file :"
                f"{edi_file} - "
                "doit etre une instance de pathlib.Path"
            )

        if not edi_file.is_file():
            raise PathFileTypeError(
                "EdiOpoto33Parser - edi_file :" f"{edi_file} - " "edi_file doit etre un fichier"
            )

        self.edi_file = edi_file
        self.cmd_parser = EDIQualifierParser()
        self.cleaner = cleaner
        self.document = {}

    @staticmethod
    def extract_entries(lines):
        """
        Générateur ligne à ligne du fichier EDI opto 33 (factures)
            :param lines: lignes du fichier
            :return: code_parser, ligne
        """
        for line in lines:
            qualifier = line[:3]
            data = re.split(r"(?<![\?])\+", line[4:])
            if qualifier:
                yield qualifier, data

    def extract_invoices(self, invoices):
        """
        Extraction des factures une à une
            :param invoices: générator des factures une à une
            :return: générateur des dictionaire des éléments des factures
        """
        try:
            invoices_list = []

            for invoice in self.invoices(invoices):
                entete, *articles, resume, _ = invoice
                invoice_dict = deepcopy(INVOICE_DICT)

                # Parser d'entête
                for element in entete[1:]:
                    qualifier, *data = element
                    element_dict = self.cmd_parser.parse_qualifier(qualifier, data)

                    if element_dict:
                        invoice_dict.update(element_dict)

                # Parser de résumé
                for element in resume:
                    qualifier, *data = element
                    element_dict = self.cmd_parser.parse_qualifier(qualifier, data)

                    if element_dict:
                        invoice_dict.update(element_dict)

                invoice_detail_dict = deepcopy(invoice_dict)
                bl_dict = {
                    "delivery_number": None,
                    "delivery_date": None,
                }

                # Parser des lignes
                for element in articles:
                    qualifier, *line_elements = element

                    # Parsing du qualifier LIN pour ajout de la référence article ou code_ean
                    line, *line_data = qualifier
                    article_dict = self.cmd_parser.parse_qualifier(line, line_data)
                    qualifier_port_emb = ""

                    for article_element in line_elements:
                        qualifier, *elements = article_element

                        if qualifier in {"RFF", "DTM"} and elements[0] in {"AAK", "35"}:
                            bl_element_dict = self.cmd_parser.parse_qualifier(qualifier, elements)
                            if bl_element_dict:
                                bl_dict.update(bl_element_dict)

                        if qualifier == "MOA":
                            qualifier = "MOAL"

                        if qualifier == "ALC":
                            emb_port = str(elements[-1]).replace("'", "")
                            if emb_port == "PC":
                                qualifier_port_emb = "packaging_amount"
                            elif emb_port == "FC":
                                qualifier_port_emb = "transport_amount"
                            else:
                                qualifier_port_emb = ""

                        elif qualifier == "MOAL" and elements[0] == "8":
                            if qualifier_port_emb:
                                price_dict = self.cmd_parser.parse_qualifier(qualifier, elements)
                                invoice_detail_dict[qualifier_port_emb] = price_dict.get(
                                    "emb_port_price"
                                )
                                del price_dict["emb_port_price"]
                                invoice_detail_dict.update(price_dict)

                            qualifier_port_emb = ""

                        else:
                            element_dict = self.cmd_parser.parse_qualifier(qualifier, elements)

                            if element_dict:
                                invoice_detail_dict.update(element_dict)

                    if article_dict:
                        invoice_detail_dict.update(article_dict)
                        invoice_detail_dict.update(bl_dict)

                        if not invoice_detail_dict.get("delivery_date"):
                            del invoice_detail_dict["delivery_date"]

                        if not invoice_detail_dict.get("acuitis_order_date"):
                            del invoice_detail_dict["acuitis_order_date"]

                        invoices_list.append(invoice_detail_dict)
                        invoice_detail_dict = deepcopy(invoice_dict)

            yield from invoices_list

        except (OptoLinesError, Exception) as error:
            raise OptoLinesError("Erreur dans l'extraction des factures") from error

    @staticmethod
    def invoices(lines):
        """
        Générateur des éléments des factures, factures par factures
        :param lines: lignes des fichiers
        """
        for line in lines:
            yield [
                [
                    re.split(r"(?<![\?])\+|:", invoice_lines)
                    for invoice_lines in re.split(r"(?<!\?)['|\n]", invoice)
                    if invoice_lines
                ]
                for invoice in re.split(r"[\n|'](?=LIN)|[\n|'](?=UNS)|[\n|'](?=UNT)", line)
            ]

    def parse(self):
        """
        Fontion de parsing du fichier bancaire
            :return: {"file_name": "", "edi_financial_documents": []}
        """
        encoding = encoding_detect(self.edi_file) or "ascii"

        with open(self.edi_file, encoding=encoding) as file:
            text = file.read().strip()
            try:
                _, header, *invoices, footer = re.split(
                    r"[\n|'](?=UNB)|[\n|'](?=UNH)|[\n|'](?=UNZ)", text
                )

            except ValueError:
                raise OptoParserError(
                    "Impossible d'extraire les données du pied de page du fichier :"
                    f" {self.edi_file.name!r}"
                )

            header, footer = self.extract_entries([header, footer])
            id_interchange = header[1][4]

            footer_parse = self.cmd_parser.cmd_footer(footer[1])
            footer_id_interchange = footer_parse.get("document_id").replace("'", "")
            footer_count_invoices = footer_parse.get("financial_documents_count")

            # On vérifie l'ID d'interchage
            if id_interchange != footer_id_interchange:
                raise OptoParserError(
                    r"l'ID du fichier Edi en entête (UNB) et en pied de page (UNZ) sont différents"
                )

            # On vérifie que le nombre de factures est celui annoncé
            if len(re.findall(r"UNH(?=\+)", text)) != footer_count_invoices:
                raise OptoParserError(
                    r"Il n'y a pas dans le fichier le nombre de factures "
                    r"annoncé dans le pied de page (UNZ)"
                )
            error = False
            errors_list = []
            # On vérifie que toutes les lignes de factures sont présentes
            for line in self.invoices(invoices):
                entete, *articles, resume = line
                nb_lignes = int(resume[0][1])
                all_files = len([_ for lis in line for _ in lis]) != nb_lignes

                if all_files:
                    print(entete, nb_lignes, len([_ for lis in line for _ in lis]))
                    print(entete[1][2], " : ", nb_lignes, len([_ for lis in line for _ in lis]))
                    error = True
                    errors_list.append(entete[1][2])

            if error:
                raise OptoParserError(
                    r"Le nombre de lignes des factures/avoirs : %s "
                    r"ne correpond pas au "
                    r"nombre de lignes indiquées dans leur résumé (UNT)" % ", ".join(errors_list)
                )

            return {
                "header": header,
                "footer": self.cmd_parser.cmd_footer(footer[1]),
                "invoices": self.extract_invoices(invoices),
                "get_columns": INVOICE_DICT,
            }


@profile
def essai():
    # OUT_FILE = Path(r"C:\SitesWeb\heron\files\processing\suppliers_invoices_files\EDI\EDI_BEAUSOLEIL_ACUITIS-32022-2022041-36665.fac")
    # OUT_FILE = Path(
    #     r"C:\SitesWeb\heron\files\processing\suppliers_invoices_files\EDI\EDI_BBGR_473_1_FFEDI-ACUITIS_9232000NNCUT.edi"
    # )
    FILE = Path(r"C:\SitesWeb\heron\files\processing\suppliers_invoices_files\EDI\test_bbgr")
    OUT_FILE = Path(
        r"C:\SitesWeb\heron\files\processing\suppliers_invoices_files\EDI\EDI_NOVACEL_10956_FR02024.edi"
    )

    PARSER = EdiOpoto33Parser(OUT_FILE)

    DOCUMENT_PARSER = PARSER.parse()
    invoices = DOCUMENT_PARSER["invoices"]

    l_doc = list(invoices if invoices else [])

    set_fac = set()
    j = 0
    with FILE.open(mode="w") as file:
        for j, line in enumerate(l_doc, 1):
            set_fac.add(line["invoice_number"])
            print(line)
            file.write(str(line) + "\n")

    print(DOCUMENT_PARSER["footer"])
    print(len(set_fac), "factures - avec : ", j, " lignes")
    import psutil

    print("mem psutil : ", psutil.Process().memory_info().rss / (1024 * 1024))


if __name__ == "__main__":
    essai()
