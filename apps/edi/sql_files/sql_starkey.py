# pylint: disable=E0401,C0303
"""
FR : Module des requêtes sql de post-traitement après import des fichiers Starkey
EN : Post-processing sql module after importing supplier invoice files

Commentaire:

created at: 2022-11-27
created by: Paulo ALVES

modified at: 2022-11-27
modified by: Paulo ALVES
"""
from psycopg2 import sql

post_starkey_dict = {
    "sql_update": sql.SQL(
        """
        update "edi_ediimport"
        set 
            "invoice_type" = case when "invoice_type" = 'FA' then '380' else '381' end,
            "net_unit_price" = ("net_amount"::numeric / "qty"::numeric)::numeric,
            "purchase_invoice" = true,
            "sale_invoice" = true,
            "origin" = 1
        where "uuid_identification" = %(uuid_identification)s
        and ("valid" = false or "valid" isnull)
        """
    ),
    "sql_update_units": sql.SQL(
        """
        update "edi_ediimport"
        set 
            "qty" = case 
                        when "net_amount" < 0 then (abs("qty")::numeric * -1::numeric)
                        when "net_amount" > 0 then abs("qty")::numeric
                        else "qty" 
                    end,
            "gross_unit_price" = abs("gross_unit_price"),
            "net_unit_price" = abs("net_unit_price"),
            "gross_amount" = case 
                                when "net_amount" = 0 then 0
                                when "net_amount" < 0 
                                    then (
                                        abs("gross_unit_price"::numeric * "qty"::numeric)::numeric 
                                        * 
                                        -1::numeric
                                    )
                                when "net_amount" > 0 
                                    then (
                                        abs("gross_unit_price"::numeric * "qty"::numeric)::numeric 
                                    )
                            end
        where "uuid_identification" = %(uuid_identification)s
        and ("valid" = false or "valid" isnull)
        """
    ),
    "sql_copie_envoi_depot": sql.SQL(
        """
        insert into "edi_starkeydepot"
        (
            "created_at",
            "modified_at",
            "delete",
            "export",
            "final_at",
            "acquitted",
            "level_group",
            "flag_to_active",
            "flag_to_delete",
            "flag_to_export",
            "flag_to_valid",
            "flag_to_acquitted",
            "uuid_file",
            "invoice_number",
            "invoice_date",
            "invoice_month",
            "invoice_year",
            "invoice_type",
            "devise",
            "invoice_amount_without_tax",
            "invoice_amount_tax",
            "invoice_amount_with_tax",
            "purchase_invoice",
            "sale_invoice",
            "manual_entry",
            "acuitis_order_number",
            "acuitis_order_date",
            "delivery_number",
            "delivery_date",
            "initial_home",
            "initial_date",
            "final_date",
            "first_name",
            "last_name",
            "heures_formation",
            "formation_month",
            "reference_article",
            "ean_code",
            "libelle",
            "client_name",
            "comment",
            "command_reference",
            "qty",
            "gross_unit_price",
            "net_unit_price",
            "gross_amount",
            "discount_price_01",
            "discount_price_02",
            "discount_price_03",
            "net_amount",
            "vat_amount",
            "amount_with_vat",
            "bi_id",
            "flow_name",
            "uuid_identification",
            "third_party_num",
            "supplier",
            "supplier_name",
            "supplier_ident",
            "siret_payeur",
            "code_fournisseur",
            "code_maison",
            "maison",
            "famille",
            "unit_weight",
            "packaging_qty",
            "vat_rate",
            "packaging_amount",
            "transport_amount",
            "insurance_amount",
            "fob_amount",
            "fees_amount",
            "serial_number",
            "active",
            "to_delete",
            "to_export",
            "valid",
            "vat_rate_exists",
            "supplier_exists",
            "maison_exists",
            "article_exists",
            "axe_pro_supplier_exists",
            "axe_pro_supplier",
            "vat_regime",
            "is_multi_store",
            "acquitted_by",
            "axe_bu",
            "axe_prj",
            "axe_pro",
            "axe_pys",
            "axe_rfa",
            "uuid_big_category",
            "cct_uuid_identification",
            "created_by",
            "delete_by",
            "modified_by",
            "origin",
            "personnel_type",
            "uuid_sub_big_category",
            "uuid_control",
            "vat",
            "import_uuid_identification"
        )
        select 
            "created_at",
            "modified_at",
            "delete",
            "export",
            "final_at",
            "acquitted",
            "level_group",
            "flag_to_active",
            "flag_to_delete",
            "flag_to_export",
            "flag_to_valid",
            "flag_to_acquitted",
            "uuid_file",
            "invoice_number",
            "invoice_date",
            "invoice_month",
            "invoice_year",
            "invoice_type",
            "devise",
            "invoice_amount_without_tax",
            "invoice_amount_tax",
            "invoice_amount_with_tax",
            "purchase_invoice",
            "sale_invoice",
            "manual_entry",
            "acuitis_order_number",
            "acuitis_order_date",
            "delivery_number",
            "delivery_date",
            "initial_home",
            "initial_date",
            "final_date",
            "first_name",
            "last_name",
            "heures_formation",
            "formation_month",
            "reference_article",
            "ean_code",
            "libelle",
            "client_name",
            "comment",
            "command_reference",
            "qty",
            "gross_unit_price",
            "net_unit_price",
            "gross_amount",
            "discount_price_01",
            "discount_price_02",
            "discount_price_03",
            "net_amount",
            "vat_amount",
            "amount_with_vat",
            "bi_id",
            "flow_name",
            "uuid_identification",
            "third_party_num",
            "supplier",
            "supplier_name",
            "supplier_ident",
            "siret_payeur",
            "code_fournisseur",
            "code_maison",
            "maison",
            "famille",
            "unit_weight",
            "packaging_qty",
            "vat_rate",
            "packaging_amount",
            "transport_amount",
            "insurance_amount",
            "fob_amount",
            "fees_amount",
            "serial_number",
            "active",
            "to_delete",
            "to_export",
            "valid",
            "vat_rate_exists",
            "supplier_exists",
            "maison_exists",
            "article_exists",
            "axe_pro_supplier_exists",
            "axe_pro_supplier",
            "vat_regime",
            "is_multi_store",
            "acquitted_by",
            "axe_bu",
            "axe_prj",
            "axe_pro",
            "axe_pys",
            "axe_rfa",
            "uuid_big_category",
            "cct_uuid_identification",
            "created_by",
            "delete_by",
            "modified_by",
            "origin",
            "personnel_type",
            "uuid_sub_big_category",
            "uuid_control",
            "vat",
            "import_uuid_identification"
        from "edi_ediimport" ee
        where ee."uuid_identification" = %(uuid_identification)s
        and ee."comment" = 'ENVOI_DEPOT'
        and (ee."valid" = false or ee."valid" isnull)
        on conflict do nothing
        """
    ),
    "sql_delete_envoi_depot": sql.SQL(
        """
        delete from "edi_ediimport"
        where "uuid_identification" = %(uuid_identification)s
        and "comment" = 'ENVOI_DEPOT'
        and ("valid" = false or "valid" isnull)
        """
    ),
}
