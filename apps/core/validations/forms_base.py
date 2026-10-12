"""FR: Formulaires django à hériter pour validation.

EN: Django forms to Inherit for validation
for django verions == 1.11 | 2.0 | 2.1 | 2.2 | 3.2
    author: Paulo ALVES
    created at: 2022-03-11
    modified at: 2022-03-11
    version : 0.02.
"""

from django import forms
from django.utils import timezone


class TruncatedTextField(forms.CharField):
    """FR: forms.field qui tronque le texte à la longueur du max_lenght du modèle.

    EN: forms.field which truncates the text to the length of the max_lenght of the model.
    """

    def clean(self, value):
        """FR: Troncature de texte avant méthode propre.

            :param value: valeur à valider
            :return: méthode Clean
        EN: text truncation before clean method
            :param value: value to validate
            :return: Clean method.
        """
        value = "" if value is None else value[: self.max_length]

        return super().clean(value)


class TildeTextField(forms.CharField):
    """FR: forms.field qui récupère le premier élément du texte splité sur les ~~.

    EN: forms.field which retrieves the first element of the split text on the ~~.
    """

    def clean(self, value):
        """FR: Troncature de texte avant méthode propre.

            :param value: valeur à valider
            :return: méthode Clean
        EN: text truncation before clean method
            :param value: value to validate
            :return: Clean method.
        """
        if isinstance(value, (str,)):
            value = "" if value is None else value.split("~~")[0]

        return super().clean(value)


class FrenchBooleanField(forms.BooleanField):
    """FR: forms.field valide les booléens français.

    EN: forms.field wich velidate frenh boolean.
    """

    def clean(self, value):
        """FR: booléens méthode propre.

            :param value: valeur à valider
            :return: méthode Clean
        EN: frenh boolean clean method
            :param value: value to validate
            :return: Clean method.
        """
        if str(value).lower() in {"true", "1", "yes", "oui", "vrai"}:
            value = "true"
        elif str(value).lower() in {"False", "false", "0", "", "non", "faux"}:
            value = "false"
        else:
            value = "false"

        return super().clean(value)


class FrenchNullBooleanField(forms.BooleanField):
    """FR: forms.field valide les booléens français.

    EN: forms.field wich velidate frenh boolean.
    """

    def clean(self, value):
        """FR: booléens méthode propre.

            :param value: valeur à valider
            :return: méthode Clean
        EN: frenh boolean clean method
            :param value: value to validate
            :return: Clean method.
        """
        if str(value).lower() in {"true", "1", "yes", "oui", "vrai"}:
            value = "true"
        elif str(value).lower() in {"False", "false", "0", "non", "faux"}:
            value = "false"
        else:
            value = None

        return super().clean(value)


class SageNullBooleanField(forms.NullBooleanField):
    """FR: forms.field valide les booléens pour Sage (2 = vrai, 1 = faux, sinon null).

        Le widget TextInput transmet la valeur brute du fichier Sage à clean() ; avec le
        CheckboxInput de BooleanField, "2" était converti en bool avant clean() et le champ
        ne pouvait jamais être valide.
    EN: forms.field wich velidate for Sage boolean (2 = true, 1 = false, else null).
    """

    widget = forms.TextInput

    def __init__(self, *args, **kwargs):
        # Champ nullable : non requis par défaut, sinon le ModelForm valide le None contre
        # blank=False du champ de modèle ("Ce champ ne peut pas être vide")
        """Rend le champ facultatif par défaut (champ nullable)."""
        kwargs.setdefault("required", False)
        super().__init__(*args, **kwargs)

    def clean(self, value):
        """FR: booléens méthode propre.

            :param value: valeur à valider
            :return: méthode Clean
        EN: frenh boolean clean method
            :param value: value to validate
            :return: Clean method.
        """
        str_value = str(value).strip().lower()

        if str_value in {"2", "2.0"}:
            value = True
        elif str_value in {"1", "1.0"}:
            value = False
        else:
            value = None

        return super().clean(value)


class NullZeroDecimalField(forms.DecimalField):
    """FR: forms.field qui renvoie 0 si le champ est vide.

    EN: forms.field which returns 0 if the field is empty.
    """

    def clean(self, value):
        """FR: Remplace la valeur par 0 si la valeur est nulle.

            :param value: valeur à valider
            :return: method clean 0
        EN: Replace value to 0 if value is null
            :param value: value to validate
            :return: Clean method.
        """
        # Valeur absente, None ou vide -> "0" ; les nombres déjà typés sont normalisés en texte
        new_value = "0" if value in (None, "") else str(value)

        if "." in new_value and "," in new_value:
            # le premier séparateur rencontré est celui des milliers : il est retiré
            thousands = "," if new_value.index(",") < new_value.index(".") else "."
            new_value = new_value.replace(thousands, "")

        new_value = new_value.replace(",", ".")

        return super().clean(new_value)


class DefaultDateTodayField(forms.DateField):
    """FR: forms.field qui renvoie la date du jour si la date est vide.

    EN: forms.field which returns date of day if the field is empty.
    """

    def clean(self, _value):
        """FR: Remplace par la date du jour si le champ est vide.

            :param value: valeur à valider
            :return: method clean date du jour au format iso
        EN: Replace value to date of day if value is null
            :param value: value to validate
            :return: Clean method date today iso-format.
        """
        new_value = timezone.localdate().isoformat()

        return super().clean(new_value)


class DefaultDateField(forms.DateField):
    """FR: forms.field qui renvoie la date 01/01/2000 (date générique) si la date est vide.

    EN: forms.field which returns 2000-01-01 if the field is empty.
    """

    def clean(self, _value):
        """FR: Remplace par la date 01/01/2000 si le champ est vide.

            :param value: valeur à valider
            :return: method clean date 01/01/2000 au format iso
        EN: Replace value to date 2000-01-01 if value is null
            :param value: value to validate
            :return: Clean method date "2000-01-01" iso-format.
        """
        new_value = "2000-01-01"

        return super().clean(new_value)
