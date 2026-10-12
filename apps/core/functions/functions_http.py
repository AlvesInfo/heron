"""Utilitaires HTTP : détection ajax, pagination, redirections sûres et boutons."""

from django.utils.html import format_html, format_html_join
from django.utils.http import url_has_allowed_host_and_scheme

from apps.core.functions.functions_setups import settings

DOMAINS_WHITELIST = settings.DOMAINS_WHITELIST


def is_ajax(request) -> bool:
    """FR : Requête émise en ajax (en-tête X-Requested-With: XMLHttpRequest) ; remplace la.

         méthode is_ajax de HttpRequest, supprimée dans Django 4.0
    EN : Ajax request detection (X-Requested-With header), replacement for the removed method
    :param request: HttpRequest Django
    :return: True si la requête porte l'en-tête ajax.
    """
    return request.headers.get("x-requested-with", "").lower() == "xmlhttprequest"


def get_limit(request, default: int = 50) -> int:
    """Nombre maximal de résultats demandé par le paramètre GET limit.

    :param request: requête Django
    :param default: valeur par défaut, aussi utilisée si le paramètre est absent, non numérique
                    ou non strictement positif
    :return: entier strictement positif.
    """
    try:
        limit = int(request.GET.get("limit", default))
    except (TypeError, ValueError):
        return default

    return limit if limit > 0 else default


def check_next_page(url):
    """Vérification de l'url de next page, pour s'assurer que la redirection n'a pas été remaniée.

    Sont acceptées les urls relatives internes (/book/...) et les urls absolues d'un domaine de la
    liste blanche ; tout le reste (domaine étranger, //hote, javascript:, vide) renvoie vers "/"
    :param url: url de next_page venue de request
    :return: url de redirection sûre.
    """
    if not url or not url_has_allowed_host_and_scheme(url, allowed_hosts=set(DOMAINS_WHITELIST)):
        return "/"

    return url


def get_button(
    actual_page,
    page,
    base_color,
    position_color,
    texte="",
):
    """Retourne le bouton de pagination demandé.

    :param actual_page: page actuelle du paginator
    :param page: page à écrire
    :param texte: icon à insérer (html sûr construit par format_html, sinon il est échappé)
    :param base_color: couleur des boutons du changement de page de base
    :param position_color: couleur des boutons du changement de page de la page affichée
    :return: retourne la balise html (échappée, marquée sûre) d'un bouton de pagination.
    """
    label = texte or page

    if page == actual_page:
        return format_html(
            '<div class="ui button pagination"  style="background-color: {};">{}</div>\n',
            position_color,
            label,
        )

    return format_html(
        '<div class="ui button pagination" onclick="paginateWithFilter({})" '
        'style="background-color: {};">{}</div>\n',
        page,
        base_color,
        label,
    )


def join_html(parts):
    """Concatène des fragments html sûrs en un fragment sûr (les fragments non sûrs sont échappés)."""
    return format_html_join("", "{}", ((part,) for part in parts))


def get_buttons(
    actual_page,
    nbre_pages,
    nbre_boutons,
    nbre,
    base_color="",
    position_color="blue",
):
    """Fonction qui va générer le html des boutons de pagination courants.

    :param actual_page: page actuelle du paginator
    :param nbre_pages: nombre de pages totales dans le paginator
    :param nbre_boutons: nombre de boutons souhaités
    :param nbre: nombre de boutons de chaque côté de l'actuelle page
    :param base_color: couleur des boutons de changement de page de base
    :param position_color: couleur des boutons de changement de page de la page affichée
    :return: les balises html à envoyer au template.
    """
    if nbre_pages <= nbre_boutons:
        pages = range(1, nbre_pages + 1)
    else:
        min_page = max(actual_page - nbre, 1)
        max_page = min(min_page + (2 * nbre), nbre_pages)

        if max_page > nbre_boutons:
            min_page = max_page - (2 * nbre)

        pages = range(min_page, max_page + 1)

    return join_html(
        get_button(actual_page, page, base_color=base_color, position_color=position_color)
        for page in pages
    )


def have_left(acutal_page, nbre):
    """Détermine s'il faut les flèches de gauche.

    :param acutal_page: index de la page actuelle
    :param nbre: nbre de boutons à droite et à gauche de la page actuelle
    :return: True ou False.
    """
    return (nbre + 2) <= acutal_page


def have_right(acutal_page, nbre_pages, nbre):
    """Détermine s'il faut les flèches de droite.

    :param acutal_page: index de la page actuelle
    :param nbre_pages: nombre de pages
    :param nbre: nbre de boutons à droite et à gauche de la page actuelle
    :return: True ou False.
    """
    return (nbre + acutal_page) < nbre_pages


ICON_LEFT = format_html('<i class="{} icon"></i>', "angle double left")
ICON_RIGHT = format_html('<i class="{} icon"></i>', "angle double right")


def get_pagination_buttons(
    acutal_page,
    nbre_pages,
    *,
    nbre_boutons=10,
    base_color="#FFFFFF",
    position_color="blue",
    icon_left=ICON_LEFT,
    icon_right=ICON_RIGHT,
):
    """Fonction qui va générer le html des boutons de pagination.

    :param acutal_page: page actuelle du paginator
    :param nbre_pages: nombre de pages totales dans le paginator
    :param nbre_boutons: nombre de boutons souhaités
    :param base_color: couleur des boutons de changement de page de base
    :param position_color: couleur des boutons de changement de page de la page affichée
    :param icon_left: icone vers la gauche (html sûr, sinon échappé)
    :param icon_right: icone vers la droite (html sûr, sinon échappé)
    :return: les balises html, marquées sûres : à afficher sans le filtre safe dans le template.
    """
    if nbre_pages == 1:
        return ""

    real_nbre_butons = nbre_boutons + 1 if nbre_boutons % 2 == 0 else nbre_boutons
    nbre = int((real_nbre_butons - 1) / 2)
    with_arrows = nbre_pages > nbre_boutons
    parts = []

    if with_arrows and have_left(acutal_page, nbre):
        parts.append(
            get_button(
                acutal_page,
                1,
                base_color=base_color,
                position_color=position_color,
                texte=icon_left,
            )
        )

    parts.append(
        get_buttons(
            acutal_page,
            nbre_pages,
            real_nbre_butons,
            nbre,
            base_color=base_color,
            position_color=position_color,
        )
    )

    if with_arrows and have_right(acutal_page, nbre_pages, nbre):
        parts.append(
            get_button(
                acutal_page,
                nbre_pages,
                base_color=base_color,
                position_color=position_color,
                texte=icon_right,
            )
        )

    return join_html(parts)
