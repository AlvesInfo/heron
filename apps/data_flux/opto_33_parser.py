# pylint: disable=R0914
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
from typing import AnyStr, Callable, Generator
from pathlib import Path
from copy import deepcopy

from apps.data_flux.utilities import encoding_detect
from apps.data_flux.exceptions import (
    OptoDateError,
    OptoLinesError,
    OptoQualifierError,
    OptoIdError,
    # OptoNumberError,
    OptoParserError,
    PathTypeError,
    PathFileError,
)

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
    "gross_amount": "0",
    "net_amount": "0",
    "vat_rate": "0",
    "vat_amount": "0",
    "amount_with_vat": "0",
    "client_name": "",
    "serial_number": "",
    "comment": "",
    "invoice_amount_without_tax": "0",
    "invoice_amount_tax": "0",
    "invoice_amount_with_tax": "0",
}


def edi_iso_date_format(qualifier_date: str, date_value: AnyStr) -> str:
    """
    FR: Fonction pour parser la date au format edi vers un format iso_date
    EN: Function to parse the date in edi format to iso_date format
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

        if date_value == "00000000":
            iso_date = "1900-01-01"
        else:
            iso_date = datetime.strptime(date_value, date_format).date().isoformat()

    except ValueError as except_error:
        raise OptoDateError(f"{date_value} is not in edi date format dictionnary") from except_error

    return iso_date


class EDIQualifierParser:
    """Qualifier pour l'EDI opto 33"""

    def __init__(self, edi_file: Path):
        self.edi_file = edi_file.name

    def parse_qualifier(self, qualifier: str, data: list) -> dict:
        """Parsing des function à appliquer en fonction des qualifiers"""
        try:
            method = getattr(self, f"cmd_{qualifier.lower()}")
            return method(data)
        except AttributeError:
            pass

        return {}

    def cmd_unh(self, data: list) -> dict:
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

        except ValueError as except_error:
            raise OptoQualifierError(
                f"Impossible d'extraire les données UNH de l'en-tête financial_document: {data!r}"
                f", pour le fichier {self.edi_file!r}"
            ) from except_error

        return {
            "financial_document_number": num,
            "metadata": unknown,
            "format": financial_document_format,
        }

    def cmd_bgm(self, data: list) -> dict:
        """
        PARSE BGM : num and invoice type
        :param data: list of values
        """
        try:
            invoice_type, invoice_number, _ = data

        except ValueError as except_error:
            raise OptoQualifierError(
                f"Impossible d'extraire les données du qualifier BGM : {data!r}"
                f", pour le fichier {self.edi_file!r}"
            ) from except_error

        return {
            "invoice_type": invoice_type.replace("'", ""),
            "invoice_number": invoice_number.replace("'", ""),
        }

    def cmd_dtm(self, data: list) -> dict:
        """
        PARSE DTM : balise EDI pour les Dates
        :param data: list of values
        """
        try:
            dtm_dict = {
                "4": "acuitis_order_date",
                "35": "delivery_date",
                "3": "invoice_date",
            }
            dtm, dte, dtm_qualifier = data

        except ValueError as except_error:
            raise OptoQualifierError(
                f"Impossible d'extraire les données du qualifier DTM : {data!r}"
                f", pour le fichier {self.edi_file!r}"
            ) from except_error

        test_dtm = dtm_dict.get(dtm)

        return (
            {test_dtm: edi_iso_date_format(dtm_qualifier, dte.replace("'", ""))} if test_dtm else {}
        )

    def cmd_nad(self, data: list) -> dict:
        """
        PASE NAD : balise EDI pour l'indication des acteurs de la facture
        :param data: list of values
        """

        try:
            if data[0] not in ["BY", "SU", "PR", "II"]:
                return ""

            nad_qualifier, ident, qualifier_ident, _, name, *elements = data

        except IndexError as except_error:
            raise OptoParserError(
                f"Impossible d'extraire les données du qualifier NAD "
                f"(data[0] not in ['BY', 'SU', 'PR', 'II']): {data!r}"
                f", pour le fichier {self.edi_file!r}"
            ) from except_error

        except ValueError as except_error:
            # NAD+BY, peut être placé dans les lignes de facturation, cela indique le magasin livré
            # Mais nous ne prenons que l'indicateur NAD dans la partie entête de la facture
            if data[0] == "BY" and len(data) < 5:
                return ""

            raise OptoQualifierError(
                f"Impossible d'extraire les données du qualifier NAD : {data!r}"
                f", pour le fichier {self.edi_file!r}"
            ) from except_error

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

    def cmd_moa(self, data: list) -> dict:
        """
        PARSE MOA : balise EDI pour les Montants du resume
        :param data: list of values
        """
        try:
            moa_dict = {
                "125": "invoice_amount_without_tax",
                "128": "invoice_amount_with_tax",
            }
            moa_qualifier, amount = data

        except ValueError as except_error:
            raise OptoQualifierError(
                f"Impossible d'extraire les données du qualifier MOA : {data!r}"
                f", pour le fichier {self.edi_file!r}"
            ) from except_error

        test_moa = moa_dict.get(moa_qualifier)

        return {test_moa: amount.replace("'", "")} if test_moa else {}

    def cmd_moal(self, data: list) -> dict:
        """
        PARSE MOA : balise EDI pour les Montants des lignes
        :param data: list of values
        """
        try:
            moa_dict = {
                "98": "gross_amount",
                "125": "net_amount",
                "128": "amount_with_vat",
            }
            moa_qualifier, amount = data

        except ValueError as except_error:
            raise OptoQualifierError(
                f"Impossible d'extraire les données du qualifier MOA(L) : {data!r}"
                f", pour le fichier {self.edi_file!r}"
            ) from except_error

        amount = amount.replace("'", "")

        if moa_qualifier == "8":
            return {
                "gross_unit_price": amount,
                "net_unit_price": amount,
                "gross_amount": amount,
                "net_amount": amount,
                "emb_port_price": amount,
            }

        test_moa = moa_dict.get(moa_qualifier)

        return {test_moa: amount} if test_moa else {}

    def cmd_lin(self, data: list) -> dict:
        """
        PARSE LIN : balise EDI pour les lignes
        :param data: list of values
        """
        try:
            *_, code_article, type_code, _, line_type, _ = data

        except ValueError as except_error:
            raise OptoQualifierError(
                f"Impossible d'extraire les données du qualifier LIN : {data!r}"
                f", pour le fichier {self.edi_file!r}"
            ) from except_error

        if line_type != "20":

            if type_code in {"EN", "EAN"}:
                return {"ean_code": code_article.replace("'", "")}

            return {"reference_article": code_article.replace("'", "")}

        return {}

    def cmd_rff(self, data: list) -> dict:
        """
        PARSE RFF : balise EDI pour les références de livraison ou commande
        :param data: list of values
        """
        try:
            rff_dict = {
                "AAK": "delivery_number",
                "ON": "acuitis_order_number",
                "AEG": "client_name",
                "ACD": "comment",
            }
            if len(data) == 1:
                return ""

            rff_qualifier, reference, *_ = data

        except ValueError as except_error:
            # print(data)
            raise OptoQualifierError(
                f"Impossible d'extraire les données du qualifier RFF : {data!r}"
                f", pour le fichier {self.edi_file!r}"
            ) from except_error

        test_rff = rff_dict.get(rff_qualifier)

        return {test_rff: reference} if test_rff else {}

    def cmd_imd(self, data: list) -> dict:
        """
        PARSE IMD : balise EDI pour les statistiques et libellés des articles
        :param data: list of values
        """
        try:
            imd_qualifier, _, stat, *libelle = data

        except ValueError as except_error:
            raise OptoQualifierError(
                f"Impossible d'extraire les données du qualifier IMD : {data!r}"
                f", pour le fichier {self.edi_file!r}"
            ) from except_error

        if imd_qualifier != "F":
            return {}

        return {
            "libelle": "".join(libelle),
            "famille": f"{stat.replace('O', '0').replace(' ', '0')}".ljust(17, "0"),
        }

    def cmd_qty(self, data: list) -> dict:
        """
        PARSE QTY : balise EDI pour quantités
        :param data: list of values
        """
        try:
            qty_qualifier, qty, *_ = data

        except ValueError as except_error:
            raise OptoQualifierError(
                f"Impossible d'extraire les données du qualifier QTY : {data!r}"
                f", pour le fichier {self.edi_file!r}"
            ) from except_error

        if qty_qualifier != "47":
            return {}

        return {
            "qty": qty.replace("'", ""),
        }

    def cmd_pri(self, data: list) -> dict:
        """
        PARSE PRI : balise EDI pour les prix de référence de l'article
        :param data: list of values
        """
        try:
            pri_dict = {
                "AAB": "gross_unit_price",
                "AAA": "net_unit_price",
            }
            pri_qualifier, price, _, qualifier = data

        except ValueError as except_error:
            raise OptoQualifierError(
                f"Impossible d'extraire les données du qualifier PRI : {data!r}"
                f", pour le fichier {self.edi_file!r}"
            ) from except_error

        test_pri = pri_dict.get(pri_qualifier)

        if (pri_qualifier == "AAB" and qualifier == "GRP") or (
            pri_qualifier == "AAA" and qualifier == "NTP"
        ):
            return {test_pri: price.replace("'", "")}

        return {}

    def cmd_tax(self, data: list) -> dict:
        """
        PARSE TAX : balise EDI pour le taux de tva
        :param data: list of values
        """
        try:
            tax_qualifier, *_, tax = data

        except ValueError as except_error:
            raise OptoQualifierError(
                f"Impossible d'extraire les données du qualifier TAX : {data!r}"
                f", pour le fichier {self.edi_file!r}"
            ) from except_error

        if tax_qualifier != "7":
            return {}

        return {
            "vat_rate": tax.replace("'", ""),
        }

    def cmd_footer(self, data: list) -> dict:
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
        except ValueError as except_error:
            raise OptoParserError(
                f"Unable to extract data from the footer: '{data!r}'"
                f", pour le fichier {self.edi_file!r}"
            ) from except_error

        try:
            count = int(count)
        except (TypeError, ValueError) as except_error:
            raise OptoParserError(
                f"financial_document count should an int: '{count!r}'"
                f", pour le fichier {self.edi_file!r}"
            ) from except_error

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
            raise PathFileError(
                "EdiOpoto33Parser - edi_file :" f"{edi_file} - " "edi_file doit etre un fichier"
            )

        self.edi_file = edi_file
        self.cmd_parser = EDIQualifierParser(self.edi_file)
        self.cleaner = cleaner
        self.document = {}

    @staticmethod
    def extract_entries(lines: str) -> Generator:
        """
        Générateur ligne à ligne du fichier EDI opto 33 (factures)
            :param lines: lignes du fichier
            :return: code_parser, ligne
        """
        for line in lines:
            qualifier = line[:3]
            data = re.split(r"(?<![?])\+", line[4:])

            if qualifier:
                yield qualifier, data

    def entete_resume_parser(self, elements: list, invoice_dict: dict, detail: str) -> None:
        """Extraction des éléments de l'entête et du résumé"""
        try:
            for element in elements:
                qualifier, *data = element
                element_dict = self.cmd_parser.parse_qualifier(qualifier, data)

                if element_dict:
                    # print(element_dict)
                    invoice_dict.update(element_dict)

        except ValueError as except_error:
            raise OptoQualifierError(
                f"Impossible de parser {detail}: " f"{str(elements)!r}"
            ) from except_error

    def line_parser(self, articles: list, invoice_dict: dict, invoices_list: list) -> None:
        """Extraction des éléments des lignes"""
        invoice_detail_dict = deepcopy(invoice_dict)
        bl_dict = {
            "delivery_number": None,
            "delivery_date": None,
        }

        # Parser des lignes
        for element in articles:
            try:
                qualifier, *line_elements = element

                # Parsing du qualifier LIN pour ajout de la référence article ou code_ean
                line, *line_data = qualifier

            except ValueError as except_error:
                raise OptoQualifierError(
                    f"Impossible de parser element ou qualifier : " f"{str(element)!r}"
                ) from except_error

            article_dict = self.cmd_parser.parse_qualifier(line, line_data)
            qualifier_port_emb = ""

            for article_element in line_elements:
                try:
                    qualifier, *elements = article_element

                except ValueError as except_error:
                    raise OptoQualifierError(
                        f"Impossible de parser article_element en qualifier, *elements: "
                        f"{str(article_element)!r}"
                    ) from except_error

                element_cal = elements[0]
                qualifier = "MOAL" if qualifier == "MOA" else qualifier

                if qualifier in {"RFF", "DTM"} and element_cal in {"AAK", "35"}:
                    bl_dict.update(self.cmd_parser.parse_qualifier(qualifier, elements))

                if qualifier == "ALC":
                    test_element = str(elements[-1]).replace("'", "")

                    if test_element == "PC":
                        qualifier_port_emb = "packaging_amount"

                    elif test_element == "FC":
                        qualifier_port_emb = "transport_amount"

                    else:
                        qualifier_port_emb = ""

                elif qualifier == "MOAL" and element_cal == "8" and qualifier_port_emb:
                    price_dict = self.cmd_parser.parse_qualifier(qualifier, elements)

                    if price_dict.get("net_amount") != "0":
                        invoice_detail_dict[qualifier_port_emb] = price_dict.get("emb_port_price")

                        del price_dict["emb_port_price"]
                        # print(price_dict)
                        invoice_detail_dict.update(price_dict)

                    qualifier_port_emb = ""

                elif element_cal != "8":
                    invoice_detail_dict.update(self.cmd_parser.parse_qualifier(qualifier, elements))

            if article_dict:
                invoice_detail_dict.update(article_dict)
                invoice_detail_dict.update(bl_dict)

                invoices_list.append(invoice_detail_dict)
                invoice_detail_dict = deepcopy(invoice_dict)

    def extract_invoices(self, invoices: list) -> Generator:
        """
        Extraction des factures une à une
            :param invoices: générator des factures une à une
            :return: générateur des dictionaire des éléments des factures
        """
        try:
            invoices_list = []

            for invoice in self.invoices(invoices):
                try:
                    entete, *articles, resume, _ = invoice

                except ValueError as except_error:
                    raise OptoQualifierError(
                        f"Impossible de parser invoice en qualifier, entete, *articles, resume, _: "
                        f"{str(invoice)!r}"
                    ) from except_error

                invoice_dict = deepcopy(INVOICE_DICT)

                # Parser d'entête
                self.entete_resume_parser(entete[1:], invoice_dict, "l'entête")

                # Parser du résumé
                self.entete_resume_parser(resume, invoice_dict, "le résumé")

                # Paser des lignes
                self.line_parser(articles, invoice_dict, invoices_list)

            yield from invoices_list

        except (OptoLinesError, Exception) as except_error:
            raise OptoLinesError("Erreur dans l'extraction des factures") from except_error

    @staticmethod
    def invoices(lines: list) -> Generator:
        """
        Générateur des éléments des factures, factures par factures
        :param lines: lignes des fichiers
        """
        for line in lines:
            yield [
                [
                    re.split(r"(?<![?])\+|:", invoice_lines)
                    for invoice_lines in re.split(r"(?<!\?)['|\n]", invoice)
                    if invoice_lines
                ]
                for invoice in re.split(r"[\n|'](?=LIN)|[\n|'](?=UNS)|[\n|'](?=UNT)", line)
            ]

    def parse(self) -> dict:
        """
        Fontion de parsing du fichier bancaire
            :return: {"file_name": "", "edi_financial_documents": []}
        """
        encoding = encoding_detect(self.edi_file) or "ascii"

        with open(self.edi_file, encoding=encoding) as file:
            text = file.read().strip()
            try:
                _, header, *invoices, footer = re.split(
                    r"[\n|'](?=UNB)|[\n|'](?=UNH)|[\n|'](?=UNZ)" if text[:3] == "UNA"
                    # Certains fichiers EDI n'ont pas l'entête UNA
                    else r"(?=UNB)|[\n|'](?=UNH)|[\n|'](?=UNZ)",
                    text,
                )
            except ValueError as except_error:
                raise OptoParserError(
                    "Impossible d'extraire les données du pied de page du fichier :"
                    f" {self.edi_file.name!r}"
                ) from except_error

            header, footer = self.extract_entries([header, footer])
            footer_parse = self.cmd_parser.cmd_footer(footer[1])
            footer_count_invoices = footer_parse.get("financial_documents_count")

            # ANNULATION DE LA VALIDATION CAR JULBO NE RESPECTE PAS ID INTERCHANGE
            # On vérifie l'ID d'interchage
            if str(header[1][4]).replace("'", "") != footer_parse.get("document_id").replace(
                "'", ""
            ):
                # print(self.edi_file.name)
                # print(header, footer_parse.get("document_id"))
                raise OptoIdError(
                    rf"l'ID du fichier Edi '{self.edi_file.name}' en entête (UNB) "
                    r"et en pied de page (UNZ) sont différents"
                )

            # On vérifie que le nombre de factures est celui annoncé
            # if len(re.findall(r"UNH(?=\+)", text)) != footer_count_invoices:
            #     raise OptoNumberError(
            #         r"Il n'y a pas dans le fichier le nombre de factures "
            #         r"annoncé dans le pied de page (UNZ), "
            #         f"dans le fichier {self.edi_file.name!r}"
            #     )

            # ANNULATION DE LA VALIDATION CAR CooperVision NE RESPECTE PAS LE NOMBRE DE LIGNES
            # errors_list = []
            #
            # # On vérifie que toutes les lignes de factures sont présentes.
            # for line in self.invoices(invoices):
            #     entete, *_, resume = line
            #
            #     if len([_ for lis in line for _ in lis]) != int(resume[0][1]):
            #         errors_list.append(entete[1][2])
            #
            # if errors_list:
            #     raise OptoNumberError(
            #         f"Le nombre de lignes des factures/avoirs : {', '.join(errors_list)!r} "
            #         "ne correpond pas au "
            #         "nombre de lignes indiquées dans leur résumé (UNT), "
            #         f"dans le fichier {self.edi_file.name!r}"
            #     )

            return {
                "header": header,
                "footer": self.cmd_parser.cmd_footer(footer[1]),
                "invoices": self.extract_invoices(invoices),
                "get_columns": INVOICE_DICT,
                "count_invoices": footer_count_invoices,
            }
