select
	third_party_num, supplier
    from edi_ediimport ee
    left join parameters_category pc
    on ee.uuid_big_category = pc.uuid_identification
    where (ee."delete" = false or ee."delete" isnull)
    group by pc."name",
             third_party_num,
             supplier,
             invoice_month
    having (
        pc."name" || '||' || third_party_num || '||' || supplier || '||' || invoice_month
    ) isnull