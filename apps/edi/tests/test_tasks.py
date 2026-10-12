"""Tests des tâches celery de l'app edi (apps/edi/tasks.py), appelées directement.

created at: 2026-10-10
created by: Paulo ALVES
"""

from pathlib import Path

import pytest

from apps.core.models import SSEProgress
from apps.edi import tasks
from conftest import patched_attrs


class BrokenProgress:
    """Faux modèle SSEProgress dont la recherche échoue d'une erreur inattendue"""

    DoesNotExist = SSEProgress.DoesNotExist

    class Objects:  # pylint: disable=R0903
        """Manager factice"""

        @staticmethod
        def select_for_update():
            raise RuntimeError("verrou impossible")

        @staticmethod
        def create(**_kwargs):
            raise RuntimeError("création impossible")

    objects = Objects


@pytest.fixture
def no_sleep(monkeypatch):
    with patched_attrs(monkeypatch, tasks.time, sleep=lambda _seconds: None):
        yield


@pytest.fixture
def import_file(edi_dirs):
    """Fichier à importer dans WIDEX et son chemin de backup"""
    file = edi_dirs.processing / "WIDEX" / "facture.csv"
    file.write_text("a;b\n", encoding="utf8")
    return file, edi_dirs.backup / "WIDEX" / "facture.csv"


def fake_import(trace, to_print="Import : Widex\n"):
    """Fonction d'import factice renvoyant la trace donnée"""

    def _import(*_args, **_kwargs):
        return trace, to_print

    return _import


# IMPORT DES FICHIERS FOURNISSEURS =================================================================


def test_launch_suppliers_import(
    import_file, make_trace, make_user, make_sse_progress, monkeypatch
):
    """Succès : trace rattachée à l'utilisateur, fichier déplacé en backup, jauge avancée"""
    file, backup = import_file
    user = make_user()
    trace = make_trace(flow_name="Widex", comment="")
    progress = make_sse_progress(user=user, total_items=1)

    with patched_attrs(monkeypatch, tasks, processing_dict={"WIDEX": fake_import(trace)}):
        result = tasks.launch_suppliers_import(
            (str(file), str(backup), "WIDEX"), user.pk, progress.job_id
        )

    assert "edi - WIDEX" in result["import : "]
    trace.refresh_from_db()
    assert trace.created_by == user
    assert trace.invoices is True
    assert trace.errors is False
    assert not file.exists()
    assert backup.exists()
    progress.refresh_from_db()
    assert progress.processed_items == 1
    assert progress.failed_items == 0
    assert "traité avec succès" in progress.current_message


def test_launch_suppliers_import_backup_deja_present(
    import_file, make_trace, make_user, monkeypatch
):
    """Le backup existe déjà : le fichier traité est simplement supprimé"""
    file, backup = import_file
    backup.write_text("ancien", encoding="utf8")
    trace = make_trace()

    with patched_attrs(monkeypatch, tasks, processing_dict={"WIDEX": fake_import(trace)}):
        tasks.launch_suppliers_import((str(file), str(backup), "WIDEX"), make_user().pk, None)

    assert not file.exists()
    assert backup.read_text(encoding="utf8") == "ancien"


@pytest.mark.usefixtures("make_user")
def test_launch_suppliers_import_trace_en_erreur(
    import_file, make_trace, make_sse_progress, monkeypatch
):
    """La fonction d'import a signalé des erreurs dans la trace : la jauge compte un échec"""
    file, backup = import_file
    trace = make_trace(errors=True)
    progress = make_sse_progress()

    with patched_attrs(monkeypatch, tasks, processing_dict={"WIDEX": fake_import(trace)}):
        tasks.launch_suppliers_import(
            (str(file), str(backup), "WIDEX"), progress.user_id, progress.job_id
        )

    progress.refresh_from_db()
    assert progress.failed_items == 1
    assert "Erreur sur facture.csv" in progress.current_message


def test_launch_suppliers_import_flux_inconnu(import_file, make_sse_progress, caplog):
    """Clé de traitement inconnue : erreur explicite journalisée, le fichier n'est pas perdu"""
    file, backup = import_file
    progress = make_sse_progress()

    result = tasks.launch_suppliers_import(
        (str(file), str(backup), "INCONNU"), progress.user_id, progress.job_id
    )

    assert "Flux inconnu 'INCONNU'" in caplog.text
    assert "TypeError" not in caplog.text
    assert "edi - INCONNU" in result["import : "]
    assert backup.exists()
    progress.refresh_from_db()
    assert progress.failed_items == 1


def test_launch_suppliers_import_type_error(import_file, make_user, monkeypatch, caplog):
    """TypeError levée par la fonction d'import : journalisée comme telle, fichier archivé"""
    file, backup = import_file

    def _boom(_file):
        raise TypeError("colonnes manquantes")

    with patched_attrs(monkeypatch, tasks, processing_dict={"WIDEX": _boom}):
        tasks.launch_suppliers_import((str(file), str(backup), "WIDEX"), make_user().pk, None)

    assert "TypeError" in caplog.text
    assert backup.exists()


def test_launch_suppliers_import_exception_generale(import_file, make_user, monkeypatch, caplog):
    file, backup = import_file

    def _boom(_file):
        raise RuntimeError("import cassé")

    with patched_attrs(monkeypatch, tasks, processing_dict={"WIDEX": _boom}):
        tasks.launch_suppliers_import((str(file), str(backup), "WIDEX"), make_user().pk, None)

    assert "Exception Générale: facture.csv" in caplog.text


class FakeTrace:
    """Trace factice dont l'affectation de created_by échoue : erreur après récupération de la trace"""

    def __init__(self, comment="Import", time_to_process=1):
        self.comment = comment
        self.time_to_process = time_to_process
        self.errors = False
        self.invoices = False
        self.saved = 0

    @property
    def created_by(self):
        return None

    @created_by.setter
    def created_by(self, _user):
        raise RuntimeError("affectation impossible")

    def save(self):
        self.saved += 1


def test_launch_suppliers_import_erreur_apres_trace(import_file, make_user, monkeypatch, caplog):
    """Erreur une fois la trace récupérée : trace en erreur, commentée et sauvegardée"""
    file, backup = import_file
    trace = FakeTrace(comment="Import ok")

    with patched_attrs(monkeypatch, tasks, processing_dict={"WIDEX": fake_import(trace)}):
        tasks.launch_suppliers_import((str(file), str(backup), "WIDEX"), make_user().pk, None)

    assert trace.errors is True
    assert trace.comment == "Import ok\n. Une erreur c'est produite veuillez consulter les logs"
    assert trace.invoices is True
    assert trace.saved == 1
    assert "Exception Générale" in caplog.text
    assert backup.exists()


def test_launch_suppliers_import_jauge_inconnue(
    import_file, make_trace, make_user, monkeypatch, caplog
):
    file, backup = import_file

    with patched_attrs(monkeypatch, tasks, processing_dict={"WIDEX": fake_import(make_trace())}):
        tasks.launch_suppliers_import(
            (str(file), str(backup), "WIDEX"), make_user().pk, "job-inconnu"
        )

    assert "SSEProgress non trouvé pour job_id: job-inconnu" in caplog.text


def test_launch_suppliers_import_erreur_jauge(
    import_file, make_trace, make_user, monkeypatch, caplog
):
    file, backup = import_file

    with patched_attrs(
        monkeypatch,
        tasks,
        processing_dict={"WIDEX": fake_import(make_trace())},
        SSEProgress=BrokenProgress,
    ):
        tasks.launch_suppliers_import((str(file), str(backup), "WIDEX"), make_user().pk, "job")

    assert "Erreur mise à jour progression" in caplog.text


# IMPORT BBGR DEPUIS LA B.I ========================================================================


def test_launch_bbgr_bi_import(make_trace, make_user, make_sse_progress, monkeypatch):
    user = make_user()
    trace = make_trace(flow_name="BbgrStatment", time_to_process=3)
    progress = make_sse_progress(user=user)

    with patched_attrs(
        monkeypatch,
        tasks,
        bbgr_dict={"bbgr_statment": fake_import(trace, "Import : BbgrStatment\n")},
    ):
        result = tasks.launch_bbgr_bi_import("bbgr_statment", user.pk, progress.job_id)

    assert result == {"import : ": "BBGR BI - bbgr_statment - 3 s"}
    trace.refresh_from_db()
    assert trace.created_by == user
    assert trace.invoices is True
    progress.refresh_from_db()
    assert progress.processed_items == 1
    assert progress.failed_items == 0


def test_launch_bbgr_bi_import_fonction_inconnue(make_sse_progress, caplog):
    """Nom inconnu : erreur explicite, pas de trace, durée calculée localement, jauge en échec"""
    progress = make_sse_progress()

    result = tasks.launch_bbgr_bi_import("inconnu", progress.user_id, progress.job_id)

    assert "Import B.I inconnu 'inconnu'" in caplog.text
    assert "TypeError" not in caplog.text
    assert result["import : "].startswith("BBGR BI - inconnu - ")
    progress.refresh_from_db()
    assert progress.failed_items == 1


def test_launch_bbgr_bi_import_type_error(make_user, monkeypatch, caplog):
    """TypeError levée par l'import B.I : journalisée comme telle"""

    def _import():
        raise TypeError("paramètre manquant")

    with patched_attrs(monkeypatch, tasks, bbgr_dict={"bbgr_monthly": _import}):
        tasks.launch_bbgr_bi_import("bbgr_monthly", make_user().pk, None)

    assert "TypeError" in caplog.text


@pytest.mark.usefixtures("db")
def test_launch_bbgr_bi_import_exception_generale(monkeypatch, caplog):
    """Erreur générale avant toute trace : journalisée, pas de trace à marquer"""

    def _import():
        raise RuntimeError("B.I injoignable")

    with patched_attrs(monkeypatch, tasks, bbgr_dict={"bbgr_monthly": _import}):
        tasks.launch_bbgr_bi_import("bbgr_monthly", 1, None)

    assert "Exception Générale: bbgr_monthly" in caplog.text


def test_launch_bbgr_bi_import_erreur_apres_trace(make_user, monkeypatch):
    """Erreur une fois la trace récupérée : trace en erreur et commentée"""
    trace = FakeTrace(comment="Import")

    with patched_attrs(monkeypatch, tasks, bbgr_dict={"bbgr_retours": fake_import(trace)}):
        result = tasks.launch_bbgr_bi_import("bbgr_retours", make_user().pk, None)

    assert trace.errors is True
    assert trace.comment == "Import\n. Une erreur c'est produite veuillez consulter les logs"
    assert result == {"import : ": "BBGR BI - bbgr_retours - 1 s"}


def test_launch_bbgr_bi_import_jauge_inconnue_et_erreur_jauge(
    make_trace, make_user, monkeypatch, caplog
):
    trace = make_trace(time_to_process=1)
    user = make_user()

    with patched_attrs(monkeypatch, tasks, bbgr_dict={"bbgr_receptions": fake_import(trace)}):
        tasks.launch_bbgr_bi_import("bbgr_receptions", user.pk, "job-inconnu")

        with patched_attrs(monkeypatch, tasks, SSEProgress=BrokenProgress):
            tasks.launch_bbgr_bi_import("bbgr_receptions", user.pk, "job")

    assert "SSEProgress non trouvé pour job_id: job-inconnu" in caplog.text
    assert "Erreur mise à jour progression" in caplog.text


# NETTOYAGE SQL GÉNÉRAL ============================================================================


@pytest.fixture
def clean_recorder(monkeypatch):
    calls = []

    with patched_attrs(
        monkeypatch,
        tasks,
        post_processing_all=lambda: calls.append("post_processing_all"),
        edi_trace_supplier_insert=lambda: calls.append("edi_trace_supplier_insert"),
        set_exclusions=lambda: calls.append("set_exclusions"),
    ):
        yield calls


def test_launch_sql_clean_general(clean_recorder, make_sse_progress):
    progress = make_sse_progress(total_items=2)

    result = tasks.launch_sql_clean_general(0.0, progress.job_id)

    assert clean_recorder == ["post_processing_all", "edi_trace_supplier_insert", "set_exclusions"]
    assert set(result) == {"Clean Sql Général : ", "Ensemble"}
    progress.refresh_from_db()
    assert progress.processed_items == 1
    assert progress.current_message == "Validation et mises à jour"


def test_launch_sql_clean_general_sans_job(clean_recorder):
    tasks.launch_sql_clean_general(0.0)

    assert clean_recorder == ["post_processing_all", "edi_trace_supplier_insert", "set_exclusions"]


@pytest.mark.usefixtures("clean_recorder", "db")
def test_launch_sql_clean_general_jauge_inconnue(caplog):
    """Jauge inconnue au départ : avertissement, puis l'erreur de fin est journalisée"""
    tasks.launch_sql_clean_general(0.0, "job-inconnu")

    assert "SSEProgress non trouvé pour job_id: job-inconnu" in caplog.text
    assert "Exception Générale: sur tâche launch_sql_clean_general" in caplog.text


@pytest.mark.usefixtures("clean_recorder", "db")
def test_launch_sql_clean_general_erreur_jauge(monkeypatch, caplog):
    with patched_attrs(monkeypatch, tasks, SSEProgress=BrokenProgress):
        tasks.launch_sql_clean_general(0.0, "job")

    assert "Erreur mise à jour progression" in caplog.text


@pytest.mark.usefixtures("db")
def test_launch_sql_clean_general_erreur_traitement(monkeypatch, caplog):
    def _boom():
        raise RuntimeError("sql cassé")

    with patched_attrs(monkeypatch, tasks, post_processing_all=_boom):
        tasks.launch_sql_clean_general(0.0)

    assert "sql cassé" in caplog.text


# ABONNEMENTS ======================================================================================


def test_subscription_launch_task(make_trace, make_user, make_sse_progress, monkeypatch):
    user = make_user()
    trace = make_trace(time_to_process=2)
    progress = make_sse_progress(user=user)
    seen = {}

    def _royalties(dte_d, dte_f, user_uuid):
        seen.update({"dte_d": dte_d, "dte_f": dte_f, "user": user_uuid})
        return trace, "Génération des royalties "

    with patched_attrs(monkeypatch, tasks, get_object=lambda name: _royalties):
        result = tasks.subscription_launch_task(
            "royalties", "2026-01-01", "2026-01-31", str(user.uuid_identification), progress.job_id
        )

    assert seen == {
        "dte_d": "2026-01-01",
        "dte_f": "2026-01-31",
        "user": str(user.uuid_identification),
    }
    assert result == {
        "Génération des abonnement : ": "Génération des royalties , réalisée avec sucess, en 2 s"
    }
    trace.refresh_from_db()
    assert trace.created_by == user
    progress.refresh_from_db()
    assert progress.processed_items == 1
    assert "traité avec succès" in progress.current_message


def test_subscription_launch_task_sans_abonnements(
    make_trace, make_user, make_sse_progress, monkeypatch
):
    """La fonction renvoie un message d'erreur métier : résultat en erreur avec le commentaire"""
    user = make_user()
    trace = make_trace(time_to_process=2, comment="rien à générer")
    progress = make_sse_progress(user=user)

    with patched_attrs(
        monkeypatch,
        tasks,
        get_object=lambda name: fake_import(trace, "Erreur Génération des royalties"),
    ):
        result = tasks.subscription_launch_task(
            "royalties", "2026-01-01", "2026-01-31", str(user.uuid_identification), progress.job_id
        )

    assert (
        result["Génération des abonnement : "]
        == "Erreur -  Génération des royalties : 'rien à générer'"
    )


def test_subscription_launch_task_type_error(make_user, make_sse_progress, monkeypatch, caplog):
    """Fonction à la mauvaise signature : TypeError, pas de trace, jauge en échec"""
    user = make_user()
    progress = make_sse_progress(user=user)

    with patched_attrs(monkeypatch, tasks, get_object=lambda name: lambda: None):
        result = tasks.subscription_launch_task(
            "royalties", "2026-01-01", "2026-01-31", str(user.uuid_identification), progress.job_id
        )

    assert "TypeError" in caplog.text
    assert result["Génération des abonnement : "].startswith("Erreur - TypeError")
    progress.refresh_from_db()
    assert progress.failed_items == 1


def test_subscription_launch_task_exception_generale_avec_trace(make_trace, monkeypatch, caplog):
    """Erreur après la trace (utilisateur inconnu) : trace en erreur, commentaire précédé de l'ancien"""
    trace = make_trace(comment="Génération", time_to_process=1)

    with patched_attrs(
        monkeypatch, tasks, get_object=lambda name: fake_import(trace, "Génération des royalties ")
    ):
        result = tasks.subscription_launch_task(
            "royalties", "2026-01-01", "2026-01-31", "00000000-0000-0000-0000-000000000000", None
        )

    assert "Exception Générale: royalties" in caplog.text
    trace.refresh_from_db()
    assert trace.errors is True
    assert trace.comment == "Génération\nUne erreur c'est produite veuillez consulter les logs"
    assert result["Génération des abonnement : "].startswith("Erreur - Génération des royalties  :")


def test_subscription_launch_task_trace_sans_commentaire(make_trace, monkeypatch):
    trace = make_trace(comment="", time_to_process=1)

    with patched_attrs(monkeypatch, tasks, get_object=lambda name: fake_import(trace, "ok")):
        tasks.subscription_launch_task(
            "royalties", "2026-01-01", "2026-01-31", "00000000-0000-0000-0000-000000000000", None
        )

    trace.refresh_from_db()
    assert trace.comment == "Une erreur c'est produite veuillez consulter les logs"


def test_subscription_launch_task_erreur_jauge(make_trace, make_user, monkeypatch, caplog):
    user = make_user()

    with patched_attrs(
        monkeypatch,
        tasks,
        get_object=lambda name: fake_import(make_trace(time_to_process=1)),
        SSEProgress=BrokenProgress,
    ):
        tasks.subscription_launch_task(
            "royalties", "2026-01-01", "2026-01-31", str(user.uuid_identification), "job"
        )

    assert "Erreur lors de la mise à jour du SSEProgress" in caplog.text


# JAUGE DE TEST ====================================================================================


@pytest.mark.usefixtures("no_sleep")
def test_task_test_import_jauge(make_user):
    user = make_user()

    result = tasks.task_test_import_jauge("job-test", user.pk)

    assert result == {"status": "success", "job_id": "job-test"}
    progress = SSEProgress.objects.get(job_id="job-test")
    assert progress.status == "completed"
    assert progress.processed_items == 100


def test_task_test_import_jauge_erreur_pendant_le_traitement(make_user, monkeypatch, caplog):
    """Erreur en cours de route : la jauge est marquée en échec puis l'erreur remonte"""
    user = make_user()

    def _boom(_seconds):
        raise RuntimeError("interruption")

    with patched_attrs(monkeypatch, tasks.time, sleep=_boom):
        with pytest.raises(RuntimeError, match="interruption"):
            tasks.task_test_import_jauge("job-ko", user.pk)

    assert SSEProgress.objects.get(job_id="job-ko").status == "failed"
    assert "Erreur dans test_import_jauge" in caplog.text


@pytest.mark.usefixtures("db")
def test_task_test_import_jauge_erreur_a_la_creation(monkeypatch):
    """La jauge n'a pu être créée : l'échec ne peut être marqué, l'erreur remonte quand même"""
    with patched_attrs(monkeypatch, tasks, SSEProgress=BrokenProgress):
        with pytest.raises(RuntimeError, match="création impossible"):
            tasks.task_test_import_jauge("job-ko", 1)


def test_fichier_absent_n_est_pas_deplace(edi_dirs, make_trace, make_user, monkeypatch):
    """Le fichier a déjà disparu : ni déplacement ni suppression"""
    file = edi_dirs.processing / "WIDEX" / "absent.csv"
    backup = edi_dirs.backup / "WIDEX" / "absent.csv"

    with patched_attrs(monkeypatch, tasks, processing_dict={"WIDEX": fake_import(make_trace())}):
        tasks.launch_suppliers_import((str(file), str(backup), "WIDEX"), make_user().pk, None)

    assert not backup.exists()
    assert isinstance(Path(file), Path)
