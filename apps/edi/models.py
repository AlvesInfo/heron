from django.db import models

from heron.models import DatesTable, FlagsTable


class ShaFiles(DatesTable):
    id_sha512_file = models.TextField()
    nom_fichier = models.TextField(null=True, blank=True, max_length=255)
    errors = models.TextField(null=True, blank=True)


class EdiGenericImport(FlagsTable):
    fournisseur = models.CharField(null=True, blank=True, max_length=35)
    siret_fournisseur = models.CharField(null=True, blank=True, max_length=20)
    siret_payeur = models.CharField(null=True, blank=True, max_length=20)
    code_fournisseur = models.CharField(null=True, blank=True, max_length=30)
    code_maison = models.CharField(null=True, blank=True, max_length=30, default="AF000")
    maison = models.CharField(null=True, blank=True, max_length=80)
    num_commande_acuitis = models.CharField(
        null=True, blank=True, max_length=80, verbose_name="RFF avec ON"
    )
    date_commande_acuitis = models.DateField(null=True, verbose_name="DTM avec 4 quand RFF avec ON")
    num_bl = models.CharField(null=True, blank=True, max_length=80, verbose_name="RFF avec AAK")
    date_bl = models.DateField(null=True, verbose_name="DTM avec 35 quand RFF avec AAK")
    num_facture = models.CharField(null=True, blank=True, max_length=35)
    date_facture = models.DateField(null=True, verbose_name="DTM avec 3")
    nature_facture = models.CharField(
        null=True, blank=True, max_length=2, verbose_name="BGM Facture=380 Avoir=381"
    )
    devise = models.CharField(null=True, blank=True, max_length=3, default="EUR")
    reference_article = models.CharField(
        null=True, blank=True, max_length=35, verbose_name="LIN avec 21 et autre chose que EN"
    )
    code_ean = models.CharField(
        null=True, blank=True, max_length=35, verbose_name="LIN avec 21 et EN"
    )
    libelle = models.CharField(
        null=True, blank=True, max_length=80, verbose_name="IMD avec F dernière position"
    )
    famille = models.CharField(
        null=True, blank=True, max_length=80, verbose_name="IMD avec F 1ère position"
    )
    qte = models.DecimalField(
        decimal_places=5, default=0, max_digits=20, verbose_name="QTY avec 47"
    )
    qte_emballage = models.DecimalField(
        decimal_places=5, default=0, max_digits=20, verbose_name="QTY avec 52"
    )
    px_unitaire_brut = models.DecimalField(
        decimal_places=5, default=0, max_digits=20, verbose_name="PRI avec AAB et GRP"
    )
    px_unitaire_net = models.DecimalField(
        decimal_places=5, default=0, max_digits=20, verbose_name="PRI avec AAA et NTP"
    )
    emballage = models.DecimalField(
        decimal_places=5, default=0, max_digits=20, verbose_name="MOA avec 8 quand ALC avec M et PC"
    )
    port = models.DecimalField(
        decimal_places=5, default=0, max_digits=20, verbose_name="MOA avec 8 quand ALC avec M et FC"
    )
    montant_brut = models.DecimalField(
        decimal_places=5, default=0, max_digits=20, verbose_name="MOA avec 98"
    )
    montant_net = models.DecimalField(
        decimal_places=5, default=0, max_digits=20, verbose_name="MOA avec 125"
    )
    taux_tva = models.DecimalField(
        decimal_places=5, default=0, max_digits=20, verbose_name="TAX avec 7 quand ALC avec Y"
    )
    montant_tva = models.DecimalField(decimal_places=5, default=0, max_digits=20)
    montant_ttc = models.DecimalField(decimal_places=5, default=0, max_digits=20)
    nom_client = models.CharField(null=True, blank=True, max_length=80)
    num_serie = models.TextField(null=True, blank=True, max_length=1000)
    Commentaire = models.CharField(null=True, blank=True, max_length=120)
    montant_facture_HT = models.DecimalField(
        decimal_places=5, default=0, max_digits=20, verbose_name="MOA avec 125"
    )
    montant_facture_TVA = models.DecimalField(
        decimal_places=5, default=0, max_digits=20, verbose_name="MOA avec 150"
    )
    montant_facture_TTC = models.DecimalField(
        decimal_places=5, default=0, max_digits=20, verbose_name="MOA avec 128"
    )
