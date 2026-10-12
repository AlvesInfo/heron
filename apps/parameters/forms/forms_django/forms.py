"""FR : Module pour le typage de champs.

EN : Module for field typing.

Commentaire:

created at: 2023-01-17
created by: Paulo ALVES

modified at: 2023-01-17
modified by: Paulo ALVES
"""

from django.forms.widgets import TextInput


class NumberInput(TextInput):
    """Widget de saisie numérique."""

    input_type = "number"
