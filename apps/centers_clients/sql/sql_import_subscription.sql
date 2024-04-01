select
	"model", "reference", "identification"
from (
	select
		'article' as "model", aa."reference", max("uuid_identification"::text) as "identification"
	from "articles_article" aa
	where exists (
		select 1 from "centers_clients_maisonsubcription" "ccm" where "ccm"."article" = "aa"."uuid_identification"
	)
	group by "aa"."reference"
	union all
	select
		'unit_weight' as "model", "unity" as "reference", "id"::text as "identification"
	from "parameters_unitchoices" "pu"
	union all
	select
		'maison' as "model", "cct" as "reference", "cct" as "identification"
	from "centers_clients_maison" "ccm"
	union all
	select
		'function' as "model", "function_name" as "reference", "function_name" as "identification"
	from "parameters_invoicefunctions" "pif"
	union all
	select
		'signboard' as "model", "code" as "reference", "code" as "identification"
	from "centers_purchasing_signboard" "cpf"
) req