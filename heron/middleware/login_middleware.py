# pylint: disable=E0401,R0903
"""
FR : Middlewares de la partie login
EN : Middlewares of the login part

Commentaire:

created at: 2022-05-18
created by: Paulo ALVES

modified at: 2022-05-18
modified by: Paulo ALVES
"""
from django.shortcuts import redirect


class LoginMiddleware:
    """
    Restriction d'acces au site, en fonction du login et d'appartenance à un groupe.
    SuperUser   :   - Acces Total
    Staff       :   - Acces à ses groupes
                    - Création d'utlisateurs, restreints à ces propres groupes
    User        :   - Acces à ses groupes
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        """
        Si l'on n'est pas authentifié, on est renvoyé sur la page de login
        :param request: request django
        :return: Redirige vers la page de login si non connecté.
        """
        list_path = str(request.path).split("/")
        # on vérifie password-reset-confirm dans request.path pour les reset des passwords
        is_confirm = list_path[1] == "password-reset-confirm"

        # on vérifie reactivate dans request.path pour les reset des passwords
        if len(list_path) >= 2 and f"{list_path[1]}" == "reactivate":
            is_confirm = True

        # Si l'on est pas authentifié, on est renvoyé sur la page de login
        paths = [
            "/logout_email/",
            "/password-reset/",
            "/password-reset-done/",
            "/password-reset-complete/",
            "/accounts/login/",
            str(request.path) if is_confirm else "",
        ]

        if not request.user.is_authenticated:
            if request.path not in paths:
                return redirect("accounts:login")

        # Avant changements
        # if not request.user.is_authenticated and request.path != '/accounts/login/':
        #     return redirect("accounts:login")

        response = self.get_response(request)

        return response
