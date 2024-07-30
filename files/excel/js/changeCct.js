$(document).ready(function () {
    let urlCct = ``;

    $(".cct_sage").dblclick(function () {
        if ($(this).data("clickable") === `yes`) {
            urlCct = $(this).data("url");

            let cct = $(this).data("cct");
            let modale = $('#modalCct');
            let [pk, uuid_identification, third_party_num, invoice_number, invoice_year, code_maison, maison] = $(this).data("value").split("|");

            $(`#id_cct`).dropdown('set selected', cct);
            $(`#headerTiers`).html(`Tiers : ${third_party_num} - N° Facture : ${invoice_number} - CCT venant du fournisseur : ${code_maison} - ${maison}`);
            $(`#id_id`).val(pk)
            $(`#id_uuid_identification`).val(uuid_identification);
            $(`#id_third_party_num`).val(third_party_num);
            $(`#id_invoice_number`).val(invoice_number);
            $(`#id_invoice_year`).val(invoice_year);

            modale
                .modal({
                    closable: false,
                    onApprove: function() {
                        $(`#cctFormChange`).submit();
                        $(`.message`).hide();
                        $(`.datatable-chargement`).show();
                    }
                })
                .modal(`show`)
        }
    });

    $(`#cctFormChange`).submit(function (event) {
        let formData = {
            id: $("#id_id").val(),
            uuid_identification: $("#id_uuid_identification").val(),
            third_party_num: $("#id_third_party_num").val(),
            invoice_number: $("#id_invoice_number").val(),
            invoice_year: $("#id_invoice_year").val(),
            cct: $("#id_cct").val(),
        };

        $.ajax({
            type: "POST",
            url: urlCct,
            data: formData,
            encode: true,
        }).done(function () {
            window.location.reload()
        });

        event.preventDefault();

    });
});