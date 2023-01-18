def get_request_formset(request_dict: dict, base_data_dict: dict):
    """Assemblage des formset avec des données de base inline
    :param request_dict: dictionnaire de la requete post django
    :param base_data_dict: dictionnaire des éléments de base du formset
    :return: dict avec les données retraitées
    """
    formset_dict = {
        **{"csrfmiddlewaretoken": request_dict.pop("csrfmiddlewaretoken")},
        **{key: value for key, value in request_dict.items() if key[:4] == "form"},
    }
    total_forms = int(request_dict.get("form-TOTAL_FORMS", "1"))

    for i in range(total_forms):
        formset_dict.update({f"form-{i}-{key}": value for key, value in base_data_dict.items()})

    return formset_dict


def get_request_formset_to_form(request_dict: dict, base_data_dict: dict):
    """Assemblage des formset avec des données de base inline
    :param request_dict: dictionnaire de la requete post django
    :param base_data_dict: dictionnaire des éléments de base du formset
    :return: dict avec les données retraitées
    """
    csrfmiddlewaretoken = request_dict.pop("csrfmiddlewaretoken")
    formset_dict = {key: value for key, value in request_dict.items() if key[:4] == "form"}
    total_forms = int(request_dict.get("form-TOTAL_FORMS", "1"))

    for i in range(total_forms):
        formset_dict.update({f"form-{i}-{key}": value for key, value in base_data_dict.items()})

    results_dict = {}
    for j in range(total_forms):
        results_dict.update({j: {}})
        for key, value in formset_dict.items():
            if str(key).startswith(f"form-{j}-"):
                results_dict[j].update({key.replace(f"form-{j}-", ""): value})

    print(results_dict)
    return results_dict


def get_sens(sens: str):
    """Retourne le sens de facturation AC, AC/VE, VE"""
    if sens == "2":
        return {"purchase_invoice": "on", "sale_invoice": "on"}

    if sens == "1":
        return {"purchase_invoice": "off", "sale_invoice": "on"}

    return {"purchase_invoice": "on", "sale_invoice": "off"}
