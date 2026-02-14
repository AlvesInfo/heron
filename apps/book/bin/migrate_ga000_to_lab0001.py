from apps.core.functions.functions_setups import *
from apps.book.models import SupplierCct
from copy import deepcopy


def migrate_ga000_to_lab0001():
    """Suite à la demande de Marc Villeneuve, il faut migrer tous les GA0000 vers LAB0001
    pour tous les fournisseurs
    """
    for supplier in SupplierCct.objects.filter(cct_uuid_identification__cct="GA0000"):
        all_cct = deepcopy(
            supplier.cct_identifier.strip()[:-1].split("|")
            if supplier.cct_identifier.endswith("|")
            else supplier.cct_identifier.strip().split("|")
        )
        lab_supplier = SupplierCct.objects.get(
            third_party_num_id=supplier.third_party_num_id,
            cct_uuid_identification__cct="LAB0001",
        )
        all_cct_lab = deepcopy(
            lab_supplier.cct_identifier.strip()[:-1].split("|")
            if lab_supplier.cct_identifier.endswith("|")
            else lab_supplier.cct_identifier.strip().split("|")
        )
        assemblage = (
            "|".join(value.strip() for value in {*all_cct, *all_cct_lab}) + "|"
        )
        # # changement côté GA0000
        supplier.cct_identifier = "ZZZ|"
        supplier.save()
        print(
            supplier.third_party_num_id,
            supplier.cct_identifier,
            supplier.cct_uuid_identification,
            sep=" : ",
        )

        # # changement côté LAB0001
        lab_supplier.cct_identifier = (
            assemblage.replace("ZZZ|", "").replace("|ZZZ", "").replace("|ZZZ|", "")
        )
        lab_supplier.save()
        print(
            lab_supplier,
            lab_supplier.cct_identifier,
            sep=" : ",
        )


if __name__ == "__main__":
    migrate_ga000_to_lab0001()
