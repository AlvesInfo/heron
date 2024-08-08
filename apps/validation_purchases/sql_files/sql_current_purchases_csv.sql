COPY (
    select "si"."code_center"                as "Centrale",
           "si"."code_signboard"             as "Enseigne",
           "si"."third_party_num"            as "Tiers X3",
           "bs"."name",
           case
               when "si"."invoice_type" = '380'
                   then 'FACTURE'
               else 'AVOIR'
               end                           as "Type Facture",
           "si"."invoice_amount_without_tax" as "Total HT",
           "si"."invoice_amount_tax"         as "Total TVA",
           "si"."invoice_amount_with_tax"    as "Total TTC",
           "cm"."cct"                        as "CCT X3",
           "si"."command_reference"          as "Référence commande",
           "si"."acuitis_order_number"       as "N° Commande",
           "si"."acuitis_order_date"         as "Date Commande",
           "si"."delivery_number"            as "N° BL",
           "si"."delivery_date"              as "Date BL",
           "si"."invoice_number"             as "N° Facture",
           "si"."invoice_date"               as "Date Facture",
           "si"."reference_article"          as "Référence article",
           "si"."libelle"                    as "Libellé",
           "si"."qty"                        as "Qte",
           "si"."net_unit_price"             as "PU Net",
           "si"."net_amount"                 as "Montant Net",
           "si"."vat"                        as "VAT X3",
           "si"."vat_rate"                   as "Taux TVA",
           "si"."vat_amount"                 as "Montant TVA",
           "si"."amount_with_vat"            as "Montant TTC",
           "bu"."section"                    as "axe_bu",
           "pro"."section"                   as "axe_pro",
           "prj"."section"                   as "axe_prj",
           "pys"."section"                   as "axe_pys",
           "rfa"."section"                   as "axe_rfa",
           "sb"."name"                       as "big_category",
           coalesce("sd"."name", '')         as "sub_category",
           "si"."client_name"                as "Nom Cient",
           "si"."serial_number"              as "N° Série"
    from "edi_ediimport" "si"
             left join "parameters_category" "sb"
                       on "sb"."uuid_identification" = "si"."uuid_big_category"
             left join "parameters_subcategory" "sd"
                       on "sd"."uuid_identification" = "si"."uuid_sub_big_category"
             left join "book_society" "bs"
                       on "si"."third_party_num" = "bs"."third_party_num"
             left join "centers_clients_maison" "cm"
                       on "si"."cct_uuid_identification" = "cm"."uuid_identification"
             left join (select "uuid_identification",
                               "section"
                        from "accountancy_sectionsage"
                        where "axe" = 'BU') "bu"
                       on "si"."axe_bu" = "bu"."uuid_identification"
             left join (select "uuid_identification",
                               "section"
                        from "accountancy_sectionsage"
                        where "axe" = 'PRO') "pro"
                       on "si"."axe_pro" = "pro"."uuid_identification"
             left join (select "uuid_identification",
                               "section"
                        from "accountancy_sectionsage"
                        where "axe" = 'PRJ') "prj"
                       on "si"."axe_prj" = "prj"."uuid_identification"
             left join (select "uuid_identification",
                               "section"
                        from "accountancy_sectionsage"
                        where "axe" = 'PYS') "pys"
                       on "si"."axe_pys" = "pys"."uuid_identification"
             left join (select "uuid_identification",
                               "section"
                        from "accountancy_sectionsage"
                        where "axe" = 'RFA') "rfa"
                       on "si"."axe_rfa" = "rfa"."uuid_identification"
    order by "si"."invoice_month",
             "bs"."name",
             "si"."invoice_number",
             "cm"."cct",
             "si"."reference_article"
) TO %(to_csv)s DELIMITER ';' CSV HEADER NULL '' ENCODING 'UTF8';
