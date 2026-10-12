"""Views de l'app users : connexion, création et profil des utilisateurs, gestion des groupes,.

intégration en masse des Admin délégués (csv) et des utilisateurs (excel).
"""

import json
from typing import Any

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.contrib.sessions.models import Session
from django.db import connection, transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.views.decorators.http import require_http_methods
from django.views.generic.edit import FormView

from apps.core.bin.typing_helpers import current_user
from apps.core.functions.functions_http import check_next_page, is_ajax
from apps.core.functions.functions_logs import LOG_FILE, envoi_mail_erreur, write_log
from apps.core.functions.functions_sql import clean_id
from apps.core.functions.functions_utilitaires import get_client_ip
from apps.users.bin.file_insert_users import set_insert_users
from apps.users.bin.insert_staffs import delete_upload_file, set_insert_staffs
from apps.users.Exceptions import UsersError
from apps.users.forms.forms_django.forms import (
    ChangeEmailForm,
    GroupAccessStaffForm,
    InsertStaffsForm,
    UpdateGroupesForm,
    UpdateProfilForm,
    UploadStaffsForm,
    UserLoginForm,
    UserRegisterForm,
)
from apps.users.models import AuthGroupAccessStaff, AuthGroupName, UploadUserFile, User, UserSession
from heron.loggers import LOGGER_CONNEXION

# Bouton natif sans habillage : seule l'icône corbeille est visible (même style que les gabarits)
DELETE_BUTTON_STYLE = (
    "background: none; border: 0; padding: 0; margin: 0; cursor: pointer; "
    "color: inherit; font: inherit;"
)
STAFF_INSERT = 1
USERS_INSERT = 0


def _user_log(user, request):
    """Partie commune des messages de log de connexion."""
    return (
        f"mail : {user.email} - nom: {user.last_name} - prénom : {user.first_name} - "
        f"ip : {get_client_ip(request)}"
    )


def _groupes_log(groupes):
    """Texte de rattachement aux groupes pour les logs."""
    if len(groupes) > 1:
        return f"ratachés aux groupes : {', '.join(groupes)}"

    return f"rataché au groupe : {', '.join(groupes)}"


def clean_session(user_session):
    """Fonction de nettoyage des sessions précédentes pour l'utilisateur.

    :param user_session: Instance de UserSession(user, session)
    :return: None.
    """
    sessions = [
        session.session.pk
        for session in UserSession.objects.filter(user=user_session.user)
        if session != user_session
    ]
    Session.objects.filter(session_key__in=sessions).delete()


@require_http_methods(["GET", "POST"])
@csrf_protect
def login_view(request):
    """Connexion : une seule session active par utilisateur."""
    next_page = check_next_page(request.GET.get("next"))
    title = "Se Connecter"
    form = UserLoginForm(request.POST or None)
    context = {"form": form, "title": title}

    if form.is_valid():
        email = form.cleaned_data.get("email")
        password = form.cleaned_data.get("mot_de_passe")
        user = authenticate(request=request, email=email, password=password)

        if user:
            login(request, user, backend="django.contrib.auth.backends.ModelBackend")
            # Suppression des sessions précédentes,
            # afin qu'il n'y ait pas plusieurs connexions en même temps pour un utilisateur
            user_session, _ = UserSession.objects.get_or_create(
                user=user, session_id=request.session.session_key
            )
            clean_session(user_session)
            LOGGER_CONNEXION.info("Connexion réussie : %s", _user_log(user, request))
            return redirect(next_page)

        messages.warning(request, "Email ou mot de passe, non trouvés")
        LOGGER_CONNEXION.warning(
            "Connexion ratée : mail : %s - ip : %s", email, get_client_ip(request)
        )

    if form.errors:
        LOGGER_CONNEXION.error(
            "Formulaire Invalide : %s - ip : %s", form.errors, get_client_ip(request)
        )

    return render(request, "users/login_form.html", context)


def _create_registered_user(form, super_user):
    """Création de l'utilisateur à partir du formulaire validé, avec rattachement à ses groupes.

    :param form: UserRegisterForm validé
    :param super_user: True si l'utilisateur créateur est superuser
    :return: l'utilisateur créé et la liste des groupes rattachés.
    """
    cleaned_data = form.cleaned_data
    email = cleaned_data.get("email")
    username = cleaned_data.get("username") or email.split("@")[0]
    user = User.objects.create_user(
        username,
        email,
        cleaned_data.get("password"),
        first_name=cleaned_data.get("first_name"),
        last_name=cleaned_data.get("last_name"),
        function=cleaned_data.get("fonction"),
        code_child_center=form.user.code_child_center,
    )
    user.is_staff = False
    user.is_superuser = False

    # Correction du 11/10/2022, car un STAFF, pouvait créer un STAFF et un Superuser
    if super_user:
        user.is_staff = cleaned_data.get("superuser") or cleaned_data.get("staff")
        user.is_superuser = cleaned_data.get("superuser")

    user.save()
    groupes = cleaned_data.get("groups") or []

    for group_name in groupes:
        Group.objects.get(name=group_name).user_set.add(user)

    return user, groupes


@require_http_methods(["GET", "POST"])
@csrf_protect
@login_required
def register_view(request):
    """Création d'un utilisateur par un superuser ou un staff (restreint à ses groupes)."""
    form = UserRegisterForm(request.user, request.POST or None)
    super_user = request.user.is_superuser
    staf_user = request.user.is_staff
    context = {"title": "Creation Utilisateur", "form": form, "superuser": super_user}

    if (staf_user or super_user) and form.is_valid():
        user, groupes = _create_registered_user(form, super_user)
        LOGGER_CONNEXION.info(
            "Le super User : %s, a créer l'utilisateur : %s -%s",
            request.user.id,
            _user_log(user, request),
            _groupes_log(groupes),
        )
        next_page = request.GET.get("next")

        if next_page:
            # Même contrôle qu'à la connexion : pas de redirection vers un domaine étranger
            return redirect(check_next_page(next_page))

        context["form"] = UserRegisterForm(request.user)
        context["message_success"] = True
        return render(request, "users/creation_form.html", context)

    if not form.is_valid():
        return render(request, "users/creation_form.html", context)

    return redirect("/")


@require_http_methods(["GET"])
def logout_view(request):
    """Déconnexion."""
    LOGGER_CONNEXION.info("Déconnexion : %s", _user_log(request.user, request))
    logout(request)
    return redirect("/")


@require_http_methods(["GET", "POST"])
@csrf_protect
@login_required
def profil_view(request):
    """Modification de son profil et de son mot de passe."""
    user_id = request.user
    form = UpdateProfilForm(user_id, request.POST or None)
    context = {"title": "Votre Compte", "form": form}

    if form.is_valid():
        user = User.objects.get(pk=user_id.id)
        user.first_name = form.cleaned_data.get("first_name") or user.first_name
        user.last_name = form.cleaned_data.get("last_name") or user.last_name
        user.function = form.cleaned_data.get("fonction") or user.function
        email = user.email
        user.username = form.cleaned_data.get("username") or email.split("@")[0]
        user.save()
        password = form.cleaned_data.get("password")

        # Le formulaire garantit que les deux mots de passe sont identiques s'il y en a un
        if password:
            user.set_password(password)
            user.save()
            auth_user = authenticate(request=request, email=email, password=password)
            login(request, auth_user)
            LOGGER_CONNEXION.info(
                "Changement de profil ou mot de passe : %s", _user_log(user_id, request)
            )
            context["message"] = "Votre profil et votre mot passe ont bien été changés"
        else:
            LOGGER_CONNEXION.info("Changement de profil : %s", _user_log(user_id, request))
            context["message"] = "Votre profil à bien été changé"

    elif form.errors:
        LOGGER_CONNEXION.info(
            "Changement de profil ou mot de passe : %s - Echec : Les deux mots de passe ne sont pas identiques",
            _user_log(user_id, request),
        )

    return render(request, "users/user_profil.html", context)


@require_http_methods(["GET", "POST"])
@csrf_protect
@login_required
def update_user_groupes(request):
    """Ecran de gestion des groupes des utilisateurs subordonnés (staff et superuser)."""
    user = get_object_or_404(User, pk=request.user.id)

    if not user.is_staff:
        return redirect("/")

    context: dict[str, Any]

    if not user.in_groups() and not user.is_superuser:
        context = {"not_in_groups": True}
    elif not user.get_subordonates() and not user.is_superuser:
        context = {"subordinate": True}
    else:
        users = [
            (users_user.pk, users_user.get_full_name(), users_user)
            for users_user in user.get_subordonates()
        ]

        if users:
            initial_user, name, user_to_form = users[0]
            context = {
                "title": "Gestion des Groupes Utilisateurs",
                "users": users,
                "initial": (initial_user, name),
                "initial_user": initial_user,
                "form": UpdateGroupesForm(user, user_to_form),
            }
        else:
            context = {"not_users": True}

    return render(request, "users/gestion_users_form.html", context)


def _log_users_error(view_name, err):
    """Trace fichier + mail des erreurs des vues ajax de gestion des groupes."""
    log_line = f"{timezone.localtime().isoformat()} | users/views/{view_name} : {err}\n"
    write_log(LOG_FILE, log_line)
    envoi_mail_erreur(log_line)


@require_http_methods(["POST"])
@csrf_protect
@login_required
def modification_groupes(request):
    """Remplacement (ajax) des groupes d'un utilisateur par ceux cochés."""
    dic: dict = {"success": "ko"}

    if is_ajax(request) and request.POST.get("pk") != "None":
        try:
            user_pk = json.loads(request.POST["pk"])
            list_groupes = request.POST.getlist("groups[]")

            with transaction.atomic(), connection.cursor() as cursor:
                cursor.execute("delete from auth_user_groups WHERE user_id = %s;", (user_pk,))

                for groupe in list_groupes:
                    Group.objects.get(pk=groupe).user_set.add(user_pk)

                groupes = list(
                    AuthGroupName.objects.filter(group_id__in=list_groupes).values_list(
                        "group_name", flat=True
                    )
                )
                user = get_object_or_404(User, pk=user_pk)
                LOGGER_CONNEXION.info(
                    "Le super User : %s, a modifié les groupes , pour l'utilisateur :%s - %s",
                    request.user.id,
                    _user_log(user, request),
                    _groupes_log(groupes),
                )

            dic = {"success": "ok"}

        except (UsersError, Group.DoesNotExist, ValueError) as err:
            _log_users_error("modification-groupes", err)

    return JsonResponse(dic)


@require_http_methods(["POST"])
@csrf_protect
@login_required
def affichage_groupes(request):
    """Renvoi (ajax) des identifiants des groupes d'un utilisateur."""
    if not is_ajax(request):
        return redirect("/")

    dic: dict = {"success": "ko"}

    try:
        user = User.objects.get(pk=json.loads(request.POST["pk"]))
        dic = {"success": [row.id for row in user.in_groups()]}
    except (UsersError, User.DoesNotExist, ValueError) as err:
        _log_users_error("affichage-groupes", err)

    return JsonResponse(dic)


def _upload_file(request, allowed_extensions, type_insert, file_label):
    """Téléversement (ajax) d'un fichier d'intégration d'utilisateurs.

    :param request: request Django (POST + FILES)
    :param allowed_extensions: extensions acceptées
    :param type_insert: 0 utilisateurs, 1 staff
    :param file_label: libellé du type de fichier attendu dans le message d'erreur
    :return: dictionnaire JSON pour le JavaScript de la page.
    """
    form = UploadStaffsForm(request.POST, request.FILES)
    upload = request.FILES.get("file")
    name = str(upload) if upload else ""

    if name.split(".")[-1] not in allowed_extensions:
        return {
            "isValid": False,
            "message": f"Erreur : - Le fichier {name}, n'a pu être téléversé, car ce n'est "
            f"pas {file_label} !",
        }

    if not form.is_valid():
        return {
            "isValid": False,
            "message": f"Erreur : - Le fichier {name}, n'a pu être téléversé !",
        }

    if UploadUserFile.objects.filter(base_name_file=name).exists():
        return {
            "isValid": False,
            "message": f"Erreur : - Le fichier {name}, a déjà été téléversé !",
        }

    file = form.save(commit=False)
    file.base_name_file = name
    file.user = request.user
    file.type_insert = type_insert
    file.save()
    html_file = f"""
                <tr id="file{file.pk}">
                  <td style="width: 90%;">
                    {file.base_name_file}
                  </td>
                  <td class="tdDelete" style="text-align: center;">
                    <div style="cursor: pointer;">
                      <button type="button" style="{DELETE_BUTTON_STYLE}" aria-label="Supprimer"
                         onclick="deleteUpload({file.pk}, '{file.base_name_file}')"><i
                         class="red trash icon" aria-hidden="true"></i></button>
                    </div>
                  </td>
                </tr>
                """
    return {"isValid": True, "htmlFile": html_file}


def _delete_upload(pk, type_insert):
    """Suppression (ajax) d'un fichier téléversé de l'utilisateur."""
    data = {"success": "ko"}

    try:
        file_to_delete = UploadUserFile.objects.get(pk=clean_id(pk), type_insert=type_insert)
        delete_upload_file(file_to_delete)
        data = {"success": "ok"}
    except UploadUserFile.DoesNotExist:
        pass

    return JsonResponse(data)


@method_decorator(csrf_exempt, name="dispatch")
class InsertStaffs(FormView):
    """Ecran de téléversement des fichiers csv d'Admin délégués (staff)."""

    form_class = InsertStaffsForm
    template_name = "users/import_staffs_user.html"

    def get_context_data(self, **kwargs):
        """Ajoute au contexte les fichiers de salariés déjà téléversés."""
        context = super().get_context_data(**kwargs)
        context["files_upload"] = UploadUserFile.objects.filter(
            user=current_user(self.request), type_insert=STAFF_INSERT
        )
        context["messages"] = []
        return context

    def post(self, *_args, **_kwargs):
        """Réceptionne le fichier csv des salariés."""
        return JsonResponse(_upload_file(self.request, {"csv"}, STAFF_INSERT, "un csv"))


@require_http_methods(["POST"])
@csrf_protect
def delete_staffs_upload_file(request, pk):
    """Suppression d'un fichier csv de staff téléversé."""
    if not is_ajax(request):
        return redirect("home")

    return _delete_upload(pk, STAFF_INSERT)


@require_http_methods(["POST"])
@csrf_protect
def staff_integrations(request):
    """Lancement (ajax) de l'intégration des fichiers csv de staff téléversés."""
    if not is_ajax(request):
        return redirect("home")

    od, html_messages = set_insert_staffs(request.user)
    return JsonResponse({"html": html_messages, "od": od is not None})


@require_http_methods(["GET", "POST"])
@csrf_protect
@login_required
def groups_access_staff(request):
    """Choix des groupes auxquels les Admin délégués (staff) ont accès."""
    form = GroupAccessStaffForm(request.POST or None)

    if form.is_valid():
        list_group = form.cleaned_data["group"]
        AuthGroupAccessStaff.objects.exclude(group_id__in=list_group).delete()

        for group in list_group:
            AuthGroupAccessStaff.objects.get_or_create(group_id=group)

    return render(request, "users/group_access_staff.html", {"form": form})


@method_decorator(csrf_exempt, name="dispatch")
class InsertUsers(FormView):
    """Ecran de téléversement des fichiers excel d'utilisateurs."""

    form_class = InsertStaffsForm
    template_name = "users/import_users_user.html"

    def get_context_data(self, **kwargs):
        """Ajoute au contexte les fichiers d'utilisateurs déjà téléversés."""
        context = super().get_context_data(**kwargs)
        context["files_upload"] = UploadUserFile.objects.filter(
            user=current_user(self.request), type_insert=USERS_INSERT
        )
        context["messages"] = []
        return context

    def post(self, *_args, **_kwargs):
        """Réceptionne le fichier Excel des utilisateurs."""
        return JsonResponse(
            _upload_file(self.request, {"xls", "xlsx"}, USERS_INSERT, "un fichier excel")
        )


@require_http_methods(["POST"])
@csrf_protect
def delete_users_upload_file(request, pk):
    """Suppression d'un fichier excel d'utilisateurs téléversé."""
    if not is_ajax(request):
        return redirect("home")

    return _delete_upload(pk, USERS_INSERT)


@require_http_methods(["POST"])
@csrf_protect
def users_integrations(request):
    """Lancement (ajax) de l'intégration des fichiers excel d'utilisateurs téléversés."""
    if not is_ajax(request):
        return redirect("home")

    od, html_messages = set_insert_users(request.user, request)
    return JsonResponse({"html": html_messages, "od": od is not None})


@require_http_methods(["GET", "POST"])
@csrf_protect
@login_required
def change_email_view(request):
    """Changement de son adresse email, puis déconnexion."""
    level = 20
    form = ChangeEmailForm(request.POST or None)

    if form.is_valid():
        last_email = form.cleaned_data.get("last_email")
        email = form.cleaned_data.get("email")
        email_verif = form.cleaned_data.get("email_verif")

        if last_email != request.user.email:
            messages.error(
                request, f"L'ancien email {last_email} , est inconnu", extra_tags="Erreur"
            )
            request.session["level"] = 50
        elif email != email_verif:
            messages.error(
                request,
                f"L'email {email} et l'email de vérification {email_verif} , "
                "ne sont pas identiques",
                extra_tags="Erreur",
            )
            request.session["level"] = 50
        elif User.objects.filter(email=email).exists():
            messages.error(request, f"L'email {email} existe déjà", extra_tags="Erreur")
            request.session["level"] = 50
        else:
            User.objects.filter(email=last_email).update(email=email)
            logout(request)
            return redirect("logout_email")

    return render(request, "users/change_email.html", {"form": form, "level": level})
