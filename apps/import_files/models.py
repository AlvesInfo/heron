import uuid

from django.db import models

from heron.models import DatesTable

HTML_COLORS = (("#FF0000", "red"), ("#00B050", "green"))


class ShaImportInvoicesFiles(DatesTable):
    uuid_identification = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    id_sha512_file = models.TextField()
    file_name = models.TextField(null=True, blank=True, max_length=255)


class ErrorsShaImportFIles(DatesTable):
    file_line = models.IntegerField(null=True)
    column = models.CharField(null=True, blank=True, max_length=80)
    value_on_error = models.CharField(null=True, blank=True, max_length=255)
    error = models.CharField(null=True, blank=True, max_length=80)
    expected_format = models.CharField(null=True, blank=True, max_length=80)
    html_error = models.TextField(null=True, blank=True)
    html_color = models.CharField(null=True, blank=True, choices=HTML_COLORS, max_length=7)
    sha_file = models.ForeignKey(ShaImportInvoicesFiles, on_delete=models.CASCADE, null=True)
