def get_request_formset(request_dict: dict, base_data_dict: dict):
    """Assemblage des formsetd avec des données de base inline
    :param request_dict: dictionnaire de la requete post django
    :param base_data_dict: dictionnaire des éléments de base du formset
    :return: dict avec les données retraitées
    """
    formset_dict = {"csrfmiddlewaretoken": request_dict.get("csrfmiddlewaretoken")}
    total_forms = int(request_dict.get("form-TOTAL_FORMS", "1"))

    for i in range(total_forms):
        formset_dict.update(
            {
                **{f"form-{i}-{key}": value for key, value in base_data_dict.items()},
                **{
                    key: value
                    for key, value in request_dict.items()
                    if key[:4] == "form"
                },
            }
        )


    return formset_dict
