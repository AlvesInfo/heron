# pylint: disable=E0401,R0903
"""
FR : Module des modèles pour création d'od depuis un fichier csv
EN : Model module for creating od from a csv file

Commentaire:

created at: 2025-03-15
created by: Paulo ALVES

modified at: 2025-03-15
modified by: Paulo ALVES
"""

from django.db import models

from heron.models import DatesTable


class ModelOd(DatesTable):
    """
    Table des od à passer
    FR :
    EN :
    """

    date_od = models.DateField()
    libelle_od = models.TextField(blank=True, null=True)
    date_extourne = models.DateField()
    libelle_extourne = models.TextField(blank=True, null=True)
    compte_produit = models.CharField(max_length=35)
    compte_tva = models.CharField(max_length=35)
    compte_collectif = models.CharField(max_length=35)
    code_plan = models.CharField(max_length=10)
    journal = models.CharField(max_length=15)
    type_ecriture = models.CharField(max_length=15)
    libelle = models.CharField(max_length=30)
    axe_bu = models.CharField(max_length=10)
    cct = models.CharField(max_length=10)
    axe_pro = models.CharField(max_length=10)
    axe_prj = models.CharField(max_length=10)
    axe_pys = models.CharField(max_length=10)
    axe_rfa = models.CharField(max_length=10)
    montant_ht = models.DecimalField(max_digits=20, decimal_places=5, default=0)
    vat = models.CharField(max_length=5)
    taux_tva = models.DecimalField(max_digits=20, decimal_places=5, default=0)
    montant_tva = models.DecimalField(max_digits=20, decimal_places=5, default=0)
    montant_ttc = models.DecimalField(max_digits=20, decimal_places=5, default=0)

    @staticmethod
    def get_columns_import():
        """
        FR : Retourne la position des colonnes
        EN : Returns the position of the columns
        """
        return {
            "date_od": "date_od",
            "libelle_od": "libelle_od",
            "date_extourne": "date_extourne",
            "libelle_extourne": "libelle_extourne",
            "compte_produit": "compte_produit",
            "compte_tva": "compte_tva",
            "compte_collectif": "compte_collectif",
            "journal": "journal",
            "type_ecriture": "type_ecriture",
            "libelle": "libelle",
            "code_plan": "code_plan",
            "axe_bu": "axe_bu",
            "cct": "cct",
            "axe_pro": "axe_pro",
            "axe_prj": "axe_prj",
            "axe_pys": "axe_pys",
            "axe_rfa": "axe_rfa",
            "montant_ht": "montant_ht",
            "vat": "vat",
            "taux_tva": "taux_tva",
            "montant_tva": "montant_tva",
            "montant_ttc": "montant_ttc",
        }

    @staticmethod
    def get_uniques():
        """
        FR : Retourne les champs uniques de la table
        EN: Returns the unique fields of the table
        """
        return

    @property
    def get_import(self):
        """
        FR : Retourne la methode à appeler pour importer à partir d'un fichier de type csv
        EN : Returns the method to call to import from a csv file type
        """
        return "methode d'import à retourner"

    def __str__(self):
        """Texte renvoyé dans les selects et à l'affichage de l'objet"""
        return f"{self.libelle_od} - {self.journal} - {self.piece_origine}"

    class Meta:
        """class Meta du modèle django"""
