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
        :return: Redirige vers la page de login si non connecté
        """

        if not request.user.is_authenticated():
            return redirect("accounts:login")

        response = self.get_response(request)

        return response
