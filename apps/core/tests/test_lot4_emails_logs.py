# pylint: disable=E0401,W0621
"""
FR : Tests de l'envoi d'emails smtp signés DKIM (apps/core/bin/emails.py) et des logs par
     fichier ou par mail (apps/core/functions/functions_logs.py), sans réseau
EN : Tests for DKIM signed smtp emails and file / mail logs, without network

created at: 2026-10-11
created by: Paulo ALVES
"""
import smtplib
from email.mime.multipart import MIMEMultipart
from pathlib import Path

import pytest

from apps.core.bin import emails
from apps.core.exceptions import EmailException
from apps.core.functions import functions_logs
from conftest import patched_attrs


class FakeServer:
    """Serveur smtp factice : enregistre les appels"""

    def __init__(self, host=None, port=None):
        self.host = host
        self.port = port
        self.calls = []
        self.sent = []

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        self.calls.append("quit")

    def starttls(self):
        self.calls.append("starttls")

    def ehlo(self):
        self.calls.append("ehlo")

    def login(self, user, password):
        self.calls.append(("login", user, password))

    def sendmail(self, sender, recipients, message):
        self.sent.append((sender, recipients, message))

    def quit(self):
        self.calls.append("quit")


@pytest.fixture
def smtp(monkeypatch, tmp_path):
    """Serveur smtp, signature DKIM et fichier pem factices, constantes du module posées"""
    servers = []

    def _smtp(host, port):
        server = FakeServer(host, port)
        servers.append(server)
        return server

    def _sign(message, **_kwargs):
        assert b"From:" in message
        return b"DKIM-Signature: v=1; signature"

    (tmp_path / "env").mkdir()
    (tmp_path / "env" / "dkim.pem").write_text("CLE PRIVEE", encoding="utf8")

    with patched_attrs(monkeypatch, emails.smtplib, SMTP=_smtp), patched_attrs(monkeypatch, emails.dkim, sign=_sign), patched_attrs(
        monkeypatch,
        emails,
        EMAIL_HOST="smtp.test",
        EMAIL_PORT=587,
        EMAIL_HOST_USER="heron@test.local",
        EMAIL_HOST_PASSWORD="secret",
        DEFAULT_FROM_EMAIL="compta@test.local",
        ENV_ROOT=str(tmp_path / "env" / ".env"),
        DOMAIN="test.local",
        DKIM_PEM_FILE="dkim.pem",
    ):
        yield servers


def test_prepare_mail_interpole_le_contexte():
    """Sujet et html sont formatés avec le contexte, le texte brut est extrait du html"""
    message = MIMEMultipart()
    body = MIMEMultipart("alternative")

    emails.prepare_mail(message, body, "Facture {numero}", email_html="<p>Bonjour {nom}</p>", context={"numero": "F1", "nom": "Paul"})

    parts = body.get_payload()
    assert message["Subject"] == "Facture F1"
    assert message["From"] == emails.EMAIL_HOST_USER
    assert parts[0].get_payload() == "Bonjour Paul"
    assert parts[1].get_payload() == "<p>Bonjour Paul</p>"


def test_prepare_mail_sans_contexte():
    message = MIMEMultipart()
    body = MIMEMultipart("alternative")

    emails.prepare_mail(message, body, "Sujet", email_html="<b>Corps</b>")

    assert message["Subject"] == "Sujet"
    assert body.get_payload()[0].get_payload() == "Corps"


def test_send_mass_mail_sans_rien():
    assert emails.send_mass_mail() == {"Send invoices email : Il n'y a rien à envoyer"}
    assert emails.send_mass_mail([]) == {"Send invoices email : Il n'y a rien à envoyer"}


def test_send_mass_mail_envoie_signe_avec_pieces_jointes(smtp, tmp_path):
    """Connexion tls, authentification, un envoi par élément avec signature DKIM et pièces jointes"""
    attachment = tmp_path / "facture.pdf"
    attachment.write_bytes(b"%PDF")
    email_list = [
        (["client@test.local"], "Facture {numero}", "", "<p>Facture {numero}</p>", {"numero": "F1"}, [attachment]),
        (["a@test.local", "b@test.local"], "Relance", "", "<p>Relance</p>", {}, []),
    ]

    result = emails.send_mass_mail(email_list)

    server = smtp[0]
    assert result == {"Send invoices email : ", "2 ont été envoyés"}
    assert (server.host, server.port) == ("smtp.test", 587)
    assert server.calls[:2] == ["starttls", ("login", "heron@test.local", "secret")]
    assert server.calls[-1] == "quit"
    assert len(server.sent) == 2
    sender, recipients, raw = server.sent[0]
    assert (sender, recipients) == ("compta@test.local", ["client@test.local"])
    assert "Subject: Facture F1" in raw
    assert "DKIM-Signature: v=1; signature" in raw
    assert 'filename="facture.pdf"' in raw
    assert server.sent[1][2].count("To: a@test.local;b@test.local") == 1


def test_send_mass_mail_piece_jointe_illisible(smtp, tmp_path):
    """Un fichier joint absent provoque une EmailException qui cite le dernier élément"""
    email_list = [(["client@test.local"], "Sujet", "", "<p>x</p>", {}, [tmp_path / "absent.pdf"])]

    with pytest.raises(EmailException, match="absent.pdf"):
        emails.send_mass_mail(email_list)

    assert smtp[0].sent == []


def test_send_mass_mail_erreur_smtp(smtp, monkeypatch):
    def _refuse(*_args, **_kwargs):
        raise smtplib.SMTPException("refus")

    with patched_attrs(monkeypatch, emails.smtplib, SMTP=_refuse), pytest.raises(EmailException, match="send_mass_mail"):
        emails.send_mass_mail([(["client@test.local"], "Sujet", "", "<p>x</p>", {}, [])])

    assert smtp == []


# LOGS =============================================================================================


def test_write_log_cree_le_fichier_et_ajoute_les_lignes(tmp_path):
    log = tmp_path / "logs" / "mise_a_jour.log"
    log.parent.mkdir()

    functions_logs.write_log(str(log), "première\n")
    functions_logs.write_log(str(log), "seconde\n")
    functions_logs.write_log(str(log), None)
    functions_logs.write_log(None, "ignorée\n")

    assert log.read_text(encoding="utf-8") == "première\nseconde\n"
    assert Path(functions_logs.LOG_FILE).name == "log_mise_a_jour.log"
    assert Path(functions_logs.LOG_FILE_DIVERS).name == "log_divers.log"


@pytest.mark.parametrize(
    ("use_ssl", "use_tls", "expected_class", "expected_calls"),
    [
        (True, False, "SMTP_SSL", ["ehlo", ("login", "heron@test.local", "secret"), "quit"]),
        (False, True, "SMTP", ["starttls", "ehlo", ("login", "heron@test.local", "secret"), "quit"]),
        (False, False, "SMTP", ["starttls", "ehlo", ("login", "heron@test.local", "secret"), "quit"]),
    ],
)
def test_envoi_mail_erreur(settings, monkeypatch, use_ssl, use_tls, expected_class, expected_calls):
    """Connexion ssl ou tls selon les réglages, sujet par défaut ou fourni"""
    settings.EMAIL_HOST = "smtp.test"
    settings.EMAIL_PORT = 465
    settings.EMAIL_HOST_USER = "heron@test.local"
    settings.EMAIL_HOST_PASSWORD = "secret"
    settings.EMAIL_USE_SSL = use_ssl
    settings.EMAIL_USE_TLS = use_tls
    created = {}

    def _factory(name):
        def _make(host, port):
            created["class"] = name
            created["server"] = FakeServer(host, port)
            return created["server"]

        return _make

    with patched_attrs(monkeypatch, functions_logs.smtplib, SMTP=_factory("SMTP"), SMTP_SSL=_factory("SMTP_SSL")):
        functions_logs.envoi_mail_erreur("une erreur", None if use_ssl else "Sujet erreur")

    server = created["server"]
    assert created["class"] == expected_class
    assert (server.host, server.port) == ("smtp.test", 465)
    assert server.calls == expected_calls
    sender, recipient, raw = server.sent[0]
    assert (sender, recipient) == ("heron@test.local", "heron@test.local")
    assert ("Subject: Erreur B.I" if use_ssl else "Subject: Sujet erreur") in raw
    assert "une erreur" in raw
