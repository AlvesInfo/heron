//==================================================================================================
//  Variables générique
//==================================================================================================
 //HAUTEUR DE TABLE POUR DATATables
let hauteurTables = 400;

// hook à la fermeture de la fenêtre, dabord à true la fenêtre se ferme si l'on a rien touvhé
let hook = true;

//==================================================================================================
//  GESTION DES DATES POUR FIREFOX
//==================================================================================================
$(function () {
    let navigateur = navigator.userAgent;
    let firefox = 'Firefox';
    let Resultat = navigateur.indexOf(firefox);
    if (Resultat !== -1) {
        $('input[type=date]').datepicker({
              dateFormat : 'dd/mm/yy'
            }
         );
    }
});


//==================================================================================================
//  SUPPRESSION AFFICHAGE DES MESSAGES
//==================================================================================================

function hideAllMessages () {
    $(`#messages_messages`).hide();
    $(`#messages_forms`).hide();
    $(`#messages_delete`).hide();
    $(`#messages_imports`).hide();
}

let messageTimeOut = 5000

//==================================================================================================
//  GO TO URL FOR LOADER
//==================================================================================================

function gotToUrl (url) {
    $(`.datatable-chargement`).show();
    location.href = url;
}

//==================================================================================================
//  GESTION DES SOMMES DE COLONNES ET DES DELTA DANS LES TABLES
//==================================================================================================

function setDelta(attrName, attrNameI, attrNameC) {

    $(`.${attrNameI}`).each(function (index) {
        let attrValue = (
            parseFloat($(this).text().replace(/\s/g, '').replace(',', '.')) -
            parseFloat($(`#${attrNameC}${index}`).text().replace(/\s/g, '').replace(',', '.'))
        );
        $(`#${attrName}${index}`).text(attrValue.toLocaleString())
    })

}
function setSum (attrName) {

    let attrValue = 0;

    $(`.${attrName}`).each(function(){
        attrValue += parseFloat($(this).text().replace(/\s/g, '').replace(',', '.')) || 0;
    })

    $(`#${attrName}`).text(attrValue.toLocaleString())

}
function setDeltaSum (attrName, attrNameI, attrNameR) {

    let attrValueS = 0;
    let attrValueC = 0;
    let attrNameV = 0;

    $(`.${attrNameI}`).each(function(index){
        attrValueS += parseFloat($(this).text().replace(/\s/g, '').replace(',', '.')) || 0;
        attrValueC += parseFloat($(`#${attrNameR}${index}`).text().replace(/\s/g, '').replace(',', '.'))  || 0;
    })

    attrNameV = attrValueS - attrValueC
    $(`#${attrName}`).text(attrNameV.toLocaleString())

    if (attrNameV !== 0) {
        $(`#${attrName}`).css("color", "red")
    } else {
        $(`#${attrName}`).css("color", "teal")
    }

}

let addition = `{{ addition }}`;

function makeAddition () {
    setSum("supplierHt")
    setSum("SupplierTtc")
    setSum("nbreFac")
    setSum("statementHt")
    setSum("statementTtc")
    setDeltaSum("deltaHt", "supplierHt", "statementHt")
    setDeltaSum("deltaTtc", "SupplierTtc", "statementTtc")
    // setDelta("deltaHt", "supplierHt", "statementHt")
    // setDelta("deltaTtc", "SupplierTtc", "statementTtc")
}

$(document).ready(function () {
  // INITIALISATION DE MOMENT SUR LES DATATABLES POUR TRI
    $.fn.dataTable.moment( 'DD/MM/YYY' );
});

//==================================================================================================
// Fonction qui affiche le message d'erreurs Ajax
//==================================================================================================
function errorAjax (messageAjaxVal, colorMessageVal) {
    $(`#tbodyUpload`).children().remove();

    let message = $(`.ui.message`);
    message.removeClass("positive");
    message.removeClass("negative");
    message.addClass(colorMessageVal);

    if (messageAjaxVal==="") {
        $(`#ulMessage`).append(`
        <H2>Une erreur a eu lieu, l'action a été annulée!</H2>
        <H4>Si l'erreur persiste, vous pouvez envoyer un mail à l'administrateur</H4>`);
    } else {
        $(`#ulMessage`).append(messageAjaxVal);
    }

    $(`#id_dimmer_traitement`).dimmer(`hide`);

    $(`#message`).show();
    setTimeout(function () {
            $(`#message`).hide();
        },
        10000
    );
}

//==================================================================================================
// Variable pour les dropdown clerable or not
//==================================================================================================
let drop_not_clearable = false;


//==================================================================================================
// Fonction de download des fichiers
//==================================================================================================
function DownloadFile(url) {
    $(`.datatable-chargement`).show();

    let fileName = "";

    $.ajax({
        url: url,
        cache: false,
        xhr: function () {
            let xhr = new XMLHttpRequest();
            xhr.onreadystatechange = function () {
                if (xhr.readyState === 2) {
                    if (xhr.status === 200) {
                        xhr.responseType = "blob";
                        fileName = xhr.getResponseHeader("Content-Disposition").split('filename=')[1].split(';')[0];
                    } else {
                        xhr.responseType = "text";
                    }
                }
            };
            return xhr;
        },
        success: function (data) {
            console.log()
            //Convert the Byte Data to BLOB object.
            let blob = new Blob([data], { type: "application/octetstream" });
            //Check the Browser type and download the File.
            let isIE = !!document.documentMode;
            if (isIE) {
                window.navigator.msSaveBlob(blob, fileName);
            } else {
                let url = window.URL || window.webkitURL;
                link = url.createObjectURL(blob);
                let a = $("<a/>");
                a.attr("download", fileName);
                a.attr("href", link);
                let body = $("body")
                body.append(a);
                a[0].click();
                body.remove(a);
            }
            $(`.datatable-chargement`).hide();
        }
    });
}