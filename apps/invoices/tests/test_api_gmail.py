# pylint: disable=E0401,W0621,W0611,R0913
"""Tests du paquet api_gmail : configuration, authentification OAuth2, envoi, tâches et vues"""

import json
import logging
import types
from pathlib import Path

import pytest
from django.test import RequestFactory

from apps.data_flux.models import Trace
from apps.invoices.bin.api_gmail import (
    auth,
    config as config_module,
    sender as sender_module,
    tasks_gmail,
    tasks_gmail_sse,
    views_sse,
)
from apps.invoices.bin.api_gmail.sender import EmailResult, RateLimiter
from apps.invoices.tests.helpers_external import INVOICE_MONTH, http_error

pytestmark = pytest.mark.django_db


# CONFIGURATION ====================================================================================
def test_gmail_config_lecture_et_valeurs_par_defaut(gmail_config_file):
    config = config_module.GmailConfig(gmail_config_file())

    assert config.oauth2_client_id == "id"
    assert config.oauth2_client_secret == "secret"
    assert config.oauth2_redirect_uris == ["http://localhost"]
    assert config.oauth2_auth_uri.startswith("https://accounts.google.com")
    assert config.oauth2_token_uri.startswith("https://oauth2")
    assert config.scopes == ["https://www.googleapis.com/auth/gmail.send"]
    assert config.sender_email == "factures@heron.local"
    assert config.sender_name == "Heron"
    assert config.max_per_second == 2
    assert (config.max_per_minute, config.batch_size, config.delay_between_batches) == (100, 50, 2)
    assert (
        config.max_retries,
        config.retry_delay,
        config.retry_backoff,
        config.max_retry_delay,
    ) == (3, 5, 2, 60)
    assert (config.http_timeout, config.auth_timeout) == (30, 60)
    assert config.credentials_file_name == "gmail_credentials.json"
    assert config.token_file_name == "gmail_token.json"
    assert config.credentials_file_path == config_module.ENV_DIR / "gmail_credentials.json"
    assert config.token_file_path == config_module.ENV_DIR / "gmail_token.json"
    assert (config.log_level, config.debug) == ("INFO", False)
    assert (config.use_batch_mode, config.check_quotas, config.save_draft_on_failure) == (
        True,
        True,
        False,
    )
    assert config.get("sender.email.nested") is None
    assert config.get("inconnu", "défaut") == "défaut"
    assert config.get_oauth2_credentials_dict()["installed"]["client_id"] == "id"


@pytest.mark.usefixtures("gmail_config_file")
def test_gmail_config_fichier_absent_ou_invalide(tmp_path):
    with pytest.raises(FileNotFoundError, match="n'existe pas"):
        config_module.GmailConfig(tmp_path / "absent.yaml")

    bad = tmp_path / "bad.yaml"
    bad.write_text("oauth2: [unclosed", encoding="utf-8")

    with pytest.raises(ValueError, match="YAML"):
        config_module.GmailConfig(bad)


def test_config_module_est_paresseux():
    """L'instance globale ne lit le fichier qu'au premier accès (plus de lecture à l'import)"""
    assert type(config_module.config).__name__ == "SimpleLazyObject"
    assert type(auth.authenticator).__name__ == "SimpleLazyObject"
    assert type(sender_module.sender).__name__ == "SimpleLazyObject"


# AUTHENTIFICATION =================================================================================
@pytest.fixture
def authenticator(tmp_path, monkeypatch):
    """GmailAuthenticator sur des fichiers temporaires et des classes Google simulées"""
    auth_obj = auth.GmailAuthenticator()
    auth_obj.config = types.SimpleNamespace(
        token_file_path=tmp_path / "token.json",
        credentials_file_path=tmp_path / "credentials.json",
        scopes=["scope"],
        get_oauth2_credentials_dict=lambda: {"installed": {"client_id": "id"}},
    )
    return auth_obj


def creds(valid=True, expired=False, refresh_token=None, refresh_error=None):
    """Credentials simulés"""
    state = types.SimpleNamespace(valid=valid, expired=expired, refresh_token=refresh_token)

    def refresh(request):
        if refresh_error:
            raise refresh_error
        state.valid = True

    state.refresh = refresh
    state.to_json = lambda: json.dumps({"token": "t"})
    return state


def test_get_credentials_token_valide(authenticator, monkeypatch):
    authenticator.config.token_file_path.write_text("{}")
    valid = creds()
    monkeypatch.setattr(
        auth.Credentials, "from_authorized_user_file", staticmethod(lambda path, scopes: valid)
    )

    assert authenticator.get_credentials() is valid


def test_get_credentials_token_expire_rafraichi(authenticator, monkeypatch):
    authenticator.config.token_file_path.write_text("{}")
    expired = creds(valid=False, expired=True, refresh_token="r")
    monkeypatch.setattr(
        auth.Credentials, "from_authorized_user_file", staticmethod(lambda path, scopes: expired)
    )
    monkeypatch.setattr(auth, "Request", lambda: None)

    result = authenticator.get_credentials()

    assert result is expired
    assert result.valid is True
    assert json.loads(authenticator.config.token_file_path.read_text()) == {"token": "t"}


def test_get_credentials_flow_complet(authenticator, monkeypatch, caplog):
    """Token illisible, rafraîchissement en échec puis flow OAuth2 ; credentials.json créé"""
    authenticator.config.token_file_path.write_text("corrompu")

    def bad_load(path, scopes):
        raise ValueError("illisible")

    monkeypatch.setattr(auth.Credentials, "from_authorized_user_file", staticmethod(bad_load))
    new_creds = creds()
    flow = types.SimpleNamespace(run_local_server=lambda port: new_creds)
    monkeypatch.setattr(
        auth.InstalledAppFlow, "from_client_secrets_file", staticmethod(lambda path, scopes: flow)
    )

    with caplog.at_level(logging.WARNING, logger="send_email"):
        result = authenticator.get_credentials()

    assert result is new_creds
    assert "Erreur lors du chargement du token" in caplog.text
    assert json.loads(authenticator.config.credentials_file_path.read_text()) == {
        "installed": {"client_id": "id"}
    }


def test_get_credentials_refresh_en_erreur_puis_flow(authenticator, monkeypatch):
    authenticator.config.token_file_path.write_text("{}")
    expired = creds(
        valid=False, expired=True, refresh_token="r", refresh_error=RuntimeError("refresh ko")
    )
    monkeypatch.setattr(
        auth.Credentials, "from_authorized_user_file", staticmethod(lambda path, scopes: expired)
    )
    monkeypatch.setattr(auth, "Request", lambda: None)
    new_creds = creds()
    monkeypatch.setattr(
        auth.InstalledAppFlow,
        "from_client_secrets_file",
        staticmethod(
            lambda path, scopes: types.SimpleNamespace(run_local_server=lambda port: new_creds)
        ),
    )

    assert authenticator.get_credentials() is new_creds


def test_get_credentials_fichier_credentials_introuvable(authenticator, monkeypatch):
    monkeypatch.setattr(authenticator, "_create_credentials_file_if_needed", lambda path: None)

    with pytest.raises(FileNotFoundError, match="credentials"):
        authenticator.get_credentials()


def test_get_credentials_flow_en_erreur(authenticator, monkeypatch, caplog):
    def bad_flow(path, scopes):
        raise RuntimeError("flow ko")

    monkeypatch.setattr(auth.InstalledAppFlow, "from_client_secrets_file", staticmethod(bad_flow))

    with pytest.raises(RuntimeError), caplog.at_level(logging.ERROR, logger="send_email"):
        authenticator.get_credentials()

    assert "Erreur lors de l'authentification OAuth2" in caplog.text


def test_get_credentials_sauvegarde_token_impossible(authenticator, monkeypatch, tmp_path, caplog):
    authenticator.config.token_file_path = tmp_path / "absent" / "token.json"
    new_creds = creds()
    monkeypatch.setattr(
        auth.InstalledAppFlow,
        "from_client_secrets_file",
        staticmethod(
            lambda path, scopes: types.SimpleNamespace(run_local_server=lambda port: new_creds)
        ),
    )

    with caplog.at_level(logging.WARNING, logger="send_email"):
        assert authenticator.get_credentials() is new_creds

    assert "Erreur lors de la sauvegarde du token" in caplog.text


def test_create_credentials_file_deja_present(authenticator):
    authenticator.config.credentials_file_path.write_text("{}")

    authenticator._create_credentials_file_if_needed(authenticator.config.credentials_file_path)  # pylint: disable=W0212

    assert authenticator.config.credentials_file_path.read_text() == "{}"


def test_create_credentials_file_erreur(authenticator, tmp_path, caplog):
    authenticator.config.credentials_file_path = tmp_path / "absent" / "credentials.json"

    with pytest.raises(OSError, match=r".+"), caplog.at_level(logging.ERROR, logger="send_email"):
        authenticator._create_credentials_file_if_needed(authenticator.config.credentials_file_path)  # pylint: disable=W0212

    assert "Erreur lors de la création du fichier credentials.json" in caplog.text


def test_get_gmail_service(authenticator, monkeypatch):
    service = object()
    monkeypatch.setattr(authenticator, "get_credentials", lambda: "creds")
    monkeypatch.setattr(auth, "build", lambda *args, **kwargs: service)

    assert authenticator.get_gmail_service() is service
    assert authenticator.get_gmail_service() is service  # mis en cache


def test_get_gmail_service_erreur(authenticator, monkeypatch, caplog):
    def boom():
        raise RuntimeError("no creds")

    monkeypatch.setattr(authenticator, "get_credentials", boom)

    with pytest.raises(RuntimeError), caplog.at_level(logging.ERROR, logger="send_email"):
        authenticator.get_gmail_service()


def test_revoke_credentials(authenticator, monkeypatch, caplog):
    authenticator.revoke_credentials()  # pas de token : rien à faire
    authenticator.config.token_file_path.write_text("{}")
    authenticator.creds, authenticator.service = "c", "s"

    authenticator.revoke_credentials()

    assert not authenticator.config.token_file_path.exists()
    assert authenticator.creds is None
    assert authenticator.service is None

    authenticator.config.token_file_path.write_text("{}")

    def boom():
        raise OSError("verrou")

    monkeypatch.setattr(type(authenticator.config.token_file_path), "unlink", lambda self: boom())

    with pytest.raises(OSError, match=r".+"), caplog.at_level(logging.ERROR, logger="send_email"):
        authenticator.revoke_credentials()


# RATE LIMITER / SENDER ============================================================================
def test_rate_limiter_attend_si_necessaire(monkeypatch):
    limiter = RateLimiter(max_per_second=2)
    clock = iter([100.0, 100.1, 100.6, 200.0, 200.0])
    slept = []
    monkeypatch.setattr(sender_module.time, "time", lambda: next(clock))
    monkeypatch.setattr(sender_module.time, "sleep", slept.append)

    limiter.last_send_time = 100.0
    limiter.wait_if_needed()
    limiter.wait_if_needed()

    assert slept == [0.5]


def test_create_message_avec_pieces_jointes(fake_sender_module, tmp_path, caplog):
    sender, _ = fake_sender_module()
    attachment = tmp_path / "facture.pdf"
    attachment.write_bytes(b"%PDF")

    with caplog.at_level(logging.WARNING, logger="send_email"):
        message = sender.create_message(
            ["a@b.fr", "c@d.fr"],
            "Sujet {cct}",
            "texte",
            "<p>{cct}</p>",
            {"cct": "AF0001"},
            [attachment, tmp_path / "absent.pdf"],
        )

    assert set(message) == {"raw"}
    assert "Fichier non trouvé" in caplog.text


def test_create_message_piece_jointe_illisible(fake_sender_module, tmp_path, monkeypatch, caplog):
    sender, _ = fake_sender_module()
    attachment = tmp_path / "facture.pdf"
    attachment.write_bytes(b"%PDF")
    real_open = Path.open

    def bad_open(path, *args, **kwargs):
        if str(path).endswith("facture.pdf"):
            raise OSError("illisible")
        return real_open(path, *args, **kwargs)

    # les pièces jointes sont lues par Path.open
    monkeypatch.setattr(Path, "open", bad_open)

    with pytest.raises(OSError, match=r".+"), caplog.at_level(logging.ERROR, logger="send_email"):
        sender.create_message(["a@b.fr"], "s", "t", "<p>h</p>", {}, [attachment])


def test_send_message_succes(fake_sender_module):
    sender, service = fake_sender_module()

    result = sender.send_message(["a@b.fr"], "s", "t", "<p>h</p>", {})

    assert result == EmailResult(success=True, message_id="msg-1", recipient="a@b.fr")
    assert service.sent[0][0] == "me"


def test_send_message_erreur_creation(fake_sender_module):
    sender, _ = fake_sender_module()

    result = sender.send_message(["a@b.fr"], "s {absent}", "t", "<p>h</p>", {})

    assert result.success is False
    assert "création du message" in result.error


def test_send_message_http_recuperable_puis_succes(fake_sender_module, caplog):
    sender, _ = fake_sender_module(outcomes=[http_error(429), http_error(503)])

    with caplog.at_level(logging.WARNING, logger="send_email"):
        result = sender.send_message(["a@b.fr"], "s", "t", "<p>h</p>", {})

    assert result.success is True
    assert caplog.text.count("nouvelle tentative") == 2


def test_send_message_http_non_recuperable(fake_sender_module):
    sender, _ = fake_sender_module(outcomes=[http_error(400)])

    result = sender.send_message(["a@b.fr"], "s", "t", "<p>h</p>", {})

    assert result.success is False
    assert "non récupérable 400" in result.error


def test_send_message_toutes_tentatives_echouees(fake_sender_module, caplog):
    """Erreurs SSL : le service est réinitialisé, puis échec après le nombre max de tentatives"""
    sender, service = fake_sender_module(
        outcomes=[OSError("EOF occurred"), OSError("ssl error"), OSError("autre")]
    )
    resets = []
    sender._reset_service = lambda: resets.append(1)  # pylint: disable=W0212

    with caplog.at_level(logging.ERROR, logger="send_email"):
        result = sender.send_message(["a@b.fr"], "s", "t", "<p>h</p>", {})

    assert result.success is False
    assert "Échec après 3 tentatives" in result.error
    assert len(resets) == 2
    assert len(service.sent) == 3


def test_reset_service(fake_sender_module):
    sender, service = fake_sender_module()
    sender.service = None

    sender._reset_service()  # pylint: disable=W0212

    assert sender.service is service


def test_send_mass_mail(fake_sender_module, make_sse_progress, tmp_path, caplog):
    sender, _ = fake_sender_module(outcomes=[{"id": "ok"}, http_error(400)])
    progress = make_sse_progress(total_items=3)
    attachment = tmp_path / "f.pdf"
    attachment.write_bytes(b"%PDF")
    email = ("s", "t", "<p>h</p>", {}, [attachment])

    with caplog.at_level(logging.INFO, logger="send_email"):
        nb_success, nb_errors, results = sender.send_mass_mail(
            [(["a@b.fr"], *email), (["c@d.fr"], *email), (["", None], *email)],
            job_id=progress.job_id,
        )

    assert (nb_success, nb_errors) == (1, 2)
    assert [result.success for result in results] == [True, False, False]
    assert results[2].error == "Aucun destinataire valide"
    progress.refresh_from_db()
    assert (progress.processed_items, progress.failed_items) == (2, 1)
    assert "Envoi terminé: 1 succès, 2 erreurs sur 3 emails" in caplog.text


def test_send_mass_mail_sans_jauge_et_progression(fake_sender_module, tmp_path, caplog):
    """50 emails sans job_id : pas de jauge, journal de progression tous les 50 envois"""
    sender, _ = fake_sender_module(outcomes=[http_error(400)])
    attachment = tmp_path / "f.pdf"
    attachment.write_bytes(b"%PDF")

    with caplog.at_level(logging.INFO, logger="send_email"):
        nb_success, nb_errors, _ = sender.send_mass_mail(
            [(["a@b.fr"], "s", "t", "<p>h</p>", {}, [attachment])] * 50
        )

    assert (nb_success, nb_errors) == (49, 1)
    assert "Progression: 50/50" in caplog.text


def test_send_mass_mail_sans_piece_jointe(fake_sender_module):
    """Sans pièce jointe (None) : l'email envoyé est compté une seule fois, en succès"""
    sender, _ = fake_sender_module(outcomes=[{"id": "ok"}])

    nb_success, nb_errors, results = sender.send_mass_mail(
        [(["a@b.fr"], "s", "t", "<p>h</p>", {}, None)]
    )

    assert (nb_success, nb_errors) == (1, 0)
    assert [result.success for result in results] == [True]


def test_send_mass_mail_suivi_en_erreur(fake_sender_module, make_sse_progress, monkeypatch, caplog):
    """La jauge ne peut pas être mise à jour : journalisé, le résultat de l'email est inchangé"""
    from apps.core.models import SSEProgress  # pylint: disable=C0415

    sender, _ = fake_sender_module(outcomes=[{"id": "ok"}])
    progress = make_sse_progress(total_items=1)

    def boom(self, **kwargs):
        raise RuntimeError("base indisponible")

    monkeypatch.setattr(SSEProgress, "update_progress", boom)

    with caplog.at_level(logging.ERROR, logger="send_email"):
        nb_success, nb_errors, results = sender.send_mass_mail(
            [(["a@b.fr"], "s", "t", "<p>h</p>", {}, [])], job_id=progress.job_id
        )

    assert (nb_success, nb_errors) == (1, 0)
    assert len(results) == 1
    assert "Suivi de l'envoi de l'email 1 non enregistré" in caplog.text


def test_send_mass_mail_vide_et_exception(fake_sender_module, caplog):
    sender, _ = fake_sender_module()

    assert sender.send_mass_mail([]) == (0, 0, [])

    with caplog.at_level(logging.ERROR, logger="send_email"):
        nb_success, nb_errors, results = sender.send_mass_mail([("tuple", "trop", "court")])

    assert (nb_success, nb_errors) == (0, 1)
    assert results[0].success is False


# TÂCHE celery_send_invoices_emails_gmail ==========================================================
class FakeMassSender:
    """Remplace le sender global des tâches : résultats programmés"""

    def __init__(self, results):
        self.results = results
        self.calls = []

    def send_mass_mail(self, email_list, job_id=None):
        self.calls.append((email_list, job_id))
        successes = sum(1 for result in self.results if result.success)
        return successes, len(self.results) - successes, self.results

    def send_message(self, *args):
        self.calls.append(args)
        return self.results[0]


@pytest.mark.usefixtures("email_template")
def test_launch_celery_send_invoice_mails_gmail(
    sale_for_email, make_user, make_sale_invoice, monkeypatch
):
    """Deux factures dans le même pdf global : un seul email ; résultat surnuméraire ignoré"""
    sale, _ = sale_for_email()
    second = make_sale_invoice(
        cct="AF0001",
        third_party_num="CLI001",
        printed=True,
        global_invoice_file="AF0001_global.pdf",
        invoice_month=INVOICE_MONTH,
    )
    user = make_user()
    fake = FakeMassSender(
        [
            EmailResult(success=True, message_id="m1", recipient="client@heron.local"),
            EmailResult(success=False, error="surnuméraire"),
        ]
    )
    monkeypatch.setattr(tasks_gmail, "sender", fake)

    result = tasks_gmail.launch_celery_send_invoice_mails_gmail(user.pk, "job")

    assert result == {"success": True, "sent": 1, "errors": 1, "total": 1}
    email_list, job_id = fake.calls[0]
    assert job_id == "job"
    assert email_list[0][0] == ["client@heron.local", "maison@heron.local"]
    assert email_list[0][1] == "Factures {periode}"
    assert email_list[0][4]["factures"].count("- Facture de") == 2
    sale.refresh_from_db()
    second.refresh_from_db()
    assert sale.send_email is True
    assert second.send_email is True
    trace = Trace.objects.get(flow_name="send_invoice_email_gmail")
    assert trace.errors is False
    assert trace.created_by == user


@pytest.mark.usefixtures("email_template")
def test_launch_celery_send_invoice_mails_gmail_par_cct_en_erreur(
    sale_for_email, make_user, monkeypatch
):
    sale, _ = sale_for_email()
    user = make_user()
    fake = FakeMassSender([EmailResult(success=False, error="quota", recipient="x")])
    monkeypatch.setattr(tasks_gmail, "sender", fake)

    result = tasks_gmail.launch_celery_send_invoice_mails_gmail(
        user.pk, "job", cct="AF0001", period=INVOICE_MONTH.isoformat()
    )

    assert result == {"success": True, "sent": 0, "errors": 1, "total": 1}
    sale.refresh_from_db()
    assert sale.send_email is False
    assert Trace.objects.get().errors is True


@pytest.mark.usefixtures("email_template")
def test_launch_celery_send_invoice_mails_gmail_sans_email(sale_for_email, make_user, email_dirs):
    """Fichier pdf absent : aucune donnée préparée, rien à envoyer"""
    sale_for_email()
    (email_dirs.sales / "AF0001_global.pdf").unlink()

    result = tasks_gmail.launch_celery_send_invoice_mails_gmail(make_user().pk, "job")

    assert result == {"success": True, "sent": 0, "errors": 0}


@pytest.mark.usefixtures("email_template")
def test_launch_celery_send_invoice_mails_gmail_exception(
    sale_for_email, make_user, monkeypatch, caplog
):
    sale_for_email()

    def boom(**kwargs):
        raise RuntimeError("gmail down")

    monkeypatch.setattr(tasks_gmail, "sender", types.SimpleNamespace(send_mass_mail=boom))

    with caplog.at_level(logging.ERROR, logger="send_email"):
        result = tasks_gmail.launch_celery_send_invoice_mails_gmail(make_user().pk, "job")

    assert result == {"success": False, "error": "gmail down"}


def test_prepare_invoice_email_data_sans_adresse(sale_for_email, caplog):
    _, context_dict = sale_for_email(emails=(), maison_email=None)

    with caplog.at_level(logging.WARNING, logger="send_email"):
        assert tasks_gmail.prepare_invoice_email_data(context_dict) is None

    assert "Pas d'adresses mail valides" in caplog.text


def test_send_invoice_email_gmail(sale_for_email, make_user, monkeypatch):
    sale, context_dict = sale_for_email()
    user = make_user()
    monkeypatch.setattr(
        tasks_gmail, "sender", FakeMassSender([EmailResult(success=True, message_id="m1")])
    )

    result = tasks_gmail.send_invoice_email_gmail(context_dict, user.pk)

    assert "cct : AF0001" in result["Envoi de la facture par mail : "]
    sale.refresh_from_db()
    assert sale.send_email is True
    assert Trace.objects.get().created_by == user


def test_send_invoice_email_gmail_date_et_echec(sale_for_email, make_user, monkeypatch):
    """invoice_month déjà une date, et résultat en échec"""
    sale, context_dict = sale_for_email()
    context_dict["invoice_month"] = INVOICE_MONTH
    monkeypatch.setattr(
        tasks_gmail, "sender", FakeMassSender([EmailResult(success=False, error="ko")])
    )

    tasks_gmail.send_invoice_email_gmail(context_dict, make_user().pk)

    sale.refresh_from_db()
    assert sale.send_email is False
    assert Trace.objects.get().errors is True

    context_dict["invoice_month"] = INVOICE_MONTH
    monkeypatch.setattr(
        tasks_gmail, "sender", FakeMassSender([EmailResult(success=True, message_id="m")])
    )
    tasks_gmail.send_invoice_email_gmail(
        context_dict, make_user(email="b@heron.local", username="b").pk
    )
    sale.refresh_from_db()
    assert sale.send_email is True


def test_send_invoice_email_gmail_sans_donnees_et_exception(
    sale_for_email, make_user, email_dirs, monkeypatch, caplog
):
    _, context_dict = sale_for_email()
    (email_dirs.sales / "AF0001_global.pdf").unlink()

    result = tasks_gmail.send_invoice_email_gmail(context_dict, make_user().pk)

    assert "cct : AF0001" in result["Envoi de la facture par mail : "]
    assert Trace.objects.count() == 0

    def boom(context):
        raise RuntimeError("boom")

    monkeypatch.setattr(tasks_gmail, "prepare_invoice_email_data", boom)

    with caplog.at_level(logging.ERROR, logger="send_email"):
        tasks_gmail.send_invoice_email_gmail(context_dict, 1)

    assert "Exception Générale: send_invoice_email_gmail" in caplog.text


# TÂCHE SSE ========================================================================================
@pytest.mark.usefixtures("email_template")
def test_task_sse_succes_et_echec(
    sale_for_email, make_user, make_maison, make_sale_invoice, monkeypatch, fake_tracker
):
    sale, _ = sale_for_email()
    make_sale_invoice(
        cct="AF0001",
        third_party_num="CLI001",
        printed=True,
        global_invoice_file="AF0001_global.pdf",
        invoice_month=INVOICE_MONTH,
    )
    make_maison("AF0002", third_party_num=sale.third_party_num, email="m2@heron.local")
    other = make_sale_invoice(
        cct="AF0002",
        third_party_num="CLI001",
        printed=True,
        global_invoice_file="AF0001_global.pdf",
        invoice_month=INVOICE_MONTH,
    )
    make_sale_invoice(
        cct="AF0003",
        third_party_num="CLI001",
        printed=True,
        global_invoice_file="absent.pdf",
        invoice_month=INVOICE_MONTH,
    )  # pdf absent : ignorée
    user = make_user()
    results = iter(
        [EmailResult(success=True, message_id="m1"), EmailResult(success=False, error="quota")]
    )
    monkeypatch.setattr(
        tasks_gmail_sse, "sender", types.SimpleNamespace(send_message=lambda *args: next(results))
    )

    result = tasks_gmail_sse.launch_celery_send_invoice_mails_gmail_sse(user.pk, job_id="job-sse")

    assert result["job_id"] == "job-sse"
    assert (result["sent"], result["errors"], result["total"]) == (1, 1, 2)
    sale.refresh_from_db()
    other.refresh_from_db()
    assert (sale.send_email, other.send_email) == (True, False)
    kinds = [event[0] for event in fake_tracker.events]
    assert kinds == ["start", "progress", "warning", "complete"]
    from apps.core.models import SSEProgress

    progress = SSEProgress.objects.get(job_id="job-sse")
    assert progress.status == "completed"
    assert progress.failed_items == 1


@pytest.mark.usefixtures("email_template")
def test_task_sse_suivi_en_erreur_apres_envoi(sale_for_email, make_user, monkeypatch, fake_tracker):
    """Email parti mais suivi non enregistré : compté une seule fois, en succès, avec avertissement"""
    sale_for_email()

    def boom(*args):
        raise RuntimeError("trace impossible")

    monkeypatch.setattr(
        tasks_gmail_sse,
        "sender",
        types.SimpleNamespace(
            send_message=lambda *args: EmailResult(success=True, message_id="m1")
        ),
    )
    monkeypatch.setattr(tasks_gmail_sse, "_record_sent", boom)

    result = tasks_gmail_sse.launch_celery_send_invoice_mails_gmail_sse(
        make_user().pk, job_id="job-suivi"
    )

    assert (result["sent"], result["errors"], result["total"]) == (1, 0, 1)
    warnings = [event for event in fake_tracker.events if event[0] == "warning"]
    assert len(warnings) == 1
    assert "envoyé, suivi incomplet" in warnings[0][1][0]


@pytest.mark.usefixtures("email_template")
def test_task_sse_exception_par_email_et_filtre_cct(
    sale_for_email, make_user, monkeypatch, fake_tracker
):
    sale_for_email()

    def boom(*args):
        raise RuntimeError("boom")

    monkeypatch.setattr(tasks_gmail_sse, "sender", types.SimpleNamespace(send_message=boom))

    result = tasks_gmail_sse.launch_celery_send_invoice_mails_gmail_sse(
        make_user().pk, cct="AF0001", period=INVOICE_MONTH.isoformat()
    )

    assert result["errors"] == 1
    assert result["success"] is True
    assert [event[0] for event in fake_tracker.events] == ["start", "warning", "complete"]


@pytest.mark.usefixtures("email_template", "fake_tracker")
def test_task_sse_rien_a_envoyer_et_erreur_globale(make_user, caplog):
    user = make_user()

    result = tasks_gmail_sse.launch_celery_send_invoice_mails_gmail_sse(user.pk)

    assert result["sent"] == 0
    assert "job_id" in result

    with caplog.at_level(logging.ERROR, logger="invoices_flux"):
        result = tasks_gmail_sse.launch_celery_send_invoice_mails_gmail_sse(999999)

    assert result["success"] is False
    assert "job_id" in result


@pytest.mark.usefixtures("email_template")
def test_task_sse_erreur_globale_avec_jauge(sale_for_email, make_user, monkeypatch, fake_tracker):
    """Erreur après création de la jauge : elle est marquée en échec et l'événement SSE envoyé"""
    sale_for_email()
    monkeypatch.setattr(
        tasks_gmail_sse,
        "sender",
        types.SimpleNamespace(send_message=lambda *a: EmailResult(success=True, message_id="m")),
    )

    def boom(self, *args, **kwargs):
        raise RuntimeError("sse down")

    monkeypatch.setattr(fake_tracker, "send_start", boom)

    result = tasks_gmail_sse.launch_celery_send_invoice_mails_gmail_sse(
        make_user().pk, job_id="job-ko"
    )

    assert result["success"] is False
    assert ("error", ("❌ Erreur critique : sse down",), {}) in fake_tracker.events
    from apps.core.models import SSEProgress

    assert SSEProgress.objects.get(job_id="job-ko").status == "failed"


def test_prepare_invoice_email_data_sse(sale_for_email, email_dirs, caplog):
    _, context_dict = sale_for_email()
    context_dict["invoice_month"] = INVOICE_MONTH

    data = tasks_gmail_sse.prepare_invoice_email_data(context_dict)

    assert data["mail_to"] == ["client@heron.local", "maison@heron.local"]
    assert data["email_tuple"][4]["periode"] == "JANVIER 2026"

    _, context_dict = sale_for_email(
        cct="AF0002", emails=(), maison_email=None, third_party_num="CLI002"
    )

    with caplog.at_level(logging.WARNING, logger="send_email"):
        assert tasks_gmail_sse.prepare_invoice_email_data(context_dict) is None

    (email_dirs.sales / "AF0002_global.pdf").unlink()
    assert tasks_gmail_sse.prepare_invoice_email_data(context_dict) is None


# VUES SSE =========================================================================================
@pytest.fixture
def render_recorder(monkeypatch):
    rendered = []
    monkeypatch.setattr(
        views_sse,
        "render",
        lambda request, template, context=None: (
            rendered.append((template, context)) or types.SimpleNamespace(status_code=200)
        ),
    )
    return rendered


def test_views_sse(make_user, monkeypatch, render_recorder):
    user = make_user()
    factory = RequestFactory()
    delayed = []
    monkeypatch.setattr(
        views_sse.launch_celery_send_invoice_mails_gmail_sse,
        "delay",
        lambda **kwargs: delayed.append(kwargs),
    )

    request = factory.get("/send/")
    request.user = user
    assert views_sse.send_invoices_emails_sse(request).status_code == 200
    assert render_recorder[0][0] == "invoices/send_invoices_sse.html"

    request = factory.post("/send/", {"cct": "AF0001", "period": "2026-01-01"})
    request.user = user
    response = views_sse.send_invoices_emails_sse(request)
    payload = json.loads(response.content)
    assert payload["success"] is True
    assert delayed == [
        {"user_pk": user.pk, "cct": "AF0001", "period": "2026-01-01", "job_id": payload["job_id"]}
    ]

    request = factory.get("/progress/")
    request.user = user
    assert views_sse.send_invoices_progress_sse(request, "job-1").status_code == 200
    assert render_recorder[1] == ("invoices/send_invoices_progress_sse.html", {"job_id": "job-1"})
