"""Routes URL de l'application users."""

from django.urls import path

from apps.users.views import (
    # change_user_password,
    InsertStaffs,
    InsertUsers,
    affichage_groupes,
    change_email_view,
    delete_staffs_upload_file,
    delete_users_upload_file,
    groups_access_staff,
    login_view,
    logout_view,
    modification_groupes,
    profil_view,
    register_view,
    staff_integrations,
    update_user_groupes,
    users_integrations,
)

urlpatterns = [
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("register/", register_view, name="register"),
    path("profil/", profil_view, name="user_profil"),
    path("change_email/", change_email_view, name="change_email"),
    path("update-user-groupes/", update_user_groupes, name="update_user_groupes"),
    path("modification-groupes/", modification_groupes, name="modification_groupes"),
    path("affichage-groupes/", affichage_groupes, name="affichage_groupes"),
    # Gestion des admin délégués
    path("staff-insertions/", InsertStaffs.as_view(), name="staff_insertions"),
    path(
        "delete-staffs-upload-file/<int:pk>/",
        delete_staffs_upload_file,
        name="delete_staffs_upload_file",
    ),
    path("staff-integrations/", staff_integrations, name="staff_integrations"),
    path("group-access-staff/", groups_access_staff, name="groups_access_staff"),
    # Gestion des utilisateurs
    path(r"users-insertions/", InsertUsers.as_view(), name="users_insertions"),
    path(r"users-integrations/", users_integrations, name="users_integrations"),
    path(
        r"delete_users_upload_file/<int:pk>/",
        delete_users_upload_file,
        name="delete_users_upload_file",
    ),
]
