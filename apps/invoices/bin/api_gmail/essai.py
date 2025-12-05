from pathlib import Path
from apps.invoices.bin.api_gmail.sender import sender

file_path = Path("/Users/paulo/SitesWeb/heron/files/media/sales_invoices/AF0713_20250900047550.pdf")

# Envoi d'un seul email
result = sender.send_message(
    to=["paulo.alves@4a-info.fr"],
    subject="Votre facture {cct}",
    body_text="Texte brut",
    body_html="<h1>Votre facture</h1>",
    context={"cct": "CCT123"},
    attachments=[file_path]
)

if result.success:
    print(f"Email envoyé ! ID: {result.message_id}")
else:
    print(f"Erreur: {result.error}")

# Envoi en masse
email_list = [
    (["paulo.alves@4a-info.fr", "paulo@alves.ovh"], "Sujet", "Texte", "<html>", {}, [file_path]),
    (["paulo@alves-info.fr", "paulo@alves.ovh"], "Sujet", "Texte", "<html>", {}, [file_path]),
]

nb_success, nb_errors, results = sender.send_mass_mail(email_list)
print(f"Envoyés: {nb_success}, Erreurs: {nb_errors}")
