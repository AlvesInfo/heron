# pylint: disable=E0401,R0903
"""
FR : Modèles pour les ventes Cosium
EN : Models for Cosium Sales

Commentaire:

created at: 2021-11-07
created by: Paulo ALVES

modified at: 2021-11-07
modified by: Paulo ALVES
"""
from django.db import models

from apps.centers_clients.models import Maison


class VentesCosium(models.Model):
    id_bi = models.IntegerField()
    id_vente = models.CharField(blank=True, null=True, max_length=90)
    code_ean = models.CharField(max_length=50)
    code_maison = models.CharField(blank=True, null=True, max_length=30)
    code_cosium = models.CharField(blank=True, null=True, max_length=30)
    famille_cosium = models.CharField(blank=True, null=True, max_length=30)
    rayon_cosium = models.CharField(blank=True, null=True, max_length=30)
    date_vente = models.DateField(auto_now=True)
    qte_vente = models.DecimalField(default=0, decimal_places=5, max_digits=20)
    remise = models.DecimalField(blank=True, null=True, decimal_places=5, max_digits=20)
    taux_tva = models.DecimalField(blank=True, null=True, decimal_places=5, max_digits=20)
    tva_x3 = models.CharField(max_length=20, null=True, blank=True)
    tva = models.DecimalField(null=True, default=0, max_digits=20, decimal_places=5)
    total_ttc = models.DecimalField(null=True, default=0, max_digits=20, decimal_places=5)

    # PRIX EN DEVISES
    pv_brut_unitaire = models.DecimalField(blank=True, null=True, decimal_places=5, max_digits=20)
    pv_net_unitaire = models.DecimalField(blank=True, null=True, decimal_places=5, max_digits=20)
    px_vente_ttc_devise = models.DecimalField(default=0, decimal_places=5, max_digits=20)
    px_vente_ttc_devise_apres_remise = models.DecimalField(
        default=0, decimal_places=5, max_digits=20
    )
    ca_ht_avt_remise = models.DecimalField(blank=True, null=True, decimal_places=5, max_digits=20)
    ca_ht_ap_remise = models.DecimalField(blank=True, null=True, decimal_places=5, max_digits=20)

    # PRIX EN EUROS
    taux_change = models.DecimalField(blank=True, null=True, decimal_places=5, max_digits=20)
    pv_brut_unitaire_eur = models.DecimalField(null=True, decimal_places=5, max_digits=20)
    pv_net_unitaire_eur = models.DecimalField(null=True, decimal_places=5, max_digits=20)
    px_vente_ttc_eur = models.DecimalField(null=True, decimal_places=5, max_digits=20)
    px_vente_ttc_eur_apres_remise = models.DecimalField(null=True, decimal_places=5, max_digits=20)
    ca_ht_avt_remise_eur = models.DecimalField(null=True, decimal_places=5, max_digits=20)
    ca_ht_ap_remise_eur = models.DecimalField(null=True, decimal_places=5, max_digits=20)

    px_achat_global = models.DecimalField(blank=True, null=True, decimal_places=5, max_digits=20)
    px_achat_unitaire = models.DecimalField(blank=True, null=True, decimal_places=5, max_digits=20)
    solde = models.DecimalField(blank=True, null=True, decimal_places=5, max_digits=20)

    maj_stock = models.DecimalField(null=True, default=0, decimal_places=2, max_digits=10)
    age_client = models.IntegerField(blank=True, null=True)
    centre_de_gestion = models.CharField(blank=True, null=True, max_length=50)
    centre_payeur = models.CharField(blank=True, null=True, max_length=60)
    code_barre_2 = models.CharField(blank=True, null=True, max_length=35)
    code_marketing_1 = models.CharField(blank=True, null=True, max_length=3)
    date_age_client = models.DateField(blank=True, null=True)
    date_creation = models.DateField(blank=True, null=True)
    date_encaissement = models.DateField(blank=True, null=True)
    date_ordo = models.DateField(blank=True, null=True)
    designation = models.CharField(blank=True, null=True, max_length=255)
    filtre_pack = models.CharField(blank=True, null=True, max_length=255)
    fournisseur = models.CharField(blank=True, null=True, max_length=50)
    indentification_equip = models.IntegerField(blank=True, null=True)
    indice = models.DecimalField(blank=True, null=True, decimal_places=5, max_digits=20)
    lentilles = models.CharField(blank=True, null=True, max_length=255)
    marque = models.CharField(blank=True, null=True, max_length=50)
    nom_mutuelle = models.CharField(blank=True, null=True, max_length=100)
    num_client = models.CharField(blank=True, null=True, max_length=20)
    num_devis_avoir = models.CharField(blank=True, null=True, max_length=50)
    num_facture = models.CharField(blank=True, null=True, max_length=50)
    pays = models.CharField(blank=True, null=True, max_length=50)
    photochromique = models.IntegerField(blank=True, null=True)
    prescripteur_na = models.CharField(blank=True, null=True, max_length=20)
    prescripteurs = models.CharField(blank=True, null=True, max_length=50)

    # Maison
    cct_uuid_identification = models.ForeignKey(
        Maison,
        null=True,
        on_delete=models.PROTECT,
        to_field="uuid_identification",
        related_name="ventes_maison",
        verbose_name="CCT x3",
        db_column="cct_uuid_identification",
    )

    def __str__(self):
        return f"{self.code_maison} - {self.code_ean}"

    class Meta:
        """class Meta Model DJango"""

        indexes = [
            models.Index(
                fields=[
                    "code_ean",
                    "code_maison",
                    "date_vente",
                    "maj_stock",
                    "age_client",
                    "pays",
                    "prescripteurs",
                    "id_bi",
                ]
            )
        ]
        index_together = [
            ["code_ean", "date_vente"],
            ["code_maison", "date_vente"],
            ["id_bi", "code_maison", "date_vente"],
            ["code_ean", "code_maison", "date_vente"],
        ]
        unique_together = (("code_cosium", "id_bi"),)
