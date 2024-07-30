function spaceSplash (name) {
    return name.replace("_", " ")
}

function deleteObject (url, pk, objectName) {
    let xhr = $.ajax({
        data : {},
        url : url,
        type : 'POST',
        success : function (data) {
            let success = data.success;
            let message = data.message;
            hideAllMessages();
            $(`#messages_delete`).show();

            if (success !== 'ok') {
                let ko = $(`#ko_delete`);
                let texte;
                if (message === undefined) {
                    texte = `Une erreur est survenue : ` + spaceSplash(objectName) + ` n'as pas été éffacé !`
                } else {
                    texte = message
                }
                $(`#deleted`).modal(`hide`);
                ko.find(`div.header`).text(texte);
                ko.show();
                setTimeout(function () {
                    ko.hide();
                    },
                    messageTimeOut
                );
            } else {
                let sucess_delete = $(`#sucess_delete`);
                let texte = `${spaceSplash(objectName)} à été éffacé avec succès!`;
                $(`.item.active.selected`).remove();
                $(`#deleted`).modal(`hide`);
                sucess_delete.find(`div.header`).text(texte);
                sucess_delete.show();
                $(`#table_document`).DataTable().row($(`#id_` + pk)).remove().draw()
                setTimeout(function () {
                    sucess_delete.hide();
                    },
                    messageTimeOut
                );
            }
        }
    });
    xhr.always(function() {
    });
}

function callDeleteObject (url, pk, ojectName) {
  $(`#ojectToDeleted`).text(spaceSplash(ojectName));

  $(`#deleted`)
      .modal({
          closable: false,
          onApprove: function() {
              deleteObject(url, pk, ojectName);
          }
      })
      .modal(`show`)
}
