"""
Tests de la boucle d'import des fichiers fournisseurs (apps/edi/loops/imports_loop_pool.py)

- Séparation des fichiers EDI multiples, liste des fichiers à traiter (répertoires temporaires).
- Détection des imports B.I BBGR à faire (tables B.I créées en DDL dans la transaction).
- Lancements celery : group / signature remplacés par des enregistreurs.

created at: 2026-10-10
created by: Paulo ALVES
"""
import asyncio

import pytest
from django.db import connection

from apps.core.models import SSEProgress
from apps.edi.bin.bbgr_002_statment import HISTORIC_STATMENT_ID
from apps.edi.bin.bbgr_003_monthly import HISTORIC_MONTHLY_ID
from apps.edi.bin.bbgr_004_retours import HISTORIC_RETOURS_ID
from apps.edi.bin.bbgr_005_receptions import HISTORIC_RECEPTIONS_ID
from apps.edi.loops import imports_loop_pool as module
from conftest import patched_attrs

EDI_TEXT = "UNA:+.? '\nUNB+A'\nUNA:+.? '\nUNB+B'\n"


# SÉPARATION DES FICHIERS EDI ======================================================================


def test_separate_edi_repertoire_absent(edi_dirs, caplog):
    (edi_dirs.processing / "EDI").rmdir()

    module.separate_edi()

    assert "n'existe pas" in caplog.text


def test_separate_edi_chemin_non_repertoire(edi_dirs, caplog):
    (edi_dirs.processing / "EDI").rmdir()
    (edi_dirs.processing / "EDI").write_text("fichier", encoding="utf8")

    module.separate_edi()

    assert "n'est pas un répertoire" in caplog.text


def test_separate_edi_decoupe_les_fichiers_multiples(edi_dirs, monkeypatch):
    """Fichier à deux UNA : deux fichiers .edi créés, l'original supprimé ; fichier simple conservé"""
    edi_dir = edi_dirs.processing / "EDI"
    (edi_dir / "._cache").write_text("x", encoding="utf8")
    (edi_dir / "._dossier").mkdir()
    (edi_dir / "simple.edi").write_text("UNA:+.? '\nUNB+A'\n", encoding="utf8")
    (edi_dir / "multiple.edi").write_text(EDI_TEXT, encoding="utf8")
    (edi_dir / "multiple.existant.edi").write_text("déjà là", encoding="utf8")
    names = iter(["existant", "libre1", "libre2"])

    with patched_attrs(monkeypatch, module, get_random_name=lambda: next(names)):
        module.separate_edi()

    produced = sorted(path.name for path in edi_dir.iterdir())
    assert produced == ["._dossier", "multiple.existant.edi", "multiple.libre1.edi", "multiple.libre2.edi", "simple.edi"]
    assert (edi_dir / "multiple.libre1.edi").read_text(encoding="utf8") == "UNB+A'\n"
    assert (edi_dir / "multiple.libre2.edi").read_text(encoding="utf8") == "UNB+B'"


def test_separate_edi_erreur_sur_un_fichier_continue(edi_dirs, monkeypatch, caplog):
    edi_dir = edi_dirs.processing / "EDI"
    (edi_dir / "a.edi").write_text(EDI_TEXT, encoding="utf8")
    (edi_dir / "b.edi").write_text(EDI_TEXT, encoding="utf8")

    def _boom(_file):
        raise ValueError("encodage inconnu")

    with patched_attrs(monkeypatch, module, encoding_detect=_boom):
        module.separate_edi()

    assert caplog.text.count("Erreur lors du traitement du fichier") == 2
    assert sorted(path.name for path in edi_dir.iterdir()) == ["a.edi", "b.edi"]


def test_separate_edi_encodage_non_detecte(edi_dirs, monkeypatch):
    """encoding_detect sans résultat : lecture en ascii"""
    edi_dir = edi_dirs.processing / "EDI"
    (edi_dir / "a.edi").write_text(EDI_TEXT, encoding="utf8")

    with patched_attrs(monkeypatch, module, encoding_detect=lambda _file: None):
        module.separate_edi()

    assert len(list(edi_dir.iterdir())) == 2


@pytest.mark.usefixtures('edi_dirs')
def test_separate_edi_erreur_generale(monkeypatch, caplog):
    class _BrokenPath:
        def __init__(self, *_args):
            pass

        def __truediv__(self, _other):
            return self

        def exists(self):
            raise RuntimeError("disque indisponible")

    with patched_attrs(monkeypatch, module, Path=_BrokenPath):
        module.separate_edi()

    assert "Erreur lors de la séparation des fichiers EDI" in caplog.text


# LISTE DES FICHIERS À TRAITER =====================================================================


def test_get_files_celery(edi_dirs):
    (edi_dirs.processing / "WIDEX" / "w1.csv").write_text("x", encoding="utf8")
    (edi_dirs.processing / "WIDEX" / "._w1.csv").write_text("x", encoding="utf8")
    (edi_dirs.processing / "WIDEX" / "._dossier").mkdir()
    (edi_dirs.processing / "LMC" / "l1.csv").write_text("x", encoding="utf8")

    files = module.get_files_celery()

    assert sorted(files) == [
        (str(edi_dirs.processing / "LMC" / "l1.csv"), str(edi_dirs.backup / "LMC" / "l1.csv"), "LMC"),
        (str(edi_dirs.processing / "WIDEX" / "w1.csv"), str(edi_dirs.backup / "WIDEX" / "w1.csv"), "WIDEX"),
    ]
    assert not (edi_dirs.processing / "WIDEX" / "._w1.csv").exists()
    assert (edi_dirs.processing / "WIDEX" / "._dossier").is_dir()


# DÉTECTION DES IMPORTS B.I ========================================================================


def test_get_have_statment(bi_tables):
    assert module.get_have_statment() is False

    bi_tables("heron_bi_factures_billstatement", id=HISTORIC_STATMENT_ID + 1)

    assert module.get_have_statment() is True


def test_get_have_statment_deja_importe(bi_tables, make_edi_import):
    """La dernière ligne B.I est déjà dans edi_ediimport : rien à importer"""
    bi_tables("heron_bi_factures_billstatement", id=HISTORIC_STATMENT_ID + 1)
    make_edi_import(flow_name="BbgrStatment", bi_id=HISTORIC_STATMENT_ID + 1)

    assert module.get_have_statment() is False


def test_get_have_monthly_et_retours(bi_tables):
    assert module.get_have_monthly() is False
    assert module.get_have_retours() is False

    bi_tables("heron_bi_factures_monthlydelivery", id=HISTORIC_MONTHLY_ID + 1, type_article="MONTURE")

    assert module.get_have_monthly() is True
    assert module.get_have_retours() is False

    bi_tables("heron_bi_factures_monthlydelivery", id=HISTORIC_RETOURS_ID + 2, type_article="DECOTE")

    assert module.get_have_retours() is True


def test_get_have_receptions(bi_tables):
    assert module.get_have_receptions() is False

    bi_tables("heron_bi_receptions_bbgr", id=HISTORIC_RECEPTIONS_ID + 1)

    assert module.get_have_receptions() is True


def test_get_retours_valid(bi_tables, monkeypatch):
    """La base B.I (alias bi_bdd) est lue sur la connexion de test, qui porte la table créée"""
    with patched_attrs(monkeypatch, module, connections={"bi_bdd": connection}):
        assert module.get_retours_valid() is True

        bi_tables("factures_monthlyretours", validation=False)

        assert module.get_retours_valid() is False


@pytest.mark.parametrize(
    ("truthy", "expected"),
    [
        ("get_have_statment", True),
        ("get_have_monthly", True),
        ("get_have_retours", True),
        ("get_have_receptions", True),
        ("get_files_celery", True),
        (None, False),
    ],
)
def test_have_files(monkeypatch, truthy, expected):
    """Le premier contrôle positif suffit ; tous négatifs -> False"""
    names = ["get_have_statment", "get_have_monthly", "get_have_retours", "get_have_receptions", "get_files_celery"]
    patches = {name: (lambda name=name: name == truthy and ([("f", "b", "D")] if name == "get_files_celery" else True)) for name in names}

    with patched_attrs(monkeypatch, module, **patches):
        assert module.have_files() is expected


# VERSIONS ASYNC ===================================================================================


def test_with_db_cleanup_ferme_les_connexions(monkeypatch):
    closed = []

    with patched_attrs(monkeypatch, module, close_old_connections=lambda: closed.append(True)):
        assert module._with_db_cleanup(lambda value: value * 2)(21) == 42  # pylint: disable=W0212

    assert closed == [True]


def test_get_all_import_checks_async(monkeypatch):
    async def _value(value):
        return value

    with patched_attrs(
        monkeypatch,
        module,
        get_have_statment_async=lambda: _value(True),
        get_have_monthly_async=lambda: _value(False),
        get_have_retours_async=lambda: _value(True),
        get_have_receptions_async=lambda: _value(False),
        get_files_celery_async=lambda: _value([("f", "b", "WIDEX")]),
        get_retours_valid_async=lambda: _value(True),
    ):
        assert asyncio.run(module.get_all_import_checks_async()) == [
            True, False, True, False, [("f", "b", "WIDEX")], True
        ]


def test_get_import_controls_async(monkeypatch):
    seen = {}

    async def _in_progress(action, task_name):
        seen.update({"action": action, "task_name": task_name})
        return False

    async def _control():
        return True

    with patched_attrs(
        monkeypatch, module, get_in_progress_async=_in_progress, control_insertion_async=_control
    ):
        assert asyncio.run(module.get_import_controls_async()) == [False, True]

    assert seen == {"action": "import_edi_invoices", "task_name": "suppliers_import"}


@pytest.mark.usefixtures('bi_tables')
def test_fonctions_async_executent_les_fonctions_synchrones(monkeypatch):
    """Les wrappers async appellent bien les fonctions synchrones (dans le thread courant ici)"""
    with patched_attrs(monkeypatch, module, get_have_statment=lambda: "statment"):
        wrapped = module.sync_to_async(module._with_db_cleanup(module.get_have_statment))  # pylint: disable=W0212

        assert asyncio.run(wrapped()) == "statment"


# LANCEMENTS CELERY ================================================================================


class FakeGroupResult:
    """Résultat d'un group celery"""

    def __init__(self, value):
        self.value = value

    def get(self, timeout):
        self.timeout = timeout  # pylint: disable=W0201
        return self.value


@pytest.fixture
def celery_recorder(monkeypatch):
    """Remplace celery_app.signature et group : enregistre les signatures, renvoie les résultats"""
    calls = {"signatures": [], "groups": [], "fail": None}

    def _signature(name, kwargs):
        calls["signatures"].append((name, kwargs))
        return (name, kwargs)

    def _group(*signatures):
        calls["groups"].append(signatures)

        def _apply():
            if calls["fail"] is not None:
                raise calls["fail"]

            return FakeGroupResult([f"résultat {name}" for name, _ in signatures])

        return _apply

    with patched_attrs(monkeypatch, module, group=_group), patched_attrs(
        monkeypatch, module.celery_app, signature=_signature
    ), patched_attrs(monkeypatch, module.time, sleep=lambda _seconds: None):
        yield calls


def test_celery_import_launch(celery_recorder, make_action, make_sse_progress, monkeypatch):
    """Verrou posé puis libéré, une signature par fichier, nettoyage sql, jauge terminée"""
    action = make_action(in_progress=False)
    progress = make_sse_progress(total_items=3)
    files = [("/p/WIDEX/a.csv", "/b/WIDEX/a.csv", "WIDEX"), ("/p/LMC/b.csv", "/b/LMC/b.csv", "LMC")]

    with patched_attrs(monkeypatch, module, get_files_celery=lambda: files):
        module.celery_import_launch(progress.user_id, progress.job_id)

    names = [name for name, _ in celery_recorder["signatures"]]
    assert names == ["suppliers_import", "suppliers_import", "sql_clean_general"]
    assert celery_recorder["signatures"][0][1] == {
        "process_objects": files[0], "user_pk": progress.user_id, "job_id": progress.job_id
    }
    assert celery_recorder["signatures"][2][1]["job_id"] == progress.job_id
    assert len(celery_recorder["groups"]) == 2
    action.refresh_from_db()
    assert action.in_progress is False
    progress.refresh_from_db()
    assert progress.status == "completed"


def test_celery_import_launch_attend_le_verrou(celery_recorder, make_action, make_sse_progress, monkeypatch):
    """Action déjà en cours : on attend (sleep patché libère le verrou) puis on traite"""
    action = make_action(in_progress=True)
    progress = make_sse_progress()
    waits = []

    def _release(_seconds):
        waits.append(True)
        action.in_progress = False
        action.save()

    with patched_attrs(monkeypatch, module, get_files_celery=lambda: []), patched_attrs(
        monkeypatch, module.time, sleep=_release
    ):
        module.celery_import_launch(progress.user_id, progress.job_id)

    assert waits == [True]
    assert [name for name, _ in celery_recorder["signatures"]] == ["sql_clean_general"]
    progress.refresh_from_db()
    assert progress.status == "completed"


def test_celery_import_launch_erreur_apres_la_jauge(celery_recorder, make_action, make_sse_progress, monkeypatch):
    """Erreur celery : la jauge est marquée en échec, le verrou libéré"""
    action = make_action()
    progress = make_sse_progress()
    celery_recorder["fail"] = RuntimeError("worker injoignable")

    with patched_attrs(monkeypatch, module, get_files_celery=lambda: []):
        module.celery_import_launch(progress.user_id, progress.job_id)

    progress.refresh_from_db()
    assert progress.status == "failed"
    assert "worker injoignable" in progress.error_message
    action.refresh_from_db()
    assert action.in_progress is False


@pytest.mark.usefixtures('celery_recorder')
def test_celery_import_launch_erreur_avant_la_jauge(make_action, make_sse_progress, monkeypatch):
    """Erreur avant de récupérer la jauge : elle est retrouvée et marquée en échec"""
    make_action()
    progress = make_sse_progress()

    def _boom():
        raise RuntimeError("répertoire illisible")

    with patched_attrs(monkeypatch, module, get_files_celery=_boom):
        module.celery_import_launch(progress.user_id, progress.job_id)

    progress.refresh_from_db()
    assert progress.status == "failed"


@pytest.mark.usefixtures('celery_recorder')
def test_celery_import_launch_jauge_inconnue(make_action, make_user, caplog, monkeypatch):
    make_action()

    with patched_attrs(monkeypatch, module, get_files_celery=lambda: []):
        module.celery_import_launch(make_user().pk, "job-inconnu")

    assert "Impossible de marquer le SSEProgress comme failed" in caplog.text


@pytest.mark.usefixtures('db')
def test_celery_import_launch_sans_verrou_pose(celery_recorder, caplog, monkeypatch):
    """get_action échoue : rien n'est lancé et le finally n'explose pas sur un verrou absent"""

    def _boom(action):
        raise RuntimeError("base indisponible")

    with patched_attrs(monkeypatch, module, get_action=_boom):
        module.celery_import_launch(1, "job")

    assert celery_recorder["signatures"] == []
    assert "celery_import_launch()" in caplog.text


def test_import_launch_bbgr(celery_recorder, make_action, make_sse_progress):
    action = make_action()
    progress = make_sse_progress(task_type="bbgr_import", total_items=2)

    module.import_launch_bbgr("bbgr_statment", progress.user_id, progress.job_id)

    assert celery_recorder["signatures"] == [
        ("bbgr_bi", {"function_name": "bbgr_statment", "user_pk": progress.user_id, "job_id": progress.job_id}),
        ("sql_clean_general", {"start_all": celery_recorder["signatures"][1][1]["start_all"], "job_id": progress.job_id}),
    ]
    progress.refresh_from_db()
    assert progress.status == "completed"
    action.refresh_from_db()
    assert action.in_progress is False


@pytest.mark.usefixtures('celery_recorder')
def test_import_launch_bbgr_attend_le_verrou(make_action, make_sse_progress, monkeypatch):
    action = make_action(in_progress=True)
    progress = make_sse_progress()

    def _release(_seconds):
        action.in_progress = False
        action.save()

    with patched_attrs(monkeypatch, module.time, sleep=_release):
        module.import_launch_bbgr("bbgr_monthly", progress.user_id, progress.job_id)

    progress.refresh_from_db()
    assert progress.status == "completed"


def test_import_launch_bbgr_erreur(celery_recorder, make_action, make_sse_progress):
    make_action()
    progress = make_sse_progress()
    celery_recorder["fail"] = RuntimeError("worker injoignable")

    module.import_launch_bbgr("bbgr_retours", progress.user_id, progress.job_id)

    progress.refresh_from_db()
    assert progress.status == "failed"


@pytest.mark.usefixtures('celery_recorder')
def test_import_launch_bbgr_jauge_inconnue(make_action, make_user, caplog):
    make_action()

    module.import_launch_bbgr("bbgr_receptions", make_user().pk, "job-inconnu")

    assert "Impossible de marquer le SSEProgress comme failed" in caplog.text


@pytest.mark.usefixtures('celery_recorder', 'db')
def test_import_launch_bbgr_sans_verrou_pose(caplog, monkeypatch):
    def _boom(action):
        raise RuntimeError("base indisponible")

    with patched_attrs(monkeypatch, module, get_action=_boom):
        module.import_launch_bbgr("bbgr_statment", 1, "job")

    assert "import_launch_bbgr()" in caplog.text


def test_import_launch_subscriptions(celery_recorder, make_action, make_sse_progress):
    action = make_action()
    progress = make_sse_progress(task_type="subscriptions")

    error, info = module.import_launch_subscriptions(
        "royalties", "2026-01-01", "2026-01-31", "user-uuid", progress.job_id
    )

    assert error is False
    assert info == "['résultat subscription_launch_task']"
    assert celery_recorder["signatures"] == [
        (
            "subscription_launch_task",
            {
                "task_to_launch": "royalties",
                "dte_d": "2026-01-01",
                "dte_f": "2026-01-31",
                "user": "user-uuid",
                "job_id": progress.job_id,
            },
        )
    ]
    progress.refresh_from_db()
    assert progress.status == "completed"
    action.refresh_from_db()
    assert action.in_progress is False


def test_import_launch_subscriptions_erreur_celery(celery_recorder, make_action, make_sse_progress):
    make_action()
    progress = make_sse_progress()
    celery_recorder["fail"] = RuntimeError("worker injoignable")

    error, info = module.import_launch_subscriptions("royalties", "2026-01-01", "2026-01-31", "u", progress.job_id)

    assert error is True
    assert "worker injoignable" in info
    progress.refresh_from_db()
    assert progress.status == "failed"


@pytest.mark.usefixtures('celery_recorder')
def test_import_launch_subscriptions_jauge_inconnue(make_action, caplog):
    make_action()

    error, info = module.import_launch_subscriptions("royalties", "2026-01-01", "2026-01-31", "u", "job-inconnu")

    assert error is True
    assert "SSEProgress matching query does not exist" in info
    assert "Impossible de marquer le SSEProgress comme failed" in caplog.text


@pytest.mark.usefixtures('celery_recorder')
def test_import_launch_subscriptions_sans_job(make_action, caplog):
    """Sans job_id : la jauge n'est ni cherchée en secours ni marquée"""
    make_action()

    error, _ = module.import_launch_subscriptions("royalties", "2026-01-01", "2026-01-31", "u", None)

    assert error is True
    assert "Impossible de marquer" not in caplog.text
    assert SSEProgress.objects.count() == 0
