"""FR : Module de validation par djantic des factures founisseurs.

EN : Sage X3 import validation forms module for suppliers invoices.

Commentaire:

Les schémas djantic ont besoin, à leur création, de la liste des colonnes du flux
(table edi.ColumnDefinition). Ils ne sont donc plus déclarés à l'import du module, ce qui
interdisait de charger l'URLconf sur une base vide, mais construits à la demande par
``get_schema(name)`` et mis en cache pour le processus.

created at: 2022-04-06
created by: Paulo ALVES

modified at: 2026-10-10
modified by: Paulo ALVES
"""

import datetime
import functools
import uuid
from collections.abc import Iterable
from decimal import Decimal
from typing import Any, NamedTuple

from django.core.exceptions import ImproperlyConfigured
from djantic import ModelSchema
from pydantic import BaseModel, validator

from apps.core.validations.pydantic_validators_base import (
    TvaEyeConfor,
    TvaGenerique,
    TvaInterson,
    TvaNewson,
    TvaWidex,
    ValidateFieldsBase,
)
from apps.edi.models import ColumnDefinition, EdiImport
from apps.edi.parameters.invoices_imports import get_columns

# Date sentinelle « sans date » des flux Sage : naïve à dessein (écrite telle quelle dans les colonnes date)
DEFAULT_DATE = datetime.datetime(1900, 1, 1)  # noqa: DTZ001

# Colonnes ajoutées par le loader (params_dict_loader["add_fields_dict"]) à chaque flux
BASE_COLUMNS = ["uuid_identification", "flow_name", "created_at", "modified_at"]
SUPPLIER_COLUMNS = [*BASE_COLUMNS[:2], "supplier", *BASE_COLUMNS[2:]]
SUPPLIER_IDENT_COLUMNS = [*BASE_COLUMNS[:2], "supplier", "supplier_ident", *BASE_COLUMNS[2:]]

SUPPLIER_FIELDS = {"uuid_identification": uuid.UUID, "supplier": str}
SUPPLIER_IDENT_FIELDS = {**SUPPLIER_FIELDS, "supplier_ident": str}


class SchemaDefinition(NamedTuple):
    """Description déclarative d'un schéma djantic de flux fournisseur."""

    flow_name: str
    fields: dict[str, Any]
    extra_columns: Iterable[str]
    mixins: tuple[type[BaseModel], ...] = ()
    defaults: dict[str, Any] = {}
    default_date_fields: tuple[str, ...] = ()
    doc: str = ""


def default_date(value):
    """Valeur par défaut des dates vides ou "None" issues des fichiers."""
    if not value or value == "None":
        return DEFAULT_DATE

    return value


SCHEMA_DEFINITIONS: dict[str, SchemaDefinition] = {
    "BbgrBulkSchema": SchemaDefinition(
        "BbgrBulk", SUPPLIER_IDENT_FIELDS, SUPPLIER_IDENT_COLUMNS, (TvaWidex,), doc="BbgrBulk"
    ),
    "CosiumSchema": SchemaDefinition(
        "Cosium", {"uuid_identification": uuid.UUID}, SUPPLIER_COLUMNS, (TvaWidex,), doc="Cosium"
    ),
    "CosiumTransfertSchema": SchemaDefinition(
        "Transfert",
        {"acuitis_order_date": datetime.datetime, "uuid_identification": uuid.UUID},
        SUPPLIER_COLUMNS,
        default_date_fields=("acuitis_order_date",),
        doc="Transfert Cosium",
    ),
    "EdiSchema": SchemaDefinition(
        "Edi",
        {
            "uuid_identification": uuid.UUID,
            "qty": Decimal,
            "acuitis_order_date": datetime.datetime,
            "delivery_date": datetime.datetime,
        },
        BASE_COLUMNS,
        defaults={"qty": 1},
        default_date_fields=("acuitis_order_date", "delivery_date"),
        doc="Edi",
    ),
    "EyeConfortSchema": SchemaDefinition(
        "EyeConfort",
        SUPPLIER_IDENT_FIELDS,
        SUPPLIER_IDENT_COLUMNS,
        (TvaEyeConfor,),
        doc="Eye_confort",
    ),
    "GeneriqueSchema": SchemaDefinition(
        "Generique",
        {
            "uuid_identification": uuid.UUID,
            "acuitis_order_date": datetime.datetime,
            "delivery_date": datetime.datetime,
        },
        BASE_COLUMNS,
        (TvaGenerique,),
        default_date_fields=("acuitis_order_date", "delivery_date"),
        doc="Generique",
    ),
    "HearingSchema": SchemaDefinition(
        "Hearing", SUPPLIER_IDENT_FIELDS, SUPPLIER_IDENT_COLUMNS, (TvaGenerique,), doc="Hearing"
    ),
    "IntersonSchema": SchemaDefinition(
        "Interson", SUPPLIER_IDENT_FIELDS, SUPPLIER_IDENT_COLUMNS, (TvaInterson,), doc="Interson"
    ),
    "JohnsonSchema": SchemaDefinition(
        "Johnson",
        {**SUPPLIER_IDENT_FIELDS, "delivery_date": datetime.datetime},
        SUPPLIER_IDENT_COLUMNS,
        default_date_fields=("delivery_date",),
        doc="Johnson",
    ),
    "LmcSchema": SchemaDefinition("Lmc", SUPPLIER_IDENT_FIELDS, SUPPLIER_IDENT_COLUMNS, doc="Lmc"),
    "NewsonSchema": SchemaDefinition(
        "Newson", SUPPLIER_IDENT_FIELDS, SUPPLIER_IDENT_COLUMNS, (TvaNewson,), doc="Newson"
    ),
    "PhonakSchema": SchemaDefinition(
        "Phonak", SUPPLIER_IDENT_FIELDS, SUPPLIER_IDENT_COLUMNS, (TvaGenerique,), doc="Phonak"
    ),
    "HansatonSchema": SchemaDefinition(
        "Hansaton",
        SUPPLIER_IDENT_FIELDS,
        SUPPLIER_IDENT_COLUMNS,
        (TvaGenerique,),
        doc="Hansaton. Reprise de la fonction de Phonack, car faisant parti du même groupe",
    ),
    "ProditionSchema": SchemaDefinition(
        "Prodition",
        SUPPLIER_IDENT_FIELDS,
        SUPPLIER_IDENT_COLUMNS,
        (TvaGenerique,),
        doc="Prodition",
    ),
    "SigniaSchema": SchemaDefinition(
        "Signia",
        {**SUPPLIER_IDENT_FIELDS, "delivery_date": datetime.datetime},
        SUPPLIER_IDENT_COLUMNS,
        (TvaWidex,),
        default_date_fields=("delivery_date",),
        doc="Signia",
    ),
    "StarkeySchema": SchemaDefinition(
        "Starkey",
        {**SUPPLIER_IDENT_FIELDS, "delivery_date": datetime.datetime},
        SUPPLIER_IDENT_COLUMNS,
        (TvaGenerique,),
        default_date_fields=("delivery_date",),
        doc="Starkey",
    ),
    "TechnidisSchema": SchemaDefinition(
        "Technidis", SUPPLIER_IDENT_FIELDS, SUPPLIER_IDENT_COLUMNS, (TvaWidex,), doc="Technidis"
    ),
    "UnitronSchema": SchemaDefinition(
        "Unitron", SUPPLIER_IDENT_FIELDS, SUPPLIER_IDENT_COLUMNS, (TvaGenerique,), doc="Unitron"
    ),
    "WidexSchema": SchemaDefinition(
        "Widex", SUPPLIER_IDENT_FIELDS, SUPPLIER_IDENT_COLUMNS, (TvaWidex,), doc="Widex"
    ),
    "WsauSchema": SchemaDefinition(
        "Wsau", SUPPLIER_FIELDS, SUPPLIER_COLUMNS, (TvaWidex,), doc="Wsau"
    ),
    "WidexGaSchema": SchemaDefinition(
        "WidexGa", SUPPLIER_IDENT_FIELDS, SUPPLIER_IDENT_COLUMNS, (TvaWidex,), doc="WidexGa"
    ),
    "ZBuRefacSageSchema": SchemaDefinition(
        "Zburefac",
        {
            "uuid_identification": uuid.UUID,
            "flow_name": str,
            "supplier": str,
            "supplier_ident": str,
            "unit_weight": int,
            "axe_bu": uuid.UUID,
            "axe_prj": uuid.UUID,
            "axe_pro": uuid.UUID,
            "axe_pys": uuid.UUID,
            "axe_rfa": uuid.UUID,
            "vat": str,
        },
        SUPPLIER_IDENT_COLUMNS,
        defaults={
            "flow_name": "SageYoozRefac",
            "supplier": "SAGE_YOOZ_REFAC",
            "supplier_ident": "Zburefac",
        },
        doc="Refacturation Sage Yooz (ZBuRefac)",
    ),
}


def build_schema(name: str, definition: SchemaDefinition) -> type[ModelSchema]:
    """Construit le schéma djantic d'un flux, les colonnes du fichier étant lues en base.

    :param name: nom de la classe à construire
    :param definition: description du schéma
    :return: classe djantic.
    """
    columns = list(get_columns(ColumnDefinition, definition.flow_name))

    if not columns:
        raise ImproperlyConfigured(
            f"Aucune ligne edi.ColumnDefinition pour le flux {definition.flow_name!r} : "
            f"le schéma {name} ne peut pas être construit"
        )

    config = type(
        "Config",
        (),
        {"model": EdiImport, "include": columns + list(definition.extra_columns)},
    )
    namespace = {
        "__module__": __name__,
        "__qualname__": name,
        "__doc__": f"Schema Djantic pour validation du modèle {definition.doc or name}",
        "__annotations__": dict(definition.fields),
        "Config": config,
        **definition.defaults,
    }

    # allow_reuse : la même fonction sert à plusieurs champs et plusieurs schémas
    for field_name in definition.default_date_fields:
        namespace[f"check_{field_name}"] = validator(field_name, pre=True, allow_reuse=True)(
            default_date
        )

    return type(name, (ModelSchema, ValidateFieldsBase, *definition.mixins), namespace)


@functools.cache
def get_schema(name: str) -> type[ModelSchema]:
    """Renvoie le schéma djantic demandé, construit au premier appel puis conservé en cache.

    :param name: nom du schéma, ex. "WidexSchema"
    :return: classe djantic.
    """
    try:
        definition = SCHEMA_DEFINITIONS[name]
    except KeyError as error:
        raise KeyError(
            f"Schéma {name!r} inconnu, schémas disponibles : {', '.join(SCHEMA_DEFINITIONS)}"
        ) from error

    return build_schema(name, definition)


__all__ = ["SCHEMA_DEFINITIONS", "SchemaDefinition", "build_schema", "default_date", "get_schema"]
