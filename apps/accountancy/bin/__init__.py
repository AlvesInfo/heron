# import base64
# from email.mime.text import MIMEText
# from email.mime.multipart import MIMEMultipart
# from email.mime.base import MIMEBase
# from email import encoders
# from googleapiclient.discovery import build
# from google.oauth2.credentials import Credentials
# from googleapiclient.errors import HttpError
#
#
# def create_html_message_with_attachment(sender, to, subject, html_content, file_path):
#     try:
#         # Créez le message principal
#         message = MIMEMultipart('mixed')  # Type 'mixed' pour inclure des pièces jointes
#         message['to'] = to
#         message['from'] = sender
#         message['subject'] = subject
#
#         # Ajoutez le contenu HTML
#         msg_html = MIMEText(html_content, 'html')
#         message.attach(msg_html)
#
#         # Ajoutez la pièce jointe
#         try:
#             with open(file_path, 'rb') as f:
#                 attachment = MIMEBase('application', 'octet-stream')
#                 attachment.set_payload(f.read())
#         except FileNotFoundError:
#             print(f"Erreur : Le fichier '{file_path}' est introuvable.")
#             return None
#         except Exception as e:
#             print(f"Erreur inattendue lors de la lecture du fichier : {e}")
#             return None
#
#         # Encodez la pièce jointe en base64
#         encoders.encode_base64(attachment)
#         attachment.add_header(
#             'Content-Disposition',
#             f'attachment; filename={file_path.split("/")[-1]}',
#         )
#         message.attach(attachment)
#
#         # Encodez tout le message en base64url
#         raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
#         return {'raw': raw_message}
#
#     except Exception as e:
#         print(f"Erreur lors de la création du message : {e}")
#         return None
#
#
# def send_email_with_html_and_attachment():
#     try:
#         # Remplacez par vos informations d'identification OAuth2
#         creds = None
#         try:
#             creds = Credentials('AIzaSyDcDV19Kbo-5Y-LeeVbbZmwtmsWpd8vIfg')
#         except Exception as e:
#             print("Erreur lors de l'initialisation des informations d'identification OAuth2 :", e)
#             return
#
#         try:
#             service = build('gmail', 'v1', credentials=creds)
#         except Exception as e:
#             print("Erreur lors de la création du service Gmail :", e)
#             return
#
#         # Définissez les détails du message
#         sender = "comptabilite@acuitis.com"
#         to = "paulo@alves.ovh;paulo.alves@4a-info.fr"
#         subject = "E-mail HTML avec pièce jointe"
#         html_content = """
#         <html>
#             <body>
#                 <h1 style="color:blue;">Bonjour !</h1>
#                 <p>Ceci est un e-mail au format <b>HTML</b> avec une pièce jointe.</p>
#                 <p>Voici un <a href='https://www.example.com'>lien</a>.</p>
#             </body>
#         </html>
#         """
#         file_path = "/Users/paulo/Downloads/Classeur2.pdf"  # Chemin complet du fichier à envoyer
#
#         # Créez le message HTML avec pièce jointe
#         message = create_html_message_with_attachment(sender, to, subject, html_content, file_path)
#         if message is None:
#             print("Message non créé en raison d'une erreur.")
#             return
#
#         # Envoyez le message
#         try:
#             sent_message = service.users().messages().send(userId='me', body=message).execute()
#             print(f"Message envoyé avec succès, ID : {sent_message['id']}")
#         except HttpError as error:
#             print(f"Erreur HTTP lors de l'envoi de l'e-mail : {error}")
#         except Exception as e:
#             print(f"Erreur inattendue lors de l'envoi de l'e-mail : {e}")
#
#     except Exception as e:
#         print(f"Erreur globale dans le programme : {e}")
#
#
# if __name__ == '__main__':
#     # Exécuter la fonction
#     send_email_with_html_and_attachment()