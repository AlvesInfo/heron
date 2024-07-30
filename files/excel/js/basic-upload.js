$(`#id_dimmer_maj`).dimmer(`hide`);

$(function () {

  $(".js-upload-photos").click(function () {
      console.log('click');
      $("#fileupload").click();
  });

  $("#fileupload").fileupload({
    dataType: 'json',
    /* 1. SEND THE FILES ONE BY ONE */
    sequentialUploads: true,
    start: function (e) {
      /* 2. WHEN THE UPLOADING PROCESS STARTS, SHOW THE MODAL */
      $("#id_dimmer_maj").dimmer("show");
    },
    stop: function (e) {
      /* 3. WHEN THE UPLOADING PROCESS FINALIZE, HIDE THE MODAL */
      $("#id_dimmer_maj").dimmer("hide");
    },
    progressall: function (e, data) {
        /* 4. UPDATE THE PROGRESS BAR */
        let lu = data.loaded;
        let total = data.total;
        let resultat = ((lu/total) * 100);
        let progress = parseInt(resultat, 10);
        let strProgress = "Téléversement en cours   -  "+ progress + " %";

        $(".progress-bar").css({"width": strProgress}).text(strProgress);
    },
    done: function (e, data) {

        /* 5. DATA ENVOYER PAR LE DICTIONNAIRE DATA DE LA VUE */
        if (data.result.isValid) {

            $(`.traitementButton`).show();
            $(`#tbodyUpload`).append(data.result.htmlFile)

        } else {
            // SI ERREUR ON LES AFFICHENT PENDANT 5 SECONDES
            let messageError = `<span>${data.result.message}</span>`;
            let baliseError = $(`#ajaxMessage`);
            let error = $(`#nopUpload`);
            error.find(`div.header`).html(messageError);
            baliseError.show();
            error.show();
            setTimeout(function () {
                    baliseError.hide();
                    error.hide();
                },
                5000
            );
        }
    }

  });

});

