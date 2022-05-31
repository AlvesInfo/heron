# pylint: disable=E0401,R0903
"""
FR : Module des models pour l'import des fichiers
EN : Models module for importing files

Commentaire:

created at: 2021-11-07
created by: Paulo ALVES

modified at: 2021-11-07
modified by: Paulo ALVES
"""
import uuid

from django.db import models

from heron.models import DatesTable

HTML_COLORS = (("#FF0000", "red"), ("#00B050", "green"))


class ShaImportInvoicesFiles(DatesTable):
    """
    Tables de vérification des sha512 des fichiers de factures founisseurs déjà importés.
    FR : Table des Sha512
    EN : Sha512 Import Invoices Files table
    """

    id_sha512_file = models.TextField(unique=True)
    file_name = models.TextField(null=True, blank=True, max_length=255)

    # Identification
    uuid_identification = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)

    def __str__(self):
        """Texte renvoyé dans les selects et à l'affichage de l'objet"""
        return self.file_name

    class Meta:
        """class Meta du modèle django"""

        ordering = ["file_name"]


class ErrorsShaImportFIles(DatesTable):
    """
    Tables de stockage des erreurs sur les fichiers importés.
    FR : Table des erreurs des fichiers Sha512
    EN : Errors Sha512 Import FIles table
    """

    sha_file = models.ForeignKey(
        ShaImportInvoicesFiles,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        to_field="uuid_identification",
        related_name="sha_file_sha",
        db_column="sha_file",
    )
    file_line = models.IntegerField(null=True)
    column = models.CharField(null=True, blank=True, max_length=80)
    value_on_error = models.CharField(null=True, blank=True, max_length=255)
    error = models.CharField(null=True, blank=True, max_length=80)
    expected_format = models.CharField(null=True, blank=True, max_length=80)
    html_error = models.TextField(null=True, blank=True)
    html_color = models.CharField(null=True, blank=True, choices=HTML_COLORS, max_length=7)

    def __str__(self):
        """Texte renvoyé dans les selects et à l'affichage de l'objet"""
        return self.sha_file

    class Meta:
        """class Meta du modèle django"""

        ordering = ["sha_file", "file_line"]
