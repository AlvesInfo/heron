# pylint: disable=E0401,R0912,R0913,R0914,R0915,W0703,W1203
"""
FR : Module d'import des modèles de Sage X3
EN : Import module for Sage X3 models

Commentaire:

created at: 2022-05-10
created by: Paulo ALVES

modified at: 2022-05-10
modified by: Paulo ALVES
"""
from pathlib import Path

from django.utils import timezone

from apps.core.functions.functions_setups import settings
from apps.data_flux.make_inserts import make_insert
from apps.countries.models import Country
from apps.countries.forms.forms_djantic.sage import CountrySageSchema
from apps.countries.bin.countries_post_processing import pays_post_insert
from apps.data_flux.trace import get_trace

proccessing_dir = Path(settings.PROCESSING_SAGE_DIR)


def pays_sage(file_path: Path):
    """
    Import du fichier des Pays Sage X3
    :param file_path: Path du fichier à traiter
    """
    model = Country
    validator = CountrySageSchema
    file_name = file_path.name
    trace_name = "Mise à jour des Pays Sage"
    application_name = "countries_imports_import_sage"
    flow_name = "pays_sage"
    comment = f"import journalier {file_name} des Pays Sage"
    trace = get_trace(trace_name, file_name, application_name, flow_name, comment)
    params_dict_loader = {
        "trace": trace,
        "add_fields_dict": {},
    }
    to_print = make_insert(model, flow_name, file_path, trace, validator, params_dict_loader)
    pays_post_insert()
    return trace, to_print
