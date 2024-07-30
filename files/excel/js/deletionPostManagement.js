let initialTimeOut;

// FONCTION POUR SUPPRIMER DES LIGNES AVEC LEUR ID DE BASSE DE DONNEES
function deletePk(id_pk, pk, name, url, natureToDelete) {
        console.log(id_pk, ' - ', pk, ' - ', name, ' - ', url, natureToDelete)
        $(`#textModal`).text(`Etes vous sûr de vouloir supprimer ${natureToDelete}:`);
        $(`#modalContent`).text(name);
        $(`#sucess_delete`).hide()
        $(`#ko_delete`).hide()

        $(`#demandeModal`)
            .modal({
                closable: false,
                onApprove: function() {
                    window.clearTimeout(initialTimeOut);
                    $(`.datatable-chargement`).show();
                    let xhr = $.ajax({
                        data : {'pk': pk},
                        url : url,
                        type : 'POST',
                        success : function (data) {
                            hideAllMessages();
                            let baliseError = $(`#messages_delete`);

                            if (data.success !== 'ko') {
                                // SI SUCCESS ON SUPPRIME LA LIGNES DU TABLEAU
                                $(`#id_${id_pk}`).remove();

                                event.preventDefault();

                                let messageError = `<span>${natureToDelete} ${name}, a bien été effacée !</span>`;
                                let error = $(`#sucess_delete`);
                                let table = $('#table_document');
                                error.find(`div.header`).html(messageError);
                                error.show();
                                baliseError.show();
                                if (addition === 'True') {
                                    makeAddition()
                                }
                                if (table.find("tbody").find("tr").length === 0) {
                                    table.hide()
                                }

                            } else {
                                // SI ERREUR ON LES AFFICHENT PENDANT 5 SECONDES
                                let messageError = `<span>${natureToDelete} ${name} n'a pu être effacée !</span>`;
                                let error = $(`#ko_delete`);
                                error.find(`div.header`).html(messageError);
                                error.show();
                                baliseError.show();
                            }
                            $(`.datatable-chargement`).hide();
                        }
                    });
                    xhr.always(function() {
                    });
                },
                onabort () {
                    $(`.datatable-chargement`).hide();
                }
          })
          .modal(`show`)
    }