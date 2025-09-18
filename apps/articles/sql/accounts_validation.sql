select
	sum(count_accounts) as count_accounts
from (
	select
		"aa"."account", 1 as count_accounts
	 from "accountancy_accountsage" "aa"
	where "aa"."account" in %(accounts)s
	  and "aa".code_plan_sage = 'FRA'
) req
having sum(count_accounts) = %(accounts_nb)s