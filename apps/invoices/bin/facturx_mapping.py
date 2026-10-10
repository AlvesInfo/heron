# pylint: disable=E0401,R0914,R0912,R0915
"""
FR : Construction du JSON de facture (schéma facturx_fr.models.Invoice) à partir
     d'une facture de vente heron (SaleInvoice + SaleInvoiceDetail)
EN : Builds the invoice JSON (facturx_fr.models.Invoice schema) from a heron
     sales invoice (SaleInvoice + SaleInvoiceDetail)

Règles de correspondance (voir facturx_conf.py) :
    - Vendeur  : Society liée à la centrale fille (ChildCenterPurchase.society)
    - Acheteur : Maison (CCT) facturée, à défaut le tiers X3 (Society)
    - Lignes   : SaleInvoiceDetail (quantité, prix unitaire net, taux TVA en %)
    - Avoirs   : type 381, montants exprimés en positif

Commentaire:

created at: 2026-10-10
created by: Paulo ALVES

modified at: 2026-10-10
modified by: Paulo ALVES
"""
import re
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

import pendulum
from bs4 import BeautifulSoup

from apps.accountancy.models import ModeReglement, VatSage
from apps.book.models import Society
from apps.centers_clients.models import Maison
from apps.centers_purchasing.models import ChildCenterPurchase
from apps.invoices.bin.facturx_conf import (
    DEFAULT_OPERATION_CATEGORY,
    DEFAULT_PAYMENT_MEANS_CODE,
    DEFAULT_UNIT_CODE,
    DEFAULT_ZERO_RATE_VAT_CATEGORY,
    DOMESTIC_COUNTRY_CODE,
    INVOICE_TYPE_CODES,
    OPERATION_CATEGORIES,
    PAYMENT_MEANS_KEYWORDS,
    UNIT_CODES,
    ZERO_RATE_VAT_CATEGORIES,
)
from apps.invoices.models import InvoiceCommonDetails, SaleInvoice, SaleInvoiceDetail

TWO_PLACES = Decimal("0.01")
FIVE_PLACES = Decimal("0.00001")
DIGITS_ONLY = re.compile(r"\D+")


class FacturXMappingError(Exception):
    """Données heron insuffisantes pour produire une facture Factur-X"""


def _clean(value: Any) -> str:
    """Nettoie une chaîne (None -> '')"""
    return str(value or "").strip()


def _digits(value: Any) -> str:
    """Ne conserve que les chiffres (SIREN, SIRET)"""
    return DIGITS_ONLY.sub("", _clean(value))


def _identifiers(*values: Any, country_code: str) -> Tuple[Optional[str], Optional[str]]:
    """
    (SIREN, SIRET) normalisés depuis les champs siren / siret (souvent mélangés en base).
    Hors France, les identifiants nationaux ne sont pas des SIREN : on ne renvoie rien.
    """
    if country_code != DOMESTIC_COUNTRY_CODE:
        return None, None

    siren = siret = None
    for value in values:
        digits = _digits(value)
        if len(digits) == 14 and siret is None:
            siret = digits
        elif len(digits) == 9 and siren is None:
            siren = digits

    if siren is None and siret:
        siren = siret[:9]

    return siren, siret


def _vat_number(value: Any) -> Optional[str]:
    """Normalise un numéro de TVA intracommunautaire (sans espaces, majuscules)"""
    cleaned = _clean(value).replace(" ", "").upper()
    return cleaned or None


def _country_code(country: Any, default: str = DOMESTIC_COUNTRY_CODE) -> str:
    """Code pays ISO 3166-1 alpha-2 depuis un objet Country ou une chaîne"""
    code = _clean(getattr(country, "country", country)).upper()
    return code[:2] if len(code) >= 2 else default


def _html_to_text(value: Any) -> str:
    """Convertit un texte HTML (CKEditor) en texte brut"""
    cleaned = _clean(value)
    if not cleaned:
        return ""
    return " ".join(BeautifulSoup(cleaned, "lxml").get_text(" ").split())


def _address(
    street: Any,
    additional: Any,
    city: Any,
    postal_code: Any,
    country: Any,
    fallback_street: str,
) -> Dict[str, Any]:
    """Construit une adresse conforme au modèle Address de facturx-fr"""
    street_text = _clean(street) or _clean(additional) or fallback_street
    additional_text = _clean(additional) if _clean(street) else ""
    return {
        "street": street_text,
        "additional_street": additional_text or None,
        "city": _clean(city) or "-",
        "postal_code": _clean(postal_code) or "-",
        "country_code": _country_code(country),
    }


def _party_from_society(society: Society, email: Optional[str] = None) -> Dict[str, Any]:
    """Partie (vendeur / acheteur) depuis un tiers X3"""
    name = _clean(society.corporate_name) or _clean(society.name) or _clean(society.short_name)
    address = _address(
        society.adresse,
        society.immeuble,
        society.ville,
        society.code_postal,
        society.country,
        fallback_street=name,
    )
    siren, siret = _identifiers(
        society.siren_number, society.siret_number, country_code=address["country_code"]
    )

    return {
        "name": name,
        "siren": siren,
        "siret": siret,
        "vat_number": _vat_number(society.vat_cee_number),
        "address": address,
        "email": _clean(email) or _clean(society.email) or None,
        "phone": _clean(society.telephone) or None,
    }


def _party_from_maison(maison: Maison, society: Optional[Society]) -> Dict[str, Any]:
    """Partie acheteur depuis la Maison (CCT) facturée, complétée par son tiers X3"""
    name = _clean(maison.invoice_entete) or _clean(maison.intitule)
    address = _address(
        maison.adresse,
        maison.immeuble,
        maison.ville,
        maison.code_postal,
        maison.pays,
        fallback_street=name,
    )
    siren, siret = _identifiers(
        maison.siren_number,
        maison.siret_number,
        society.siren_number if society else None,
        society.siret_number if society else None,
        country_code=address["country_code"],
    )
    vat_number = _vat_number(maison.vat_cee_number) or (
        _vat_number(society.vat_cee_number) if society else None
    )

    return {
        "name": name,
        "siren": siren,
        "siret": siret,
        "vat_number": vat_number,
        "address": address,
        # Adresse de livraison (BT-80 obligatoire pour les livraisons intracommunautaires)
        "delivery_address": address if address["country_code"] != DOMESTIC_COUNTRY_CODE else None,
        "email": _clean(getattr(maison, "email", "")) or None,
    }


def get_seller(sale: SaleInvoice) -> Tuple[Dict[str, Any], ChildCenterPurchase]:
    """
    Vendeur : Society liée à la centrale fille de la facture
    :param sale: facture de vente
    :return: (partie vendeur, centrale fille)
    """
    try:
        center = ChildCenterPurchase.objects.select_related("society", "society__country").get(
            code=sale.code_center
        )
    except ChildCenterPurchase.DoesNotExist as error:
        raise FacturXMappingError(
            f"Centrale fille {sale.code_center!r} introuvable pour la facture {sale.invoice_number}"
        ) from error

    if center.society is None:
        raise FacturXMappingError(
            f"La centrale fille {center.code} - {center.name} n'est liée à aucune Society "
            "(tiers X3 vendeur) : renseignez le champ 'Société vendeur' de la centrale fille"
        )

    seller = _party_from_society(center.society, email=center.sending_email)

    if not seller["siren"]:
        raise FacturXMappingError(
            f"Le tiers vendeur {center.society.third_party_num} n'a pas de n° SIREN / SIRET"
        )

    return seller, center


def get_buyer(sale: SaleInvoice) -> Dict[str, Any]:
    """
    Acheteur : Maison (CCT) facturée, à défaut le tiers X3 facturé
    :param sale: facture de vente
    :return: partie acheteur
    """
    society = (
        Society.objects.select_related("country")
        .filter(third_party_num=sale.third_party_num_id)
        .first()
    )
    maison = Maison.objects.select_related("pays").filter(cct=sale.cct_id).first()

    if maison is not None:
        return _party_from_maison(maison, society)

    if society is not None:
        return _party_from_society(society)

    raise FacturXMappingError(
        f"Aucune Maison ni tiers X3 trouvé pour le CCT {sale.cct_id} "
        f"(facture {sale.invoice_number})"
    )


def _vat_regimes() -> Dict[str, str]:
    """Code TVA X3 -> régime de TVA (FRA, CEE, EXP, DOM, ...)"""
    return dict(VatSage.objects.values_list("vat", "vat_regime"))


def _vat_category(
    vat_code: str, vat_rate: Decimal, regimes: Dict[str, str]
) -> Tuple[str, Any, Any]:
    """Catégorie TVA EN16931 d'une ligne : (catégorie, code motif, motif)"""
    if vat_rate > 0:
        return "S", None, None

    regime = _clean(regimes.get(vat_code)).upper()
    return ZERO_RATE_VAT_CATEGORIES.get(regime, DEFAULT_ZERO_RATE_VAT_CATEGORY)


def _payment_means_code(mode_reglement_uuid: Any) -> str:
    """Code moyen de paiement UNTDID 4461 depuis le mode de règlement X3"""
    if not mode_reglement_uuid:
        return DEFAULT_PAYMENT_MEANS_CODE

    mode = ModeReglement.objects.filter(uuid_identification=mode_reglement_uuid).first()

    if mode is None:
        return DEFAULT_PAYMENT_MEANS_CODE

    haystack = f"{_clean(mode.code)} {_clean(mode.name)} {_clean(mode.short_name)}".upper()

    for keyword, code in PAYMENT_MEANS_KEYWORDS:
        if keyword in haystack:
            return code

    return DEFAULT_PAYMENT_MEANS_CODE


def _line_quantities(
    detail: SaleInvoiceDetail, common: Optional[InvoiceCommonDetails], sign: int
) -> Tuple[Decimal, Decimal, Decimal]:
    """
    Quantité, prix unitaire et montant net d'une ligne, signés
    :param detail: ligne de vente
    :param common: ligne commune (porte la quantité), peut être None
    :param sign: 1 ou -1 (inversion des montants pour les avoirs)
    :return: (quantité, prix unitaire, montant net)
    """
    net_amount = (Decimal(detail.net_amount or 0) * sign).quantize(TWO_PLACES)
    qty = Decimal(getattr(common, "qty", None) or 0)

    if qty == 0:
        # Pas de quantité : une unité au montant net
        return Decimal("1"), net_amount, net_amount

    qty = (qty * sign).quantize(FIVE_PLACES)
    unit_price = Decimal(detail.net_unit_price or 0).quantize(FIVE_PLACES)

    return qty, unit_price, net_amount


def _line_adjustments(
    qty: Decimal, unit_price: Decimal, net_amount: Decimal
) -> Tuple[Optional[Decimal], Optional[Decimal]]:
    """
    Écart d'arrondi entre qty x PU et le montant net réellement facturé :
    absorbé dans une remise / majoration de ligne pour conserver les totaux heron
    :return: (remise, majoration), None si sans objet
    """
    gap = (net_amount - (qty * unit_price)).quantize(TWO_PLACES)

    if gap < 0:
        return -gap, None

    if gap > 0:
        return None, gap

    return None, None


def _build_line(
    number: int,
    sale: SaleInvoice,
    detail: SaleInvoiceDetail,
    common: Optional[InvoiceCommonDetails],
    sign: int,
    regimes: Dict[str, str],
) -> Dict[str, Any]:
    """
    Ligne de facture au format facturx-fr
    :param number: numéro de ligne
    :param sale: facture de vente
    :param detail: ligne de vente
    :param common: ligne commune (quantité, libellé, référence), peut être None
    :param sign: 1 ou -1 (inversion des montants pour les avoirs)
    :param regimes: code TVA X3 -> régime de TVA
    :return: ligne au format facturx-fr
    """
    libelle = _clean(getattr(common, "libelle", ""))
    reference = _clean(getattr(common, "reference_article", ""))
    order_number = _clean(getattr(common, "acuitis_order_number", ""))

    qty, unit_price, net_amount = _line_quantities(detail, common, sign)
    discount, charge = _line_adjustments(qty, unit_price, net_amount)

    vat_rate = (Decimal(detail.vat_rate or 0) * 100).quantize(TWO_PLACES)
    category, reason_code, reason = _vat_category(detail.vat, vat_rate, regimes)

    description = (
        libelle
        or reference
        or _clean(detail.sub_category)
        or _clean(detail.big_category)
        or sale.big_category
    )

    return {
        "line_number": number,
        "description": description[:500],
        "quantity": str(qty),
        "unit": UNIT_CODES.get(detail.unit_weight_id, DEFAULT_UNIT_CODE),
        "unit_price": str(unit_price),
        "vat_rate": str(vat_rate),
        "vat_category": category,
        "item_reference": reference[:50] or None,
        "buyer_reference": order_number[:50] or None,
        "discount_amount": str(discount) if discount else None,
        "charge_amount": str(charge) if charge else None,
        "vat_exemption_reason": reason,
        "vat_exemption_reason_code": reason_code,
    }


def build_lines(sale: SaleInvoice, sign: int, regimes: Dict[str, str]) -> List[Dict[str, Any]]:
    """
    Lignes de facture depuis les SaleInvoiceDetail
    :param sale: facture de vente
    :param sign: 1 ou -1 (inversion des montants pour les avoirs)
    :param regimes: code TVA X3 -> régime de TVA
    :return: liste des lignes au format facturx-fr
    """
    details = list(SaleInvoiceDetail.objects.filter(uuid_invoice=sale).order_by("ranking", "pk"))
    # Quantités, libellés et références article sont dans InvoiceCommonDetails
    # (lignes communes achats / ventes), jointes par import_uuid_identification
    commons = {
        common.import_uuid_identification: common
        for common in InvoiceCommonDetails.objects.filter(
            import_uuid_identification__in=[detail.import_uuid_identification for detail in details]
        ).only(
            "import_uuid_identification",
            "qty",
            "libelle",
            "reference_article",
            "ean_code",
            "acuitis_order_number",
        )
    }
    lines = [
        _build_line(
            number, sale, detail, commons.get(detail.import_uuid_identification), sign, regimes
        )
        for number, detail in enumerate(details, 1)
    ]

    if not lines:
        raise FacturXMappingError(f"La facture {sale.invoice_number} n'a aucune ligne de détail")

    return lines


def _check_totals(lines: List[Dict[str, Any]], amount_ht: Decimal, sign: int) -> List[str]:
    """
    Contrôle de cohérence des totaux HT des lignes avec la facture heron
    :param lines: lignes au format facturx-fr
    :param amount_ht: montant HT de la facture heron
    :param sign: 1 ou -1 (inversion des montants pour les avoirs)
    :return: liste d'avertissements (vide si cohérent)
    """
    total_lines = sum(
        (Decimal(line["quantity"]) * Decimal(line["unit_price"]))
        - Decimal(line["discount_amount"] or 0)
        + Decimal(line["charge_amount"] or 0)
        for line in lines
    ).quantize(TWO_PLACES)
    expected = (amount_ht * sign).quantize(TWO_PLACES)

    if total_lines != expected:
        return [f"Total HT des lignes ({total_lines}) différent du total HT heron ({expected})"]

    return []


def _payment_means(sale: SaleInvoice) -> Dict[str, Any]:
    """Moyen de paiement (code + coordonnées bancaires du centre si connues)"""
    centers = sale.centers
    iban = _clean(getattr(centers, "iban", "") or getattr(centers, "iban_center", "")).replace(
        " ", ""
    )
    bic = _clean(getattr(centers, "code_swift_center", "")).replace(" ", "")

    payment_means: Dict[str, Any] = {"code": _payment_means_code(sale.mode_reglement)}
    if iban:
        payment_means["bank_account"] = {"iban": iban, "bic": bic or None}

    return payment_means


def _payment_terms(sale: SaleInvoice) -> Optional[Dict[str, str]]:
    """Conditions de paiement depuis les paramètres du client"""
    condition = _clean(getattr(sale.parties, "payment_condition_client", ""))

    if condition:
        return {"description": condition}

    return None


def _billing_period(sale: SaleInvoice) -> Tuple[Optional[str], Optional[str]]:
    """Période de facturation (mois de facture) au format ISO"""
    invoice_month = sale.invoice_month

    if not invoice_month:
        return None, None

    period = pendulum.parse(invoice_month.isoformat())

    return (
        period.start_of("month").date().isoformat(),
        period.end_of("month").date().isoformat(),
    )


def _invoice_note(sale: SaleInvoice) -> str:
    """Note de facture : type, catégorie, CCT et mentions légales du centre"""
    note_parts = [f"{sale.invoice_type_name} {sale.big_category} - CCT {sale.cct_id}"]
    legal_notice = _html_to_text(getattr(sale.centers, "legal_notice_center", ""))

    if legal_notice:
        note_parts.append(legal_notice)

    return "\n".join(note_parts)[:1000]


def build_facturx_invoice(sale: SaleInvoice) -> Tuple[Dict[str, Any], List[str]]:
    """
    Construit le JSON de la facture pour le serveur Factur-X
    :param sale: facture de vente heron (SaleInvoice)
    :return: (facture JSON-compatible, liste d'avertissements non bloquants)
    """
    type_code = INVOICE_TYPE_CODES.get(_clean(sale.invoice_type).upper())
    if type_code is None:
        raise FacturXMappingError(
            f"Type de facture inconnu {sale.invoice_type!r} pour la facture {sale.invoice_number}"
        )

    # Les avoirs (381) sont exprimés en montants positifs
    amount_ht = Decimal(sale.invoice_amount_without_tax or 0)
    sign = -1 if (type_code == "381" and amount_ht < 0) else 1

    seller, center = get_seller(sale)
    buyer = get_buyer(sale)
    lines = build_lines(sale, sign, _vat_regimes())

    warnings = _check_totals(lines, amount_ht, sign)
    if buyer["address"]["country_code"] == DOMESTIC_COUNTRY_CODE and not buyer["siren"]:
        warnings.append(f"Acheteur français {buyer['name']!r} sans n° SIREN")

    period_start, period_end = _billing_period(sale)

    invoice = {
        "number": sale.invoice_number,
        "issue_date": sale.invoice_date.isoformat(),
        "due_date": sale.date_echeance.isoformat() if sale.date_echeance else None,
        "type_code": type_code,
        "currency": _clean(sale.devise) or "EUR",
        "seller": seller,
        "buyer": buyer,
        "lines": lines,
        "operation_category": OPERATION_CATEGORIES.get(
            _clean(sale.big_category_slug_name), DEFAULT_OPERATION_CATEGORY
        ),
        "vat_on_debits": False,
        "buyer_accounting_reference": _clean(sale.cct_id) or None,
        "contract_reference": _clean(center.member_num) or None,
        "payment_terms": _payment_terms(sale),
        "payment_means": _payment_means(sale),
        "billing_period_start": period_start,
        "billing_period_end": period_end,
        "note": _invoice_note(sale),
    }

    return invoice, warnings
