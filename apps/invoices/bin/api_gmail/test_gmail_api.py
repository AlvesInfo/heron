# pylint: disable=E0401
"""
FR : Script de test pour l'API Gmail
EN : Test script for Gmail API

Commentaire:
Ce script permet de tester l'envoi d'emails via l'API Gmail
sans passer par Django ou Celery.

Usage:
    python test_gmail_api.py

created at: 2025-01-10
created by: Paulo ALVES 
"""

import os
import sys
import platform
from pathlib import Path

# Configuration du path Django
BASE_DIR = r"/"

if platform.uname().node not in ["PauloMSI", "MSI"]:
    BASE_DIR = "/home/paulo/heron"

sys.path.append(BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "heron.settings")

import django

django.setup()

from apps.invoices.bin.api_gmail.config import config
from apps.invoices.bin.api_gmail.auth import authenticator
from apps.invoices.bin.api_gmail.sender import sender


def test_configuration():
    """Teste la configuration"""
    print("=" * 80)
    print("TEST DE LA CONFIGURATION")
    print("=" * 80)

    try:
        print(f"✓ Fichier de configuration trouvé: {config.config_file}")
        print(f"✓ Client ID: {config.oauth2_client_id[:20]}...")
        print(f"✓ Email expéditeur: {config.sender_email}")
        print(f"✓ Rate limit: {config.max_per_second} emails/seconde")
        print(f"✓ Batch size: {config.batch_size}")
        print(f"✓ Max retries: {config.max_retries}")
        print("\n✅ Configuration OK\n")
        return True
    except Exception as error:
        print(f"\n❌ Erreur de configuration: {error}\n")
        return False


def test_authentication():
    """Teste l'authentification OAuth2"""
    print("=" * 80)
    print("TEST DE L'AUTHENTIFICATION")
    print("=" * 80)

    try:
        print("Tentative d'authentification...")
        creds = authenticator.get_credentials()

        if creds and creds.valid:
            print(f"✓ Credentials valides")
            print(f"✓ Token file: {config.token_file_path}")
            print(f"✓ Scopes: {', '.join(config.scopes)}")
            print("\n✅ Authentification OK\n")
            return True
        else:
            print("\n❌ Credentials invalides\n")
            return False
    except Exception as error:
        print(f"\n❌ Erreur d'authentification: {error}\n")
        return False


def test_gmail_service():
    """Teste la création du service Gmail"""
    print("=" * 80)
    print("TEST DU SERVICE GMAIL API")
    print("=" * 80)

    try:
        print("Création du service Gmail API...")
        service = authenticator.get_gmail_service()

        if service:
            print(f"✓ Service Gmail créé")
            print(f"✓ Type: {type(service)}")

            # Teste une requête simple
            print("\nTest d'une requête simple (get profile)...")
            profile = service.users().getProfile(userId="me").execute()
            print(f"✓ Email du profil: {profile.get('emailAddress')}")
            print(f"✓ Messages totaux: {profile.get('messagesTotal', 0)}")
            print(f"✓ Threads totaux: {profile.get('threadsTotal', 0)}")

            print("\n✅ Service Gmail OK\n")
            return True
        else:
            print("\n❌ Impossible de créer le service\n")
            return False
    except Exception as error:
        print(f"\n❌ Erreur lors de la création du service: {error}\n")
        return False


def test_send_test_email():
    """Envoie un email de test"""
    print("=" * 80)
    print("TEST D'ENVOI D'EMAIL")
    print("=" * 80)

    # Email de test (modifiez cette adresse)
    test_email = input(
        "Entrez une adresse email de test (ou appuyez sur Entrée pour ignorer): "
    ).strip()

    if not test_email:
        print("❌ Test d'envoi ignoré\n")
        return False

    try:
        print(f"\nEnvoi d'un email de test à {test_email}...")

        result = sender.send_message(
            to=[test_email],
            subject="Test API Gmail - Heron Invoices",
            body_text="Ceci est un email de test",
            body_html="""
            <html>
            <body>
                <h1>Test API Gmail</h1>
                <p>Ceci est un email de test envoyé depuis le module API Gmail.</p>
                <p><strong>Si vous recevez cet email, la configuration fonctionne correctement !</strong></p>
                <hr>
                <p style="color: gray; font-size: 10pt;">
                    Envoyé depuis Heron - Module API Gmail
                </p>
            </body>
            </html>
            """,
            context={},
            attachments=None,
        )

        if result.success:
            print(f"\n✅ Email envoyé avec succès !")
            print(f"   Message ID: {result.message_id}")
            print(f"   Destinataire: {result.recipient}")
            print("\n⚠️  Vérifiez votre boîte email (et le dossier spam !)\n")
            return True
        else:
            print(f"\n❌ Échec de l'envoi: {result.error}\n")
            return False

    except Exception as error:
        print(f"\n❌ Erreur lors de l'envoi: {error}\n")
        return False


def main():
    """Fonction principale"""
    print("\n" + "=" * 80)
    print(" " * 20 + "TEST DU MODULE API GMAIL")
    print("=" * 80 + "\n")

    results = {
        "Configuration": test_configuration(),
        "Authentification": test_authentication(),
        "Service Gmail": test_gmail_service(),
    }

    # Si tout est OK, propose d'envoyer un email de test
    if all(results.values()):
        print("\n" + "=" * 80)
        print("✅ TOUS LES TESTS DE BASE SONT PASSÉS !")
        print("=" * 80 + "\n")

        test_send = input("Voulez-vous envoyer un email de test ? (o/N): ").strip().lower()
        if test_send in ["o", "oui", "y", "yes"]:
            results["Envoi d'email"] = test_send_test_email()
    else:
        print("\n" + "=" * 80)
        print("❌ CERTAINS TESTS ONT ÉCHOUÉ")
        print("=" * 80 + "\n")

    # Résumé
    print("\n" + "=" * 80)
    print("RÉSUMÉ DES TESTS")
    print("=" * 80)
    for test_name, test_result in results.items():
        status = "✅ OK" if test_result else "❌ ÉCHEC"
        print(f"{test_name:.<40} {status}")

    print("=" * 80 + "\n")

    if all(results.values()):
        print("🎉 TOUS LES TESTS SONT PASSÉS ! Vous pouvez utiliser le module en production.\n")
    else:
        print("⚠️  CERTAINS TESTS ONT ÉCHOUÉ. Vérifiez la configuration et les logs.\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrompus par l'utilisateur\n")
    except Exception as error:
        print(f"\n\n❌ Erreur fatale: {error}\n")
        raise