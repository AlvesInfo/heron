from urllib.parse import urlparse

from apps.core.functions.functions_setups import settings

DOMAINS_WHITELIST = settings.DOMAINS_WHITELIST


def check_next_page(url):
    """Vérification de l'url de next page, pour s'assurer que la redirection n'a pas été remanié
    :param url: url de next_page venue de request
    :return:
    """
    parsed_uri = urlparse(url)

    if not url or parsed_uri.netloc not in DOMAINS_WHITELIST:
        return "/"

    return url


def get_button(
    actual_page,
    page,
    base_color,
    position_color,
    texte="",
):
    """Retourne le bouton de pagination demandé
    :param actual_page: page actuelle du paginator
    :param page: page à écrire
    :param texte: icon à insérer
    :param base_color: couleur des boutons du changement de page de base
    :param position_color: couleur des boutons du changement de page de la page affichée
    :return: retourne la balise html d'un bouton de pagination
    """
    color = position_color if page == actual_page else base_color
    filter_function = "" if page == actual_page else f'onclick="paginateWithFilter({page})"'
    return (
        f'<div class="ui button pagination" '
        f'{filter_function} style="background-color: {color};">{texte or page}</div>\n'
    )


def get_buttons(
    actual_page,
    nbre_pages,
    nbre_boutons,
    nbre,
    base_color="",
    position_color="blue",
):
    """Fonction qui va générer le html des boutons de pagination courants
    :param actual_page: page actuelle du paginator
    :param nbre_pages: nombre de pages totales dans le paginator
    :param nbre_boutons: nombre de boutons souhaités
    :param nbre: nombre de boutons de chaque côté de l'actuelle page
    :param base_color: couleur des boutons de changement de page de base
    :param position_color: couleur des boutons de changement de page de la page affichée
    :return: les balises html à envoyer au template
    """
    balises = ""

    if nbre_pages <= nbre_boutons:
        for i in range(1, nbre_pages + 1):
            balises += get_button(
                actual_page, i, base_color=base_color, position_color=position_color
            )
        return balises

    min_page = 1 if actual_page - nbre < 1 else actual_page - nbre
    max_page = min(min_page + (2 * nbre), nbre_pages)

    if max_page > nbre_boutons:
        min_page = max_page - (2 * nbre)

    for j in range(min_page, max_page + 1):
        balises += get_button(actual_page, j, base_color=base_color, position_color=position_color)

    return balises


def have_left(acutal_page, nbre):
    """Détermine s'il faut les flèches de gauche
    :param acutal_page: index de la page actuelle
    :param nbre: nbre de boutons à droite et à gauche de la page actuelle
    :return: True ou False
    """
    return (nbre + 2) <= acutal_page


def have_right(acutal_page, nbre_pages, nbre):
    """Détermine s'il faut les flèches de droite
    :param acutal_page: index de la page actuelle
    :param nbre_pages: nombre de pages
    :param nbre: nbre de boutons à droite et à gauche de la page actuelle
    :return: True ou False
    """
    return (nbre + acutal_page) < nbre_pages


def get_pagination_buttons(
    acutal_page,
    nbre_pages,
    nbre_boutons=10,
    base_color="#FFFFFF",
    position_color="blue",
    icon_left='<i class="angle double left icon"></i>',
    icon_right='<i class="angle double right icon"></i>',
):
    """Fonction qui va générer le html des boutons de pagination
    :param acutal_page: page actuelle du paginator
    :param nbre_pages: nombre de pages totales dans le paginator
    :param nbre_boutons: nombre de boutons souhaités
    :param base_color: couleur des boutons de changement de page de base
    :param position_color: couleur des boutons de changement de page de la page affichée
    :param icon_left: icone vers la gauche
    :param icon_right: icone vers la droite
    :return: les balises html à envoyer au template
    """
    if nbre_pages == 1:
        return ""

    real_nbre_butons = nbre_boutons + 1 if nbre_boutons % 2 == 0 else nbre_boutons
    nbre = int((real_nbre_butons - 1) / 2)
    balises = (
        get_button(
            acutal_page, 1, base_color=base_color, position_color=position_color, texte=icon_left
        )
        if have_left(acutal_page, nbre) and nbre_pages > nbre_boutons
        else ""
    )
    balises += get_buttons(
        acutal_page,
        nbre_pages,
        real_nbre_butons,
        nbre,
        base_color=base_color,
        position_color=position_color,
    )
    balises += (
        get_button(
            acutal_page,
            nbre_pages,
            base_color=base_color,
            position_color=position_color,
            texte=icon_right,
        )
        if have_right(acutal_page, nbre_pages, nbre) and nbre_pages > nbre_boutons
        else ""
    )
    return balises
