# pylint: disable=E0401,W0621
"""FR : Tests du parseur des fichiers EDI OPTO 33 (apps/data_flux/opto_33_parser.py)


EN : Tests for the EDI OPTO 33 files parser

Commentaire:

Les messages d'essai sont construits à partir des segments attendus par le parseur :
UNA / UNB en-tête d'échange, UNH / BGM / DTM / NAD / RFF en-tête de facture, LIN + IMD / QTY /
PRI / TAX / MOA / ALC / RFF / DTM par ligne, UNS + MOA résumé, UNT fin de message, UNZ pied de
page. Les segments sont terminés par une apostrophe et séparés par un retour à la ligne.

created at: 2026-10-11
created by: Paulo ALVES
"""

import io
from pathlib import Path

import pytest

from apps.data_flux.exceptions import (
    OptoDateError,
    OptoIdError,
    OptoLinesError,
    OptoParserError,
    OptoQualifierError,
    PathFileError,
    PathTypeError,
)
from apps.data_flux.opto_33_parser import (
    INVOICE_DICT,
    EdiOpoto33Parser,
    EDIQualifierParser,
    edi_iso_date_format,
)

HEADER = ["UNA:+.? ", "UNB+UNOC:3+FOUR001+ACUITIS+220420:1200+1863"]
ENTETE = [
    "UNH+1+INVOIC:D:96B:UN:OPTO33",
    "BGM+380+FAC001+9",
    "DTM+3:20220420:102",
    "DTM+4:220401:101",
    "DTM+99:20220101:102",
    "NAD+SU+12345+9+FOURNISSEUR+OPTIQUE SAS",
    "NAD+BY+AF0001+160+MAGASIN+ACUITIS PARIS+12 RUE DE LA PAIX+75001",
    "NAD+PR+12345678900011+9+PAYEUR+ACUITIS SAS",
    "NAD+DP+LIVRAISON",
    "NAD+BY+AF0002",
    "RFF+ON:CMD123",
    "RFF+AEG:Client Dupont",
    "RFF+ACD:livraison urgente",
    "RFF+ZZ:ignore",
    "RFF+XX",
]
LINE_1 = [
    "LIN+1++ART001:IN::21",
    "IMD+F+123+O123 4 5:MONTURE+TITANE",
    "IMD+F+35+x:ignore",
    "IMD+B+1+x:ignore",
    "QTY+47:2",
    "QTY+12:5",
    "PRI+AAB:100:CT:GRP",
    "PRI+AAA:90:CT:NTP",
    "PRI+AAA:80:CT:GRP",
    "TAX+7+VAT+++:::20",
    "TAX+5+VAT+++:::0",
    "MOA+98:200",
    "MOA+125:180",
    "MOA+128:216",
    "MOA+77:1",
    "RFF+AAK:BL123",
    "DTM+35:20220415:102",
]
LINE_2 = [
    "LIN+2++3600000000001:EN::21",
    "QTY+47:1",
    "ALC+C++++PC",
    "MOA+8:5",
    "ALC+C++++FC",
    "MOA+8:0",
    "ALC+C++++XX",
    "MOA+8:3",
    "MOA+8:4",
]
LINE_COMMENT = ["LIN+3++COMMENTAIRE:IN::20", "IMD+F+1+:TEXTE LIBRE"]
LINE_3 = ["LIN+4++ART004:IN::21:Z", "QTY+47:3"]
RESUME = ["UNS+S", "MOA+125:1000", "MOA+128:1200", "MOA+9:0", "UNT+30+1"]
FOOTER = ["UNZ+1+1863"]


def _edi_text(*blocks, with_una=True):
    """Texte d'un fichier EDI : segments terminés par une apostrophe, un segment par ligne"""
    segments = [*(HEADER if with_una else HEADER[1:])]

    for block in blocks:
        segments.extend(block)

    return "'\n".join(segments) + "'"


@pytest.fixture
def edi_file(tmp_path):
    """Fabrique de fichiers EDI sous tmp_path"""

    def _factory(text, name="facture.edi"):
        path = tmp_path / name
        path.write_text(text, encoding="utf8")
        return path

    return _factory


def _invoices(path):
    return list(EdiOpoto33Parser(path).parse()["invoices"])


# DATES ============================================================================================


@pytest.mark.parametrize(
    ("qualifier", "value", "expected"),
    [
        ("2", "250422", "2022-04-25"),
        ("3", "042522", "2022-04-25"),
        ("101", "220425", "2022-04-25"),
        ("102'", "20220425", "2022-04-25"),
        ("201", "2204251230", "2022-04-25"),
        ("202", "220425123045", "2022-04-25"),
        ("203", "202204251230", "2022-04-25"),
        ("204", "20220425123045", "2022-04-25"),
        ("301", "2204251230+0100", "2022-04-25"),
        ("302", "220425123045+0100", "2022-04-25"),
        ("303", "202204251230+0100", "2022-04-25"),
        ("304", "20220425123045+0100", "2022-04-25"),
        ("102", "00000000", "1900-01-01"),
    ],
)
def test_edi_iso_date_format(qualifier, value, expected):
    """Chaque qualifiant de date EDI est converti en date iso, 00000000 vaut 1900-01-01"""
    assert edi_iso_date_format(qualifier, value) == expected


@pytest.mark.parametrize(
    ("qualifier", "value"), [("999", "20220425"), ("102", "2022-04-25"), ("2", "")]
)
def test_edi_iso_date_format_invalide(qualifier, value):
    with pytest.raises(OptoDateError, match="is not in edi date format dictionnary"):
        edi_iso_date_format(qualifier, value)


# QUALIFIANTS ======================================================================================


@pytest.fixture
def qualifier():
    return EDIQualifierParser(Path("facture.edi"))


def test_parse_qualifier_inconnu(qualifier):
    assert qualifier.edi_file == "facture.edi"
    assert qualifier.parse_qualifier("XYZ", ["a"]) == {}
    assert qualifier.parse_qualifier("BGM", ["380", "FAC001'", "9"]) == {
        "invoice_type": "380",
        "invoice_number": "FAC001",
    }


def test_cmd_unh(qualifier):
    assert qualifier.cmd_unh(["426914", "INVOIC:D:96B:UN:OPTO33"]) == {
        "financial_document_number": "426914",
        "metadata": ["INVOIC", "D", "96B", "UN"],
        "format": "OPTO33",
    }

    with pytest.raises(OptoQualifierError, match="UNH"):
        qualifier.cmd_unh(["426914"])


def test_cmd_bgm_invalide(qualifier):
    with pytest.raises(OptoQualifierError, match="BGM"):
        qualifier.cmd_bgm(["380"])


def test_cmd_dtm(qualifier):
    assert qualifier.cmd_dtm(["3", "20220420'", "102"]) == {"invoice_date": "2022-04-20"}
    assert qualifier.cmd_dtm(["35", "220415", "101"]) == {"delivery_date": "2022-04-15"}
    assert qualifier.cmd_dtm(["4", "20220401", "102"]) == {"acuitis_order_date": "2022-04-01"}
    assert qualifier.cmd_dtm(["99", "20220401", "102"]) == {}

    with pytest.raises(OptoQualifierError, match="DTM"):
        qualifier.cmd_dtm(["3", "20220420"])


def test_cmd_nad(qualifier):
    """Fournisseur (avec ou sans qualifiant d'identifiant), payeur, maison livrée, autres ignorés"""
    assert qualifier.cmd_nad(["SU", "12345'", "9", "FOURNISSEUR", "OPTIQUE'SAS"]) == {
        "supplier": "OPTIQUE SAS",
        "supplier_ident": "12345",
    }
    assert qualifier.cmd_nad(["II", "777", "", "LUXOTTICA", ""]) == {
        "supplier": "LUXOTTICA",
        "supplier_ident": "777",
    }
    assert qualifier.cmd_nad(["PR", "12345678900011'", "9", "PAYEUR", "ACUITIS"]) == {
        "siret_payeur": "12345678900011"
    }
    assert qualifier.cmd_nad(
        ["BY", "AF0001", "160", "MAGASIN", "ACUITIS PARIS", "12 RUE'", "", "75001"]
    ) == {
        "maison": "ACUITIS PARIS 12 RUE  75001",
        "code_maison": "AF0001",
    }
    assert qualifier.cmd_nad(["BY", "FOUR01", "92", "", "MAGASIN"]) == {
        "maison": "MAGASIN",
        "code_fournisseur": "FOUR01",
    }
    assert qualifier.cmd_nad(["DP", "LIVRAISON"]) == {}
    assert qualifier.cmd_nad(["BY", "AF0002"]) == {}

    with pytest.raises(OptoParserError, match="NAD"):
        qualifier.cmd_nad([])

    with pytest.raises(OptoQualifierError, match="NAD"):
        qualifier.cmd_nad(["SU", "12345"])


def test_cmd_moa_et_moal(qualifier):
    assert qualifier.cmd_moa(["125", "1000'"]) == {"invoice_amount_without_tax": "1000"}
    assert qualifier.cmd_moa(["128", "1200"]) == {"invoice_amount_with_tax": "1200"}
    assert qualifier.cmd_moa(["9", "1"]) == {}
    assert qualifier.cmd_moal(["98", "200"]) == {"gross_amount": "200"}
    assert qualifier.cmd_moal(["125", "180"]) == {"net_amount": "180"}
    assert qualifier.cmd_moal(["128", "216'"]) == {"amount_with_vat": "216"}
    assert qualifier.cmd_moal(["77", "1"]) == {}
    assert qualifier.cmd_moal(["8", "5"]) == {
        "gross_unit_price": "5",
        "net_unit_price": "5",
        "gross_amount": "5",
        "net_amount": "5",
        "emb_port_price": "5",
    }

    with pytest.raises(OptoQualifierError, match="MOA :"):
        qualifier.cmd_moa(["125"])

    with pytest.raises(OptoQualifierError, match=r"MOA\(L\)"):
        qualifier.cmd_moal(["125", "1", "2"])


def test_cmd_lin(qualifier):
    """Référence ou code ean selon le type de code, ligne de type 20 ignorée"""
    assert qualifier.cmd_lin(["1", "", "ART001'", "IN", "", "21"]) == {
        "reference_article": "ART001"
    }
    assert qualifier.cmd_lin(["2", "", "3600000000001", "EN", "", "21"]) == {
        "ean_code": "3600000000001"
    }
    assert qualifier.cmd_lin(["2", "", "3600000000001", "EAN", "", "21"]) == {
        "ean_code": "3600000000001"
    }
    assert qualifier.cmd_lin(["3", "", "X", "IN", "", "20"]) == {}
    assert qualifier.cmd_lin(["4", "", "ART004", "IN", "", "21", "Z"]) == {
        "reference_article": "ART004"
    }

    with pytest.raises(OptoQualifierError, match="LIN"):
        qualifier.cmd_lin(["21"])


def test_cmd_rff(qualifier):
    assert qualifier.cmd_rff(["AAK", "BL123"]) == {"delivery_number": "BL123"}
    assert qualifier.cmd_rff(["ON", "CMD123", "x"]) == {"acuitis_order_number": "CMD123"}
    assert qualifier.cmd_rff(["AEG", "Client"]) == {"client_name": "Client"}
    assert qualifier.cmd_rff(["ACD", "commentaire"]) == {"comment": "commentaire"}
    assert qualifier.cmd_rff(["ZZ", "x"]) == {}
    assert qualifier.cmd_rff(["XX"]) == {}

    with pytest.raises(OptoQualifierError, match="RFF"):
        qualifier.cmd_rff([])


def test_cmd_imd(qualifier):
    """Libellé concaténé et famille statistique normalisée sur 17 caractères"""
    assert qualifier.cmd_imd(["F", "123", "O123 4 5", "MONTURE", "TITANE"]) == {
        "libelle": "MONTURETITANE",
        "famille": "01230405000000000",
    }
    assert qualifier.cmd_imd(["F", "35", "x", "ignore"]) == {}
    assert qualifier.cmd_imd(["B", "1", "x"]) == {}

    with pytest.raises(OptoQualifierError, match="IMD"):
        qualifier.cmd_imd(["F", "1"])


def test_cmd_qty_pri_tax(qualifier):
    assert qualifier.cmd_qty(["47", "2'"]) == {"qty": "2"}
    assert qualifier.cmd_qty(["12", "5"]) == {}
    assert qualifier.cmd_pri(["AAB", "100'", "CT", "GRP"]) == {"gross_unit_price": "100"}
    assert qualifier.cmd_pri(["AAA", "90", "CT", "NTP"]) == {"net_unit_price": "90"}
    assert qualifier.cmd_pri(["AAA", "80", "CT", "GRP"]) == {}
    assert qualifier.cmd_tax(["7", "VAT", "", "", "", "20'"]) == {"vat_rate": "20"}
    assert qualifier.cmd_tax(["5", "VAT", "0"]) == {}

    with pytest.raises(OptoQualifierError, match="QTY"):
        qualifier.cmd_qty([])

    with pytest.raises(OptoQualifierError, match="PRI"):
        qualifier.cmd_pri(["AAB", "100"])

    with pytest.raises(OptoQualifierError, match="TAX"):
        qualifier.cmd_tax([])


def test_cmd_footer(qualifier):
    assert qualifier.cmd_footer(["25", "1863'"]) == {
        "document_id": "1863'",
        "financial_documents_count": 25,
    }

    with pytest.raises(OptoParserError, match="footer"):
        qualifier.cmd_footer(["25"])

    with pytest.raises(OptoParserError, match="should an int"):
        qualifier.cmd_footer(["x", "1863"])


# PARSEUR DE FICHIER ===============================================================================


def test_parser_source_invalide(tmp_path):
    source = io.StringIO("UNA")

    with pytest.raises(PathTypeError):
        EdiOpoto33Parser(source)

    with pytest.raises(PathTypeError):
        EdiOpoto33Parser("facture.edi")

    with pytest.raises(PathFileError):
        EdiOpoto33Parser(tmp_path / "absent.edi")


def test_extract_entries_et_invoices():
    """Découpage des segments d'en-tête et des blocs de facture (sans couper les + échappés)"""
    assert list(EdiOpoto33Parser.extract_entries(["UNB+UNOC:3+A+B'", "", "UNZ+1+ID'"])) == [
        ("UNB", ["UNOC:3", "A", "B'"]),
        ("UNZ", ["1", "ID'"]),
    ]
    blocks = next(
        EdiOpoto33Parser.invoices(
            ["UNH+1+X'\nBGM+380+F1+9'\nLIN+1++A?+B:IN::21'\nQTY+47:1'\nUNS+S'\nMOA+125:1'\nUNT+5+1"]
        )
    )

    assert blocks == [
        [["UNH", "1", "X"], ["BGM", "380", "F1", "9"]],
        [["LIN", "1", "", "A?+B", "IN", "", "21"], ["QTY", "47", "1"]],
        [["UNS", "S"], ["MOA", "125", "1"]],
        [["UNT", "5", "1"]],
    ]


def test_parse_facture_complete(edi_file):
    """Une facture de trois lignes (la ligne de type 20 est ignorée) avec en-tête, résumé et frais"""
    parser = EdiOpoto33Parser(
        edi_file(_edi_text(ENTETE, LINE_1, LINE_2, LINE_COMMENT, LINE_3, RESUME, FOOTER))
    )

    content = parser.parse()
    invoices = list(content["invoices"])

    assert content["header"] == ("UNB", ["UNOC:3", "FOUR001", "ACUITIS", "220420:1200", "1863'"])
    assert content["footer"] == {"document_id": "1863'", "financial_documents_count": 1}
    assert content["count_invoices"] == 1
    assert content["get_columns"] is INVOICE_DICT
    assert [row["reference_article"] or row["ean_code"] for row in invoices] == [
        "ART001",
        "3600000000001",
        "ART004",
    ]

    first = invoices[0]
    assert set(first) == set(INVOICE_DICT)
    assert (
        first["invoice_type"],
        first["invoice_number"],
        first["invoice_date"],
        first["acuitis_order_date"],
    ) == ("380", "FAC001", "2022-04-20", "2022-04-01")
    assert (first["supplier"], first["supplier_ident"], first["siret_payeur"]) == (
        "OPTIQUE SAS",
        "12345",
        "12345678900011",
    )
    assert (first["maison"], first["code_maison"], first["code_fournisseur"]) == (
        "ACUITIS PARIS 12 RUE DE LA PAIX 75001",
        "AF0001",
        "",
    )
    assert (first["acuitis_order_number"], first["client_name"], first["comment"]) == (
        "CMD123",
        "Client Dupont",
        "livraison urgente",
    )
    assert (first["invoice_amount_without_tax"], first["invoice_amount_with_tax"]) == (
        "1000",
        "1200",
    )
    assert (first["libelle"], first["famille"], first["qty"]) == (
        "MONTURETITANE",
        "01230405000000000",
        "2",
    )
    assert (first["gross_unit_price"], first["net_unit_price"], first["vat_rate"]) == (
        "100",
        "90",
        "20",
    )
    assert (first["gross_amount"], first["net_amount"], first["amount_with_vat"]) == (
        "200",
        "180",
        "216",
    )
    assert (first["delivery_number"], first["delivery_date"]) == ("BL123", "2022-04-15")
    assert (first["packaging_amount"], first["transport_amount"]) == ("0", "0")

    second = invoices[1]
    assert (second["ean_code"], second["reference_article"], second["qty"]) == (
        "3600000000001",
        "",
        "1",
    )
    # frais d'emballage portés par MOA+8 après ALC PC ; port à 0 ignoré ; ALC inconnu ignoré
    assert (second["packaging_amount"], second["transport_amount"]) == ("5", "0")
    assert (second["gross_unit_price"], second["net_amount"]) == ("5", "5")
    # les références de livraison de la ligne précédente sont reportées sur les lignes suivantes
    assert (second["delivery_number"], second["delivery_date"]) == ("BL123", "2022-04-15")
    assert invoices[2]["qty"] == "3"
    assert invoices[2]["invoice_number"] == "FAC001"


def test_parse_sans_segment_una_et_plusieurs_factures(edi_file):
    """Certains fournisseurs n'envoient pas UNA ; deux factures dans l'échange"""
    second = ["UNH+2+INVOIC:D:96B:UN:OPTO33", "BGM+381+AVO001+9", "DTM+3:20220421:102"]
    text = _edi_text(
        ENTETE,
        LINE_1,
        RESUME,
        second,
        LINE_3,
        ["UNS+S", "MOA+125:10", "UNT+6+2"],
        ["UNZ+2+1863"],
        with_una=False,
    )

    invoices = _invoices(edi_file(text))

    assert [(row["invoice_number"], row["invoice_type"], row["qty"]) for row in invoices] == [
        ("FAC001", "380", "2"),
        ("AVO001", "381", "3"),
    ]
    assert invoices[1]["invoice_amount_without_tax"] == "10"
    assert invoices[1]["supplier"] == ""


def test_parse_pied_de_page_absent(edi_file):
    parser = EdiOpoto33Parser(edi_file("UNA:+.? '\nUNB+UNOC:3+A+B+220420:1200+1863'"))

    with pytest.raises(OptoParserError, match="pied de page"):
        parser.parse()


def test_parse_identifiants_d_echange_differents(edi_file):
    parser = EdiOpoto33Parser(edi_file(_edi_text(ENTETE, LINE_1, RESUME, ["UNZ+1+9999"])))

    with pytest.raises(OptoIdError, match="UNB"):
        parser.parse()


def test_parse_nombre_de_factures_invalide(edi_file):
    parser = EdiOpoto33Parser(edi_file(_edi_text(ENTETE, LINE_1, RESUME, ["UNZ+x+1863"])))

    with pytest.raises(OptoParserError, match="should an int"):
        parser.parse()


def test_extract_invoices_facture_incomplete(edi_file):
    """Une facture sans lignes ni résumé ne peut pas être découpée : OptoLinesError à la lecture"""
    parser = EdiOpoto33Parser(
        edi_file(
            _edi_text(["UNH+1+INVOIC:D:96B:UN:OPTO33", "BGM+380+FAC001+9"], ["UNT+2+1"], FOOTER)
        )
    )

    invoices = parser.parse()["invoices"]

    with pytest.raises(OptoLinesError, match="extraction des factures") as excinfo:
        list(invoices)

    assert isinstance(excinfo.value.__cause__, OptoQualifierError)


def test_extract_invoices_segment_d_entete_invalide(edi_file):
    """Un segment NAD fournisseur incomplet dans l'en-tête remonte en OptoLinesError"""
    parser = EdiOpoto33Parser(
        edi_file(_edi_text(["UNH+1+X", "BGM+380+FAC001+9", "NAD+SU+12345"], LINE_1, RESUME, FOOTER))
    )
    invoices = parser.parse()["invoices"]

    with pytest.raises(OptoLinesError):
        list(invoices)


def test_entete_resume_parser_element_vide(edi_file):
    """Un élément vide (sans qualifiant) de l'en-tête : OptoQualifierError"""
    parser = EdiOpoto33Parser(edi_file(_edi_text(ENTETE, LINE_1, RESUME, FOOTER)))

    with pytest.raises(OptoQualifierError, match="l'entête"):
        parser.entete_resume_parser([[]], {}, "l'entête")


def test_line_parser_elements_invalides(edi_file):
    """Bloc de ligne vide ou segment de ligne vide : OptoQualifierError"""
    parser = EdiOpoto33Parser(edi_file(_edi_text(ENTETE, LINE_1, RESUME, FOOTER)))
    invoice_dict = dict(INVOICE_DICT)
    invoices = []

    with pytest.raises(OptoQualifierError, match="element ou qualifier"):
        parser.line_parser([[]], invoice_dict, invoices)

    with pytest.raises(OptoQualifierError, match="article_element"):
        parser.line_parser([[["LIN", "1", "", "ART", "IN", "", "21"], []]], invoice_dict, invoices)

    assert invoices == []
