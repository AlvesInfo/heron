# pylint: disable=
"""
FR : Module des requêtes sql de post-traitement après import des fichiers edi opto33
EN : Post-processing sql module after importing supplier invoice files

Commentaire:

created at: 2022-11-27
created by: Paulo ALVES

modified at: 2022-11-27
modified by: Paulo ALVES
"""
from psycopg2 import sql

post_edi_dict = {
    "sql_col_essilor": sql.SQL(
        """
        update "edi_ediimport"
        set 
            "supplier_ident" = 'col_opticlibre'
        where "uuid_identification" = %(uuid_identification)s
        and ("valid" = false or "valid" isnull)
        and "siret_payeur" in ('9524514', '433193067', '43319306700033', 'FR82433193067')
        """
    ),
    "sql_tva": sql.SQL(
        """
        update edi_ediimport
        set
            vat_rate =  case
                            when vat_rate = 5.5 then 0.055
                            when vat_rate = 20 then 0.20
                            when vat_rate > 0 then (vat_rate / 100)::numeric
                            else vat_rate
                        end,
            acuitis_order_number = case 
                                        when acuitis_order_number = 'UNKNOWN' 
                                        then '' 
                                        else acuitis_order_number
                                    end,
            "origin" = 1
        where "uuid_identification" = %(uuid_identification)s
        and ("valid" = false or "valid" isnull)
        """
    ),
    "sql_precilens": sql.SQL(
        """
        update "edi_ediimport" edi
        set "gross_amount" = case 
                                when "qty" < 0 
                                then abs("gross_amount") 
                                else -abs("gross_amount") 
                            end,
            "net_amount" = case 
                                when "qty" < 0 
                                then abs("net_amount") 
                                else -abs("net_amount") 
                            end,
            "qty" = -qty
        where "third_party_num" = 'PREC001'
          and edi."uuid_identification" = %(uuid_identification)s
          and "invoice_type" = '381'
          and ("valid" = false or "valid" isnull)
    """
    ),
    "sql_fac_update_edi": sql.SQL(
        """
        update "edi_ediimport"
        set 
            "net_amount" = case
                                when ("invoice_type" = '381' and "qty" < 0) 
                                  or ("invoice_type" = '380' and "qty" > 0) 
                                then abs("net_amount")::numeric
                                when ("invoice_type" = '381' and "qty" > 0) 
                                  or ("invoice_type" = '380' and "qty" < 0) 
                                then -abs("net_amount")::numeric
                            end,
            "invoice_amount_without_tax" = case 
                                    when invoice_type = '381' 
                                    then -abs("invoice_amount_without_tax")::numeric
                                    else abs("invoice_amount_without_tax")::numeric
                                  end,
            "invoice_amount_with_tax" = case 
                                            when invoice_type = '381'
                                            then -abs("invoice_amount_with_tax")::numeric
                                            else abs("invoice_amount_with_tax")::numeric  
                                          end,
            "invoice_amount_tax" = case 
                                    when invoice_type = '381'
                                    then -abs("invoice_amount_with_tax")::numeric
                                    else abs("invoice_amount_with_tax")::numeric
                                  end -
                                  case 
                                    when invoice_type = '381' 
                                    then -abs("invoice_amount_without_tax")::numeric
                                    else abs("invoice_amount_without_tax")::numeric
                                  end,
            "reference_article" = case 
                                    when "reference_article" isnull or "reference_article" = '' 
                                    then "ean_code"
                                    else "reference_article"
                                  end,
            "purchase_invoice" = true,
            "sale_invoice" = true
        where "uuid_identification" = %(uuid_identification)s
        and ("valid" = false or "valid" isnull)
        """
    ),
    "sql_get_edi": sql.SQL(
        """
        select 
            uuid_identification
        from edi_ediimport ee 
        where flow_name = 'Edi' 
        group by uuid_identification
    """
    ),
    "sql_edi_generique": sql.SQL(
        """
        update "data_flux_trace" dt 
        set "trace_name" = left(
                                "trace_name" || sup."supplier" || ' - ' ||sup."third_party_num",
                                160
                            )
          from (
            select 
                "uuid_identification", 
                "supplier",
                "third_party_num"
              from "edi_ediimport" ee 
             where "flow_name" = 'Edi'
               and "uuid_identification" = %(uuid_identification)s
             group by "uuid_identification", 
                      "supplier",
                      "third_party_num"
          ) sup 
        where dt."uuid_identification" = sup."uuid_identification"
    """
    ),
}
