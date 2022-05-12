l = [
    "third_party_num = models.CharField()  # BPRNUM",
    "name = models.CharField(null=True, blank=True, max_length=80)  # BPRNAM_0",
    "short_name = models.CharField()  # BPRSHO",
    "corporate_name = models.CharField()  # BPRNAM_1",
    "siren_number = models.CharField()  # ?",
    "siret_number = models.CharField()  # CRN",
    "vat_cee_number = models.CharField()  # EECNUM",
    "vat_number = models.CharField(null=True, blank=True, max_length=20)  # VATNUM",
    "client_category = models.ForeignKey()  # BCGCOD",
    "supplier_category = models.ForeignKey()  # BSGCOD",
    "naf_code = models.CharField()  # NAF",
    "currency = models.CharField()  # CUR",
    "country = models.ForeignKey()  # CRY models Country",
    "language = models.CharField(null=True, blank=True, max_length=80)  # LAN models Country",
    'budget_code = models.CharField()  # Z_CODBUD models TabDivSage limit_choices_to={"num_table": "6100"}',
    "reviser = models.CharField(null=True, blank=True, max_length=5)  # Z_REVUSR",
    "is_client = models.BooleanField(null=True, default=False)  # BPCFLG",
    "is_agent = models.BooleanField(null=True, default=False)  # REPFLG",
    "is_prospect = models.BooleanField(null=True, default=False)  # PPTFLG",
    "is_supplier = models.BooleanField(null=True, default=False)  # BPSFLG",
    "is_various = models.BooleanField(null=True, default=False)  # BPRACC",
    "is_service_provider = models.BooleanField(null=True, default=False)  # PRVFLG",
    "is_transporter = models.BooleanField(null=True, default=False)  # BPTFLG",
    "is_contractor = models.BooleanField(null=True, default=False)  # DOOFLG",
    "is_physical_person = models.BooleanField(null=True, default=False)  # LEGETT",
    "payment_condition_supplier = models.CharField()  # PTE - BPSUPPLIER (Table TABPAYTERM)",
    "vat_sheme_supplier = models.CharField()  # VACBPR - BPSUPPLIER (Table TABVACBPR)",
    "account_supplier_code = models.CharField()  # ACCCOD - BPSUPPLIER (Table GACCCODE)",
    "payment_condition_client = models.CharField()  # PTE - BPCUSTOMER (Table TABPAYTERM)",
    "vat_sheme_client = models.CharField()  # VACBPR - BPCUSTOMER (Table TABVACBPR)",
    "account_client_code = models.CharField()  # ACCCOD - BPCUSTOMER (Table GACCCODE)",
    """,""" "code_plan_sage = models.CharField()",
    "supplier_identifier = models.CharField()",
    "client_identifier = models.CharField()",
    "comment = models.TextField(null=True, blank=True)",
    "nature = models.ForeignKey()",
    'code_cct_x3 = models.CharField(null=True, blank=True, max_length=15, verbose_name="cct X3")',
    'code_cosium = models.CharField(null=True, blank=True, max_length=15, verbose_name="code cosium")',
    'sign_board = models.ForeignKey(    verbose_name="enseigne",)',
    'opening_date = models.DateField(null=True, verbose_name="date d ouveture")',
    'closing_date = models.DateField(null=True, verbose_name="date de fermeture")',
    'signature_franchise_date = models.DateField(null=True, verbose_name="date de signature contrat")',
    "agreement_franchise_end_date = models.DateField()",
    'agreement_renew_date = models.DateField(null=True, verbose_name="date de renouvelement contrat")',
    'entry_fee_amount = models.DecimalField(max_digits=20, decimal_places=5, null=True, verbose_name="montant de droit d entrée")',
    'renew_fee_amoount = models.DecimalField(    verbose_name="montant de droit de renouvellement",)',
    'sale_price_category = models.ForeignKey(verbose_name="categorie de prix",)',
    'generic_coefficient = models.DecimalField(    verbose_name="coeficient de vente générique",)',
    'credit_account = models.ForeignKey(verbose_name="compte X3 au crédit",    db_column="credit_account",)',
    'debit_account = models.ForeignKey(verbose_name="compte X3 au débit",)',
    "prov_account = models.ForeignKey()",
    "sage_vat_by_default = models.CharField()",
    "sage_pan_code = models.CharField(null=True, blank=True, max_length=10)",
    "rfa_frequence = models.IntegerField(null=True, choices=Frequence.choices, default=Frequence.MENSUEL)",
    "rfa_remise = models.IntegerField(null=True, choices=Remise.choices, default=Remise.TOTAL)",
    "invoice_supplier_name = models.CharField(null=True, blank=True, max_length=80)",
    "invoice_client_name = models.CharField(null=True, blank=True, max_length=80)",
]


if __name__ == '__main__':
    for row in l:
        print(row.split(" = ")[0])

    for row in l:
        print(f'society.{row.split(" = ")[0]}')

    for row in l:
        print(f'"entete": "{row.split(" = ")[0]}-{row.split(" = ")[-1]}"')

