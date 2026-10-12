"""Module pour utilitaires sql."""


def clean_id(p_k):
    """Fonction qui renvoie 0, si le pk reçu n'est pas convertible en int (texte, None, ...).

    :param p_k: int
    :return: p_k ou 0.
    """
    try:
        return int(p_k)

    except (TypeError, ValueError):
        return 0
