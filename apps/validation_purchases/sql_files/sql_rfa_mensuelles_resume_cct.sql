select
	"code_signboard",
	"cct",
	"intitule",
    $sum_amount_sql_suppliers$
	sum("TOTAL") as "TOTAL"
from (
    select
        "ee"."code_signboard",
        "cm"."cct",
        "cm"."intitule",
        $amount_sql_suppliers$
        "ee"."net_amount" as "TOTAL"
    from "edi_ediimport" "ee"
    left join "centers_clients_maison" "cm"
    on "ee"."cct_uuid_identification" = "cm"."uuid_identification"
      where "ee"."flow_name" = 'rfa_flow'
) req
group by
    "code_signboard",
    "cct",
	"intitule"
order by
    "code_signboard",
    "cct"
