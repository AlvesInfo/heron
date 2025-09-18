select
	replace(ii.supplier, ';', ' ') as supplier,
	replace(iv.invoice_number, ';', ' ') as invoice_number,
	replace(ii.cct, ';', ' ') as cct,
	replace(ii.code_maison, ';', ' ') as code_maison,
	replace(
		case
			when ccm.code_cosium isnull
			then ccm.code_maison
			else ccm.code_cosium
		end,
		';',
		' '
	) as  code_cosium,
	replace(ii.maison, ';', ' ') as maison,
	replace(ii.reference_article, ';', ' ') as reference_article,
	replace(ii.supplier_initial_libelle, ';', ' ')  as libelle,
	replace(
        case
            when aa.famille isnull
            then dt.axe_pro
            else aa.famille
        end,
        ';',
        ' '
    ) as famille_article,
	replace(
	    case
            when co.famille_cosium is null
            then cv.famille_cosium
            else co.famille_cosium
        end,
	    ';',
	    ' '
	) as famille_cosium,
	replace(
	    case
	    	when co.famille_cosium is null
	    	then cv.rayon_cosium
	    	else co.rayon_cosium
	    end,
	    ';',
	    ' '
	) as rayon_cosium,
	ii.qty,
	dt.gross_unit_price as pu_brut,
	dt.net_unit_price as pu_net,
	dt.gross_amount as montant_brut,
	dt.net_amount as montant_net,
	dt.vat_rate as taux_tva,
	dt.vat_amount as montant_tva,
	dt.amount_with_vat as montant_ttc,
	replace(ii.serial_number, ';', '|') as num_serie

from invoices_invoice iv
join invoices_invoicedetail dt
on iv.uuid_identification = dt.uuid_invoice
join invoices_invoicecommondetails ii
on ii.import_uuid_identification = dt.import_uuid_identification
join articles_article aa
on ii.reference_article = aa.reference
and ii.third_party_num = aa.third_party_num
left join (
	select
		code_ean,
		max(famille_cosium) as famille_cosium,
		max(rayon_cosium) as rayon_cosium
	from compta_ventescosium cv
	group by code_ean
) co
on ii.reference_article = co.code_ean
left join (
	select
		('3' || code_ean) as art_verre,
		max(famille_cosium) as famille_cosium,
		max(rayon_cosium) as rayon_cosium
	from compta_ventescosium cv
	group by code_ean
) cv
on ii.reference_article = cv.art_verre
left join centers_clients_maison ccm
on ii.cct = ccm.cct
where iv.invoice_date between '#dte_d' and '#dte_f'