const firstPaging = 18
let tableCount = -1
let numberAlls = "{{ form.fields|length }}"

$("tr").each(function() {
    tableCount += 1
});

function getPaging () {
    return (tableCount / 2) < firstPaging
}

$("tr").promise().done(function() {

    // FRAMEWORK DATA-TABLE POUR AVOIR UN SCROLL VERTICAL

    $('#table_document').DataTable({
        "language": {
            "url": "//cdn.datatables.net/plug-ins/9dcbecd42ad/i18n/French.json"
        },
        "oLanguage": {
            "sSearch": ""
        },
        "lengthMenu": [[firstPaging, 50, -1], [firstPaging, 50, "Tous"]],
        "paging": !getPaging(),
        "info": getPaging(),
        "initComplete": function () {
            $(`#table_document_filter`)
                .find(`label`)
                .find(`span`)
                .find(`input`)
                .css("width", "20rem")
            $(`#table_document_length`).css(`text-align`, `left`)
            if (numberAlls === "0") {
                $(`#table_document_info`).css(`display`, `none`)
            } else {
                $(`#table_document_info`).css(`text-align`, `left`)
            }
            $(`.ui.datatable-chargement.active`).hide()
        },
    });
});
