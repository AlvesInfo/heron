import json
from datetime import datetime as dt
from pathlib import Path

from django.views.generic.edit import FormView
from django.db import transaction, connection
from django.db.utils import IntegrityError
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, HttpResponse, get_object_or_404
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from django.contrib import messages
from django.contrib.auth.models import Group
from django.contrib.sessions.models import Session
from django.utils.decorators import method_decorator


from heron import settings
from apps.users.models import User, UserSession, AuthGroupName, UploadUserFile, AuthGroupAccessStaff
from apps.users.forms.forms_django.forms import (
    UserLoginForm,
    UserRegisterForm,
    UpdateProfilForm,
    UpdateGroupesForm,
    all_users_choices,
    ChangePasswordForm,
    InsertStaffsForm,
    UploadStaffsForm,
    GroupAccessStaffForm,
    ChangeEmailForm,
)
from apps.users.bin.insert_staffs import set_insert_staffs
from apps.users.bin.file_insert_users import set_insert_users
from apps.users.Exceptions import UsersError
from apps.core.functions.functions_logs import LOG_FILE, write_log, envoi_mail_erreur
from apps.core.functions.functions_sql import clean_id
from apps.core.functions.functions_utilitaires import get_client_ip
from apps.core.functions.functions_http import check_next_page
from heron.loggers import LOGGER_CONNEXION


def clean_session(user_session):
    """Fonction de nettoyage des sessions précédentes pour l'utilisateur
    :param user_session: Instance de UserSession(user, session)
    :return: None
    """
    sessions = [
        session.session.pk
        for session in UserSession.objects.filter(user=user_session.user)
        if session != user_session
    ]

    Session.objects.filter(session_key__in=sessions).delete()


@csrf_protect
def login_view(request):
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
            try:
                # Suppression des sessions précédentes,
                # afin qu'il n'y ait pas plusieurs connexions en même temps pour un utilisateur
                user_session, _ = UserSession.objects.get_or_create(
                    user=user, session_id=request.session.session_key
                )
                clean_session(user_session)
            except IntegrityError:
                # première connection
                pass

            LOGGER_CONNEXION.info(
                f"Connexion réussie : mail : {user.email} - "
                f"nom: {user.last_name} - "
                f"prénom : {user.first_name} - "
                f"ip : {get_client_ip(request)}"
            )

            return redirect(next_page)

        messages.warning(request, "Email ou mot de passe, non trouvés")
        LOGGER_CONNEXION.warning(
            f"Connexion ratée : mail : {email} - " f"ip : {get_client_ip(request)}"
        )

    if form.errors:
        LOGGER_CONNEXION.exception(
            f"Formulaire Invalide : {form.errors} - " f"ip : {get_client_ip(request)}"
        )

    return render(request, "users/login_form.html", context)


@csrf_protect
@login_required
def register_view(request):

    form = UserRegisterForm(request.user, request.POST or None)
    super_user = request.user.is_superuser
    staf_user = request.user.is_staff
    context = {"title": "Creation Utilisateur", "form": form, "superuser": super_user}

    if (staf_user or super_user) and form.is_valid():
        user_id = request.user
        first_name = form.cleaned_data.get("first_name")
        last_name = form.cleaned_data.get("last_name")
        email = form.cleaned_data.get("email")
        username = form.cleaned_data.get("username", email.split("@")[0]) or email.split("@")[0]
        fonction = form.cleaned_data.get("fonction")
        superuser = form.cleaned_data.get("superuser")
        staff = form.cleaned_data.get("staff")
        password = form.cleaned_data.get("password")
        groupes = form.cleaned_data.get("groups") or []
        user = User.objects.create_user(
            username, email, password, first_name=first_name, last_name=last_name, fonction=fonction
        )
        user.is_staff = False
        user.is_superuser = False
        # Correction du 11/10/2022, car un STAFF, pouvait créer un STAFF et un Superuser
        if super_user:
            user.is_staff = superuser or staff
            user.is_superuser = superuser

        user.save()

        # Pour chacun des groupes on va créer l'entrée
        for group_name in groupes:
            group = Group.objects.get(name=group_name)
            group.user_set.add(user)

        ratachement_groupes = (
            f"ratachés aux groupes : {', '.join(groupes)}"
            if len(groupes) > 1
            else f"rataché au groupe : {', '.join(groupes)}"
        )

        LOGGER_CONNEXION.info(
            f"Le super User : {user_id.id}, "
            f"a créer l'utilisateur : "
            f"mail : {user.email} - "
            f"nom: {user.last_name} - "
            f"prénom : {user.first_name} - "
            f"ip : {get_client_ip(request)} -"
            f"{ratachement_groupes}"
        )

        next_page = request.GET.get("next")

        if next_page:
            return redirect(next_page)

        form = UserRegisterForm(user_id)
        context["form"] = form
        context["message_success"] = True
        return render(request, "users/creation_form.html", context)

    elif not form.is_valid():
        return render(request, "users/creation_form.html", context)

    return redirect("/")


def logout_view(request):
    user = request.user
    LOGGER_CONNEXION.info(
        f"Déconnexion : mail : {user.email} - "
        f"nom: {user.last_name} - "
        f"prénom : {user.first_name} - "
        f"ip : {get_client_ip(request)}"
    )
    logout(request)
    return redirect("/")


@csrf_protect
@login_required
def profil_view(request):
    user_id = request.user
    form = UpdateProfilForm(user_id, request.POST or None)
    context = {"title": "Votre Compte", "form": form}

    if form.is_valid():
        user = User.objects.get(pk=user_id.id)
        user.first_name = form.cleaned_data.get("first_name") or user.first_name
        user.last_name = form.cleaned_data.get("last_name") or user.last_name
        user.fonction = form.cleaned_data.get("fonction") or user.fonction
        email = user.email
        user.username = form.cleaned_data.get("username") or email.split("@")[0]
        user.save()

        password = form.cleaned_data.get("password")
        password_verif = form.cleaned_data.get("password_verif")

        if password and password_verif and password == password_verif:
            user.password = password
            user.set_password(password)
            user.save()

            user = authenticate(request=request, email=email, password=password)
            login(request, user)
            LOGGER_CONNEXION.info(
                f"Changement de profil ou mot de passe : mail : {user_id.email} - "
                f"nom: {user_id.last_name} - "
                f"prénom : {user_id.first_name} - "
                f"ip : {get_client_ip(request)}"
            )
            context["message"] = "Votre profil et votre mot passe ont bien été changés"

        elif password and password_verif:
            LOGGER_CONNEXION.info(
                f"Changement de profil ou mot de passe : mail : {user_id.email} - "
                f"nom: {user_id.last_name} - "
                f"prénom : {user_id.first_name} - "
                f"ip : {get_client_ip(request)} - "
                f"Echec car les deux mots de passes sont différents"
            )
            context["message"] = "les deux mots de passes doivent être identiques"
        else:
            LOGGER_CONNEXION.info(
                f"Changement de profil : mail : {user_id.email} - "
                f"nom: {user_id.last_name} - "
                f"prénom : {user_id.first_name} - "
                f"ip : {get_client_ip(request)}"
            )
            context["message"] = "Votre profil à bien été changé"

    else:
        LOGGER_CONNEXION.info(
            f"Changement de profil ou mot de passe : mail : {user_id.email} - "
            f"nom: {user_id.last_name} - "
            f"prénom : {user_id.first_name} - "
            f"ip : {get_client_ip(request)} - "
            f"Echec : Les deux mots de passe ne sont pas identiques"
        )

    return render(request, "users/user_profil.html", context)


@csrf_protect
@login_required
def update_user_groupes(request):
    user = User.objects.get_object_or_404(pk=request.user.id)

    if user.is_staff:

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
                first_user = users[0]
                initial_user, name, user_to_form = first_user

                form = UpdateGroupesForm(user, user_to_form)
                context = {
                    "title": "Gestion des Groupes Utilisateurs",
                    "users": users,
                    "initial": (initial_user, name),
                    "initial_user": initial_user,
                    "form": form,
                }
            else:
                context = {"not_users": True}

        return render(request, "users/gestion_users_form.html", context)

    return redirect("/")


@csrf_exempt
@login_required
def modification_groupes(request):
    dic = {"success": "ko"}

    if request.is_ajax() and request.POST.get("pk") != "None":
        try:
            user_pk = json.loads(request.POST["pk"])
            list_groupes = request.POST.getlist("groups[]")
            cursor = connection.cursor()

            with transaction.atomic():
                sql_delete = f"delete from auth_user_groups WHERE user_id = %s;"
                cursor.execute(sql_delete, (user_pk,))

                for groupe in list_groupes:
                    Group.objects.get(pk__in=groupe).user_set.add(user_pk)

                groupes = [
                    r["group_name"]
                    for r in AuthGroupName.objects.filter(group_id__in=list_groupes).values(
                        "group_name"
                    )
                ]

                ratachement_groupes = (
                    f"ratachés aux groupes : {', '.join(groupes)}"
                    if len(groupes) > 1
                    else f"rataché au groupe : {', '.join(groupes)}"
                )
                user = get_object_or_404(User, pk=user_pk)

                LOGGER_CONNEXION.info(
                    f"Le super User : {request.user.id}, "
                    f"a modifié les groupes , pour l'utilisateur :"
                    f"mail : {user.email} - "
                    f"nom: {user.last_name} - "
                    f"prénom : {user.first_name} - "
                    f"ip : {get_client_ip(request)} - "
                    f"{ratachement_groupes}"
                )

            dic = {"success": "ok"}

        except UsersError as err:
            log_line = f"{dt.now().isoformat()} | users/views/modification-groupes : {err}\n"
            write_log(LOG_FILE, log_line)
            envoi_mail_erreur(log_line)

    response = JsonResponse(dic)
    return HttpResponse(response)


@csrf_exempt
@login_required
def affichage_groupes(request):

    if request.is_ajax():
        dic = {"success": "ko"}

        try:
            user_pk = json.loads(request.POST["pk"])
            user = User.objects.get(pk=user_pk)
            rows_groupes = [row.id for row in user.in_groups()]
            dic = {"success": rows_groupes}

        except UsersError as err:
            log_line = f"{dt.now().isoformat()} | users/views/affichage-groupes : {err}\n"
            write_log(LOG_FILE, log_line)
            envoi_mail_erreur(log_line)

        response = JsonResponse(dic)

        return HttpResponse(response)

    return redirect("/")


@login_required
def change_user_password(request):
    form = ChangePasswordForm(request.POST or None)
    super_user = request.user.is_staff
    user = request.user
    is_superuser = user.is_superuser

    users, initial_user, initial = all_users_choices(
        user_id=clean_id(user.id), is_superuser=is_superuser
    )
    context = {
        "title": "Gestion Groupes Utilisateurs",
        "users": users,
        "initial_user": initial_user,
        "initial": initial,
        "form": form,
    }

    if super_user and form.is_valid():
        password = form.cleaned_data.get("password")
        password_verif = form.cleaned_data.get("password_verif")
        utilisateur = clean_id(request.POST["utilisateurs"])
        user_change_password = get_object_or_404(User, pk=utilisateur)

        if password == password_verif:

            try:
                user_change_password.set_password(password)
                user_change_password.save()
                context["message_success"] = "Le mot de passe à bien été réinitialisé"
                LOGGER_CONNEXION.info(
                    f"Le super User : {user.id}, "
                    f"a modifié le mot de passe , pour l'utilisateur :"
                    f"mail : {user_change_password.email} - "
                    f"nom: {user_change_password.last_name} - "
                    f"prénom : {user_change_password.first_name} - "
                    f"ip : {get_client_ip(request)} - "
                )

            except UsersError as err:
                LOGGER_CONNEXION.info(
                    f"Le super User : {user.id}, "
                    f"a souhaité modifié le mot de passe , pour l'utilisateur :"
                    f"mail : {user_change_password.email} - "
                    f"et il c'est produit une erreur : {err} - \n"
                    f"ip : {get_client_ip(request)} - "
                )
                context["message_error"] = "Erreur de traitement"

        else:
            LOGGER_CONNEXION.info(
                f"Le super User : {user.id}, "
                f"a souhaité modifié le mot de passe , pour l'utilisateur :"
                f"mail : {user_change_password.email} - "
                f"et les deux mots de passes n'étaient pas identiques - "
                f"ip : {get_client_ip(request)} - "
            )
            users, initial_user, initial = all_users_choices(
                user_id=clean_id(user_change_password.id), is_superuser=is_superuser
            )
            context["message_error"] = "Les deux mots de passe doivent être identiques"
            context["initial_user"] = initial_user
            context["initial"] = initial

        return render(request, "users/change_pass_form.html", context)

    return redirect("/")


@method_decorator(csrf_exempt, name="dispatch")
class InsertStaffs(FormView):
    form_class = InsertStaffsForm
    template_name = "users/import_staffs_user.html"
    messages = []

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        files_upload = UploadUserFile.objects.filter(user=self.request.user)

        context["files_upload"] = files_upload
        context["messages"] = self.messages

        return context

    def post(self, *args, **kwargs):
        form = UploadStaffsForm(self.request.POST, self.request.FILES)
        name = str(self.request.FILES["file"])
        ext = name.split(".")[-1]

        if ext != "csv":
            data = {
                "isValid": False,
                "message": f"Erreur : - Le fichier {name}, n'a pu être téléversé, car ce n'est "
                f"pas un csv !",
            }

        elif form.is_valid():
            try:
                UploadUserFile.objects.get(base_name_file=name)
                data = {
                    "isValid": False,
                    "message": f"Erreur : - Le fichier {name}, a déjà été téléversé !",
                }

            except (UploadUserFile.DoesNotExist, UploadUserFile.MultipleObjectsReturned):
                file = form.save()
                file.base_name_file = name
                file.user = self.request.user
                file.save()

                html_file = f"""
                <tr id="file{file.pk}">
                  <td style="width: 90%;">
                    {file.base_name_file}
                  </td>
                  <td class="tdDelete" style="text-align: center;">
                    <div style="cursor: pointer;">
                      <i class="red trash icon" 
                         onclick="deleteUpload({file.pk}, '{file.base_name_file}')">
                      </i>
                    </div>
                  </td>
                </tr>
                """

                data = {"isValid": True, "htmlFile": html_file}

        else:
            data = {
                "isValid": False,
                "message": f"Erreur : - Le fichier {name}, n'a pu être téléversé !",
            }

        return JsonResponse(data)


@csrf_exempt
def delete_staffs_upload_file(request, pk):
    if not request.is_ajax() or request.method != "POST":
        return redirect("dashboard")

    data = {"success": "ko"}
    pk = clean_id(pk)
    try:
        file_to_delete = UploadUserFile.objects.get(pk=pk)
        file_to_delete.delete()
        delete = Path(settings.MEDIA_DIR) / str(file_to_delete.file)

        if delete.is_file():
            delete.unlink()

        data = {"success": "ok"}

    except UploadUserFile.DoesNotExist:
        pass

    return JsonResponse(data)


@csrf_exempt
def staff_integrations(request):
    if request.is_ajax() and request.method == "POST":

        od, html_messages = set_insert_staffs(request.user)
        od = od is not None
        data = {"html": html_messages, "od": od}

        return JsonResponse(data)

    return redirect("dashboard")


@csrf_protect
@login_required
def groups_access_staff(request):
    form = GroupAccessStaffForm(request.POST or None)

    if form.is_valid():
        list_group = form.cleaned_data.get("group")
        AuthGroupAccessStaff.objects.exclude(group_id__in=list_group).delete()

        for group in list_group:
            AuthGroupAccessStaff.objects.get_or_create(group_id=group)

    return render(request, "users/group_access_staff.html", {"form": form})


@method_decorator(csrf_exempt, name="dispatch")
class InsertUsers(FormView):
    form_class = InsertStaffsForm
    template_name = "users/import_users_user.html"
    messages = []

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        files_upload = UploadUserFile.objects.filter(user=self.request.user, type_insert=0)

        context["files_upload"] = files_upload
        context["messages"] = self.messages

        return context

    def post(self, *args, **kwargs):
        form = UploadStaffsForm(self.request.POST, self.request.FILES)
        name = str(self.request.FILES["file"])
        ext = name.split(".")[-1]

        if ext not in {"xls", "xlsx"}:
            data = {
                "isValid": False,
                "message": f"Erreur : - Le fichier {name}, n'a pu être téléversé, car ce n'est "
                f"pas un fichier excel !",
            }

        elif form.is_valid():
            try:
                UploadUserFile.objects.get(base_name_file=name)
                data = {
                    "isValid": False,
                    "message": f"Erreur : - Le fichier {name}, a déjà été téléversé !",
                }

            except (UploadUserFile.DoesNotExist, UploadUserFile.MultipleObjectsReturned):
                file = form.save()
                file.base_name_file = name
                file.user = self.request.user
                file.save()

                html_file = f"""
                <tr id="file{file.pk}">
                  <td style="width: 90%;">
                    {file.base_name_file}
                  </td>
                  <td class="tdDelete" style="text-align: center;">
                    <div style="cursor: pointer;">
                      <i class="red trash icon" 
                         onclick="deleteUpload({file.pk}, '{file.base_name_file}')">
                      </i>
                    </div>
                  </td>
                </tr>
                """

                data = {"isValid": True, "htmlFile": html_file}

        else:
            data = {
                "isValid": False,
                "message": f"Erreur : - Le fichier {name}, n'a pu être téléversé !",
            }

        return JsonResponse(data)


@csrf_exempt
def delete_users_upload_file(request, pk):
    if not request.is_ajax() or request.method != "POST":
        return redirect("dashboard")

    data = {"success": "nop"}
    pk = clean_id(pk)
    try:
        file_to_delete = UploadUserFile.objects.get(pk=pk, type_insert=0)
        file_to_delete.delete()
        delete = Path(settings.MEDIA_DIR) / str(file_to_delete.file)

        if delete.is_file():
            delete.unlink()

        data = {"success": "ok"}

    except UploadUserFile.DoesNotExist:
        pass

    return JsonResponse(data)


@csrf_exempt
def users_integrations(request):
    if request.is_ajax() and request.method == "POST":
        od, html_messages = set_insert_users(request.user, request)

        od = od is not None
        data = {"html": html_messages, "od": od}

        return JsonResponse(data)

    return redirect("dashboard")


@csrf_protect
@login_required
def change_email_view(request):
    level = 20
    form = ChangeEmailForm(request.POST or None)

    if form.is_valid():
        last_email = form.cleaned_data.get("last_email")
        email = form.cleaned_data.get("email")
        email_verif = form.cleaned_data.get("email_verif")
        exist = False
        try:
            User.objects.get(email=email)
            exist = True
        except User.DoesNotExist:
            pass

        if last_email != request.user.email:
            messages.error(
                request,
                "L'ancien email %s , est inconnu" % (last_email,),
                extra_tags="Erreur",
            )
            request.session["level"] = 50

        elif email != email_verif:
            messages.error(
                request,
                "L'email %s et l'email de vérification %s , ne sont pas identiques"
                % (email, email_verif),
                extra_tags="Erreur",
            )
            request.session["level"] = 50
        elif exist:
            messages.error(
                request,
                "L'email %s existe déjà" % (email,),
                extra_tags="Erreur",
            )
            request.session["level"] = 50
        else:
            User.objects.filter(email=last_email).update(email=email)
            logout(request)
            return redirect("logout_email")

    return render(request, "users/change_email.html", {"form": form, "level": level})
