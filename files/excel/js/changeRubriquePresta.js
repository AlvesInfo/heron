$(document).ready(function () {
    let urlRubriquePresta = ``;

    $(".rubriquePresta").dblclick(function () {
        urlRubriquePresta = $(this).data("url");

        let category = $(this).data("category");
        let modale = $('#modalCategory');
        let [pk, uuid_origin, big_category, third_party_num, invoice_month] = $(this).data("value").split("|");

        $(`#id_big_category_default`).dropdown('set selected', category);
        $(`#headerTiers`).html(`Tiers : ${third_party_num} - Catégorie : ${big_category}`);
        $(`#id_id`).val(pk)
        $(`#id_third_party_num`).val(third_party_num);
        $(`#id_invoice_month`).val(invoice_month);
        $(`#id_uuid_origin`).val(uuid_origin);

        modale
            .modal({
                closable: false,
                onApprove: function() {
                    $(`#rubriquePrestaFormChange`).submit();
                    $(`.message`).hide();
                    $(`.datatable-chargement`).show();
                }
            })
            .modal(`show`)
    })

    $(`#categoryFormChange`).submit(function (event) {
        let uuid_val = $("#id_big_category_default").val();
        let formData = {
            id: $("#id_id").val(),
            uuid_origin: $(`#id_uuid_origin`).val(),
            big_category: uuid_val,
            big_category_default: uuid_val,
            third_party_num: $("#id_third_party_num").val(),
            invoice_month: $("#id_invoice_month").val(),
        };

        $.ajax({
            type: "POST",
            url: urlRubriquePresta,
            data: formData,
            encode: true,
        }).done(function (data) {
            window.location.reload()
        });

        event.preventDefault();
    });

});