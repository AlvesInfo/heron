//==========================================================================================================
//  GESTION DES COOKIES
//==========================================================================================================

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
const csrftoken = getCookie('csrftoken');

function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}

$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
    }
});

//==========================================================================================================
// FONCTION SEMANTIC UI POUR INITIALISATION DES CHECKBOX
//==========================================================================================================
$('.ui.radio.checkbox').checkbox();

$('.message .close')
  .on('click', function() {
    $(this)
      .closest('.message')
      .transition('fade')
    ;
  });

//==========================================================================================================
// FONCTION POUR BOUTON DE SCROLL VERS LE HAUT DE PAGE
//==========================================================================================================

const scrollToTop = document.querySelector(".scrollToTop");

if (scrollToTop !== null) {
      scrollToTop.addEventListener("click", () => {
          window.scrollTo({
               top: 0,
               left: 0,
               behavior: "smooth",
        })
    });
}
