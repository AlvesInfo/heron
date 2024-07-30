// *********************************************************************************************************
// LANCEMENT TRAITEMENT PHOTOS
// *********************************************************************************************************
function TraitementTrue(IdFile) {
    console.log('TraitementTrue' + IdFile);
    let TId = `#id_` + IdFile;
    let DId = `#t_id_` + IdFile;
    let TrId = `#tr_id_` + IdFile;
    let TrIdS = TrId + ` td`;
    let textReference = $(TrIdS).first().text();

    $(`#article_traited`).text(textReference);
    $(`#traited`)
        .modal({
            closable: false,
            onApprove: function() {

                let xhr = $.ajax({
                    data : {'pk': IdFile},
                    url : '/web/traitement_true/',
                    type : 'POST',
                    success : function (data) {
                        let success = JSON.parse(data).success;
                        if (success === 'ko') {
                            console.log(success);
                        } else {
                            console.log(success);
                            $(TId).remove();
                            $(DId).remove();
                            $(TrId).append(`<td class="traitement">En cours...</td><td></td>`)
                        }
                    }
                });

                xhr.always(function() {
                });
            }
        })
        .modal(`show`)
}

// *********************************************************************************************************
// SUPPRESSION DU FICHIER
// *********************************************************************************************************
function TraitementDelete(IdFile) {
    console.log('TraitementDelete' + IdFile);
    let TrId = `#tr_id_` + IdFile;
    let TrIdS = TrId + ` td`;
    let textReference = $(TrIdS).first().text();

    $(`#article_deleted`).text(textReference);
    $(`#deleted`)
        .modal({
            closable: false,
            onApprove: function() {

                let xhr = $.ajax({
                    data : {'pk': IdFile},
                    url : '/web/traitement_delete/',
                    type : 'POST',
                    success : function (data) {
                        let success = JSON.parse(data).success;
                        if (success === 'ko') {
                            console.log(success);
                        } else {
                            console.log(success);
                            let TrId = `#tr_id_` + IdFile;
                            $(TrId).remove();
                        }
                    }
                });

                xhr.always(function() {
                });
            }
        })
        .modal(`show`)
}