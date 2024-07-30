//==================================================================================================
//  GESTION DES DATES POUR FIREFOX
//==================================================================================================
$(function(){
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
//  HAUTEUR DE TABLE POUR DATATables
//==================================================================================================
let hauteurTables = 400;
