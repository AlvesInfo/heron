from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.views import static
from django.conf import settings


@login_required()
def serve_secure_static(request, path):
    if settings.DEBUG:
        return static.serve(request, path, settings.MEDIA_ROOT)

    # Sinon on retourne une réponse VIDE avec en header le chemin de l'url
    # de l'upload interne
    # Nginx va l'intercepter, réaliser qu'il faut qu'il upload ce qu'il y
    # a à cette URL et faire le reste du boulot
    response = HttpResponse()
    response['X-Accel-Redirect'] = '/files/%s' % path
    return response
