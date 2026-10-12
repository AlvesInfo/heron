"""Script ponctuel : migration des identifiants du cct GA0000 vers LAB0001 pour tous les tiers"""
from apps.core.functions import functions_setups  # noqa: F401  amorçage Django hors serveur
from apps.book.models import SupplierCct
from apps.book.bin.checks import split_identifiers
from heron.loggers import LOGGER_IMPORT


def migrate_ga000_to_lab0001():
    """Suite à la demande de Marc Villeneuve, il faut migrer tous les GA0000 vers LAB0001
    pour tous les fournisseurs
    """
    for supplier in SupplierCct.objects.filter(cct_uuid_identification__cct="GA0000"):
        lab_supplier = SupplierCct.objects.filter(
            third_party_num_id=supplier.third_party_num_id,
            cct_uuid_identification__cct="LAB0001",
        ).first()

        if lab_supplier is None:
            LOGGER_IMPORT.error("%s : pas de cct LAB0001, GA0000 conservé", supplier.third_party_num_id)
            continue

        all_cct = split_identifiers((supplier.cct_identifier or "").strip())
        all_cct_lab = split_identifiers((lab_supplier.cct_identifier or "").strip())
        assemblage = (
            "|".join(value.strip() for value in sorted({*all_cct, *all_cct_lab}) if value.strip())
            + "|"
        )
        # # changement côté GA0000
        supplier.cct_identifier = "ZZZ|"
        supplier.save()
        LOGGER_IMPORT.info("%s %s %s", supplier.third_party_num_id, supplier.cct_identifier, supplier.cct_uuid_identification)

        # # changement côté LAB0001
        lab_supplier.cct_identifier = (
            assemblage.replace("ZZZ|", "").replace("|ZZZ", "").replace("|ZZZ|", "")
        )
        lab_supplier.save()
        LOGGER_IMPORT.info("%s %s", lab_supplier, lab_supplier.cct_identifier)


if __name__ == "__main__":
    migrate_ga000_to_lab0001()
