# pylint: disable=E0401,R0912,R0913,R0914,R0915,W0703,W1203
"""
FR : Module d'import des modèles de Sage X3
EN : Import module for Sage X3 models

Commentaire:

created at: 2022-04-08
created by: Paulo ALVES

modified at: 2022-04-08
modified by: Paulo ALVES
"""

from pathlib import Path

from django.utils import timezone

from apps.core.functions.functions_setups import settings
from apps.data_flux.make_inserts import make_insert
from apps.od.models import ModelOd
from apps.od.forms.forms_djantic.djantic_od import OdSchema
from apps.data_flux.trace import get_trace

proccessing_dir = Path(settings.PROCESSING_OD_A_PASSER)


def import_od_a_passer(file_path: Path):
    """
    Import du fichier des comptes comptable Sage X3
    :param file_path: Path du fichier à traiter
    """
    model = ModelOd
    validator = OdSchema
    file_name = file_path.name
    trace_name = "Mise à jour Comptes Sage"
    application_name = "accountacy_imports_import_sage"
    flow_name = "AccountSage"
    comment = f"import journalier {file_name} des Comptes comptables Sage"
    trace = get_trace(trace_name, file_name, application_name, flow_name, comment)
    params_dict_loader = {
        "trace": trace,
        "add_fields_dict": {
            "created_at": timezone.now(),
            "modified_at": timezone.now(),
        },
    }
    to_print = make_insert(
        model, flow_name, file_path, trace, validator, params_dict_loader
    )

    return trace, to_print


def import_od_files():
    """Boucle d'import des fichiers pour générer les od"""
    for file_path in proccessing_dir.glob("*.csv"):
        print(file_path)


if __name__ == "__main__":
    import_od_files()
