"""
FR : Module de validation de la sous catégory
EN : Subcategory validation module

Commentaire:

created at: 2023-06-04
created by: Paulo ALVES

modified at: 2023-06-04
modified by: Paulo ALVES
"""
import uuid
from apps.parameters.models import SubCategory


def check_sub_category(uuid_sub_category: uuid.UUID, uuid_big_category: uuid.UUID):
    """
    Vérifie que la sous-catégorie appartient à la catégorie demandée
    :param uuid_sub_category: sous-catégorie à vérifier
    :param uuid_big_category: catégorie dont la sous-catégorie appartiendrait
    :return:
    """

    return SubCategory.objects.filter(
        big_category=uuid_big_category, uuid_identification=uuid_sub_category
    ).exists()
